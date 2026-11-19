"""카드뉴스(1080x1350) 이미지 생성"""
import glob
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import art

import config

W, H = 1080, 1350
NAVY, NAVY2 = (11, 27, 51), (20, 40, 72)
WHITE, ORANGE = (255, 255, 255), (255, 122, 26)
MUTED, SOFT = (150, 168, 196), (222, 230, 242)
PAD = 84

_BOLD = ["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
         "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
         "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
         "C:/Windows/Fonts/malgunbd.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc"]
_REG = ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "C:/Windows/Fonts/malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc"]


@lru_cache(maxsize=64)
def font(size, bold=True):
    local = sorted(glob.glob(str(config.BASE / "fonts" / "*")))
    pick = [p for p in local if ("bold" in p.lower()) == bold] or local
    for path in pick + (_BOLD if bold else _REG):
        if not Path(path).exists():
            continue
        for idx in (1, 0):  # .ttc 에서는 1번이 한국어 계열
            try:
                return ImageFont.truetype(path, size, index=idx)
            except Exception:
                continue
    return ImageFont.load_default()


def wrap(text, f, max_w):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if f.getlength(trial) <= max_w:
            cur = trial
            continue
        if cur:
            lines.append(cur)
            cur = ""
        if f.getlength(word) <= max_w:
            cur = word
        else:
            buf = ""
            for ch in word:
                if f.getlength(buf + ch) <= max_w:
                    buf += ch
                else:
                    lines.append(buf)
                    buf = ch
            cur = buf
    if cur:
        lines.append(cur)
    return lines


def clamp(lines, n, f, max_w):
    if len(lines) <= n:
        return lines
    out = lines[:n]
    last = out[-1]
    while last and f.getlength(last + "…") > max_w:
        last = last[:-1]
    out[-1] = last + "…"
    return out


def ball_icon(d, cx, cy, r):
    """작은 야구공 아이콘"""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(246, 242, 230, 255))
    red = (206, 40, 50, 255)
    d.arc([cx - 3.1 * r, cy - 1.4 * r, cx - 0.3 * r, cy + 1.4 * r], start=-38, end=38, fill=red, width=2)
    d.arc([cx + 0.3 * r, cy - 1.4 * r, cx + 3.1 * r, cy + 1.4 * r], start=142, end=218, fill=red, width=2)


def _fit(text, f, max_w):
    while f.getlength(text) > max_w and len(text) > 3:
        text = text[:-2] + "…"
    return text


def make_card(item, idx, total, date_label, out_path):
    import summarizer
    p = art.pal(item["league"])
    acc = p["accent"]
    PADX = 72
    sums = summarizer.clean_lines(item["title"], item.get("lines")) if config.SHOW_SUMMARY else []
    title_only = not sums

    art_h, fh, fade_y, fade_h = (1000, 600, 500, 500) if title_only else (900, 500, 470, 430)
    img = Image.new("RGB", (W, H), art.BG)
    img.paste(art.render_scene(W, art_h, item["league"], idx, fh=fh), (0, 0))
    fade = Image.linear_gradient("L").resize((W, fade_h))        # 일러스트 → 하단 패널로 부드럽게
    img.paste(Image.new("RGB", (W, fade_h), art.BG), (0, fade_y), fade)
    d = ImageDraw.Draw(img, "RGBA")

    # 상단 바: 브랜드 + 페이지
    ball_icon(d, PADX + 20, 80, 20)
    d.text((PADX + 56, 62), "BASEBALL NEWS", font=font(28), fill=WHITE)
    pg = f"{idx:02d} / {total:02d}"
    pf = font(26)
    pw = int(pf.getlength(pg)) + 44
    d.rounded_rectangle([W - PADX - pw, 58, W - PADX, 104], radius=23, fill=(0, 0, 0, 110), outline=acc + (255,), width=2)
    d.text((W - PADX - pw + 22, 66), pg, font=pf, fill=WHITE)

    # 제목 (아래쪽 기준 정렬: 줄 수에 따라 위로 늘어남)
    max_w = W - PADX * 2
    sizes = (104, 94, 84, 74, 64, 56) if title_only else (78, 70, 62, 54)
    max_lines = 4
    for size in sizes:
        f = font(size)
        lines = wrap(item["title"], f, max_w)
        if len(lines) <= max_lines:
            break
    lines = clamp(lines, 5 if title_only else max_lines, f, max_w)
    lh = int(size * 1.22)
    y_end = 1140 if title_only else 872
    y = y_end - len(lines) * lh
    bf = font(30)
    bw = int(bf.getlength(item["league"])) + 52
    by = y - 92
    d.rounded_rectangle([PADX, by, PADX + bw, by + 52], radius=26, fill=acc + (255,))
    d.text((PADX + 26, by + 6), item["league"], font=bf, fill=art.BG)
    d.text((PADX + bw + 20, by + 9), date_label, font=font(28, bold=False), fill=(255, 255, 255, 200))
    for ln in lines:
        d.text((PADX, y + 3), ln, font=f, fill=(0, 0, 0, 150))
        d.text((PADX, y), ln, font=f, fill=WHITE)
        y += lh

    if title_only:
        d.line([PADX, y_end + 26, PADX + 120, y_end + 26], fill=acc + (255,), width=6)
    else:                                                          # 요약 켠 경우: 구분선 + 요약 줄
        d.line([PADX, 908, W - PADX, 908], fill=(255, 255, 255, 40), width=2)
        d.line([PADX, 908, PADX + 120, 908], fill=acc + (255,), width=5)
        sf = font(38, bold=False)
        y = 944
        for s_ in sums:
            wl = clamp(wrap(s_, sf, max_w - 30), 2, sf, max_w - 30)
            if y + len(wl) * 56 > 1180:
                break
            d.rounded_rectangle([PADX, y + 6, PADX + 6, y + len(wl) * 56 - 8], radius=3, fill=acc + (255,))
            for ln in wl:
                d.text((PADX + 30, y), ln, font=sf, fill=(230, 236, 246, 255))
                y += 56
            y += 26

    # 하단: 출처 + 채널
    d.line([PADX, 1204, W - PADX, 1204], fill=(255, 255, 255, 34), width=2)
    tf = font(26)
    tw = int(tf.getlength("출처")) + 32
    d.rounded_rectangle([PADX, 1224, PADX + tw, 1268], radius=22, outline=acc + (255,), width=2)
    d.text((PADX + 16, 1229), "출처", font=tf, fill=acc)
    d.text((PADX + tw + 18, 1222), _fit(item["source"], font(34), max_w - tw - 18), font=font(34), fill=WHITE)

    d.ellipse([PADX, 1278, PADX + 44, 1322], fill=acc + (255,))
    ball_icon(d, PADX + 22, 1300, 15)
    d.text((PADX + 58, 1284), config.CHANNEL_NAME, font=font(26, bold=False), fill=(170, 184, 208, 255))
    hint = "넘겨서 보기  →" if idx < total else "저장하고 내일도 확인!"
    hf = font(26)
    d.text((W - PADX - hf.getlength(hint), 1284), hint, font=hf, fill=acc)

    img.save(out_path)
    return img
