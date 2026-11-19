"""수집 → 선별(KBO/MLB/NPB 섞기) → 요약 → 카드 5장 → 릴스 → 캡션"""
import difflib
import json
import shutil
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import cardmaker
import collector
import config
import db
import quality
import reelmaker
import summarizer

DEMO_SAMPLES = [
    ("KBO", "(데모) 한국시리즈 우승팀, 내년 시즌 외국인 선수 재계약 발표", "샘플뉴스"),
    ("KBO", "(데모) 신인 투수, 데뷔 첫 선발 등판서 6이닝 무실점", "샘플스포츠"),
    ("KBO", "(데모) 프로야구 FA 시장 개장, 포수 최대어 관심 집중", "샘플일보"),
    ("MLB", "(데모) 메이저리그 겨울 이적 시장 개막, 선발 투수 영입전 치열", "샘플MLB"),
    ("MLB", "(데모) 아시아 출신 타자, 올 시즌 20홈런 20도루 달성", "샘플뉴스"),
    ("MLB", "(데모) 올스타 유격수, 장기 연장 계약 합의", "샘플스포츠"),
    ("NPB", "(데모) 일본프로야구 일본시리즈 우승팀 퍼레이드 개최", "샘플재팬"),
    ("NPB", "(데모) NPB 에이스, 포스팅 통한 메이저리그 도전 선언", "샘플일보"),
]


def today():
    return datetime.now(ZoneInfo(config.TZ)).strftime("%Y-%m-%d")


def _sim(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def seed_demo():
    now = datetime.now(timezone.utc)
    with db.conn() as c:
        for i, (lg, title, src) in enumerate(DEMO_SAMPLES):
            pub = (now - timedelta(hours=i + 1)).isoformat()
            c.execute("INSERT OR IGNORE INTO articles(url,title,source,league,published,snippet,collected_at) "
                      "VALUES(?,?,?,?,?,?,?)",
                      (f"https://example.com/demo/{i}", title, src, lg, pub,
                       "샘플 요약 문장입니다. 실제 수집 시에는 기사 내용이 들어갑니다. 세 번째 문장도 표시됩니다.",
                       now.isoformat()))


def select(date, reset=False):
    """date 의 카드 후보를 채운다. reset=False 면 기존 선택은 유지하고 빈 슬롯만 채움."""
    now = datetime.now(timezone.utc)
    with db.conn() as c:
        if reset:
            c.execute("UPDATE articles SET status='new', batch_date=NULL, slot=NULL "
                      "WHERE status='selected' AND batch_date=?", (date,))
        existing = c.execute("SELECT * FROM articles WHERE status='selected' AND batch_date=?", (date,)).fetchall()
        need = config.CARDS_PER_DAY - len(existing)
        if need <= 0:
            return
        past = [r["title"] for r in c.execute(
            "SELECT title FROM articles WHERE status='selected' AND batch_date!=? "
            "AND batch_date>=?", (date, (now - timedelta(days=3)).strftime("%Y-%m-%d")))]
        rows = c.execute("SELECT * FROM articles WHERE status='new'").fetchall()

        # 최신 기사만, 최근 며칠 내 쓴 기사와 비슷한 건 제외
        cands = []
        for r in rows:
            age = (now - datetime.fromisoformat(r["published"])).total_seconds() / 3600
            if age > config.MAX_AGE_HOURS:
                continue
            if quality.is_junk(r["title"], r["source"]):
                continue
            if any(_sim(r["title"], t) > 0.6 for t in past):
                continue
            cands.append((r, age))
        cands.sort(key=lambda x: x[1])

        # 비슷한 제목은 한 묶음으로 → 여러 매체가 다룬 이슈일수록 점수 가산
        clusters = []
        for r, age in cands:
            for cl in clusters:
                if _sim(r["title"], cl["row"]["title"]) > 0.55:
                    cl["n"] += 1
                    if quality.source_bonus(r["source"]) > quality.source_bonus(cl["row"]["source"]):
                        cl["row"] = r
                    break
            else:
                clusters.append({"row": r, "n": 1, "age": age})
        for cl in clusters:
            cl["score"] = cl["n"] * 10 - cl["age"] * 0.2 + quality.bonus(cl["row"]["title"], cl["row"]["source"])
        clusters.sort(key=lambda x: -x["score"])

        taken = {x["title"] for x in existing}
        picks = []
        have = {lg: sum(1 for x in existing if x["league"] == lg) for lg in config.QUOTA}
        src_n = {}
        for x in existing:
            src_n[x["source"]] = src_n.get(x["source"], 0) + 1

        def add(cl):
            picks.append(cl)
            src_n[cl["row"]["source"]] = src_n.get(cl["row"]["source"], 0) + 1

        def ok(cl, strict):
            r = cl["row"]
            return (cl not in picks and r["title"] not in taken
                    and (not strict or src_n.get(r["source"], 0) < 2))

        for lg, q in config.QUOTA.items():
            for cl in clusters:
                if len(picks) >= need or have.get(lg, 0) >= q:
                    break
                if cl["row"]["league"] == lg and ok(cl, True):
                    add(cl); have[lg] = have.get(lg, 0) + 1
        for strict in (True, False):          # 부족하면 점수순으로 채움 (마지막엔 매체 제한 해제)
            for cl in clusters:
                if len(picks) >= need:
                    break
                if ok(cl, strict):
                    add(cl)
        picks.sort(key=lambda x: -x["score"])

        used = {x["slot"] for x in existing}
        free = [s for s in range(1, config.CARDS_PER_DAY + 1) if s not in used]
        for slot, cl in zip(free, picks):
            c.execute("UPDATE articles SET status='selected', batch_date=?, slot=? WHERE id=?",
                      (date, slot, cl["row"]["id"]))


def render(date):
    out_dir = config.OUTPUT_DIR / date
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    with db.conn() as c:
        rows = c.execute("SELECT * FROM articles WHERE status='selected' AND batch_date=? ORDER BY slot",
                         (date,)).fetchall()
    if not rows:
        raise RuntimeError("선택된 뉴스가 없습니다. 수집된 기사가 없거나 모두 오래된 기사입니다.")

    items = []
    for r in rows:
        s = json.loads(r["summary"]) if r["summary"] else None
        if not s:
            s = summarizer.summarize(r["title"], r["snippet"], r["source"])
            with db.conn() as c:
                c.execute("UPDATE articles SET summary=? WHERE id=?", (json.dumps(s, ensure_ascii=False), r["id"]))
        items.append({"id": r["id"], "league": r["league"], "title": s["title"], "lines": s["lines"],
                      "source": r["source"], "url": r["url"]})

    d = datetime.strptime(date, "%Y-%m-%d")
    date_label = f"{d.month}월 {d.day}일"
    imgs = []
    for i, it in enumerate(items, 1):
        imgs.append(cardmaker.make_card(it, i, len(items), date_label, out_dir / f"card_{i}.png"))
    reelmaker.make_reel(items, imgs, date_label, out_dir)
    shutil.rmtree(out_dir / "_frames", ignore_errors=True)

    cap = [f"⚾ 오늘의 야구 뉴스 TOP {len(items)} ({d.month}/{d.day})", ""]
    for i, it in enumerate(items, 1):
        cap.append(f'{i}. [{it["league"]}] {it["title"]} (출처: {it["source"]})')
    cap += ["", f"📌 저장하고 팔로우하면 내일도 확인할 수 있어요 {config.CHANNEL_NAME}", "",
            "#야구 #야구뉴스 #KBO #프로야구 #MLB #메이저리그 #NPB #일본야구"]
    (out_dir / "caption.txt").write_text("\n".join(cap), encoding="utf-8")
    (out_dir / "items.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")

    with db.conn() as c:
        c.execute("INSERT INTO batches(date,status,updated_at) VALUES(?, 'draft', ?) "
                  "ON CONFLICT(date) DO UPDATE SET status='draft', updated_at=excluded.updated_at",
                  (date, datetime.now(timezone.utc).isoformat()))
    return items


def run_all(demo=False):
    """전체 실행: 수집 → 선별(새로) → 카드/릴스. 오류/경고 메시지 리스트 반환."""
    db.init()
    date = today()
    msgs = []
    if demo:
        seed_demo()
    else:
        added, errors = collector.collect()
        msgs += errors
        msgs.append(f"새 기사 {added}건 수집")
    select(date, reset=True)
    render(date)
    return msgs


def replace_article(article_id):
    """카드 1장 제외 후 대체 기사로 채워서 다시 렌더링"""
    date = today()
    with db.conn() as c:
        c.execute("UPDATE articles SET status='excluded', slot=slot WHERE id=?", (article_id,))
    select(date, reset=False)
    return render(date)
