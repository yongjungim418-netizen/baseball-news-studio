"""RSS 에서 야구 뉴스 수집 → DB 저장 (표준 라이브러리만 사용)"""
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import config
import db


def _clean(t):
    t = re.sub(r"<[^>]+>", " ", html.unescape(t or ""))
    return re.sub(r"\s+", " ", t).strip()


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 BaseballNewsStudio"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()


def classify(text):
    for league in ("MLB", "NPB", "KBO"):
        if any(k.lower() in text.lower() for k in config.LEAGUE_KEYWORDS[league]):
            return league
    return None


def collect():
    """수집한 새 기사 수와 오류 메시지 목록을 반환"""
    added, errors = 0, []
    now = datetime.now(timezone.utc).isoformat()
    for feed in config.FEEDS:
        try:
            root = ET.fromstring(_fetch(feed["url"]))
        except Exception as e:  # 네트워크/파싱 오류는 해당 피드만 건너뜀
            errors.append(f'{feed["name"]}: {e}')
            continue
        for item in root.iter("item"):
            title = _clean(item.findtext("title"))
            link = (item.findtext("link") or "").strip()
            if not title or not link:
                continue
            src_el = item.find("source")
            source = _clean(src_el.text) if src_el is not None and src_el.text else feed["name"]
            title = re.sub(r"\s+-\s+" + re.escape(source) + r"$", "", title)
            snippet = _clean(item.findtext("description"))
            try:
                pub = parsedate_to_datetime(item.findtext("pubDate")).astimezone(timezone.utc).isoformat()
            except Exception:
                pub = now
            league = feed.get("league")
            if feed.get("filter"):
                league = classify(title + " " + snippet)
            if not league:
                continue
            with db.conn() as c:
                cur = c.execute(
                    "INSERT OR IGNORE INTO articles(url,title,source,league,published,snippet,collected_at) "
                    "VALUES(?,?,?,?,?,?,?)", (link, title, source, league, pub, snippet, now))
                added += cur.rowcount
    return added, errors
