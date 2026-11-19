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


def _card_art(item, idx, total, date_label, out_path):
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

    # 제목 (아래쪽 기준 정렬: 줄 수에 따라 위로 늘어남) + 핵심 단어 색 강조
    max_w = W - PADX * 2
    sizes = (104, 94, 84, 74, 64, 56) if title_only else (78, 70, 62, 54)
    hl = pick_highlight(item["title"])
    size, f, lines = fit_title(item["title"], sizes, max_w, 4, hl)
    lh = int(size * 1.22)
    y_end = 1140 if title_only else 872
    y = y_end - len(lines) * lh
    bf = font(30)
    bw = int(bf.getlength(item["league"])) + 52
    by = y - 92
    d.rounded_rectangle([PADX, by, PADX + bw, by + 52], radius=26, fill=acc + (255,))
    d.text((PADX + 26, by + 6), item["league"], font=bf, fill=art.BG)
    d.text((PADX + bw + 20, by + 9), date_label, font=font(28, bold=False), fill=(255, 255, 255, 200))
    draw_lines(d, lines, PADX, y + 3, f, lh, (4, 6, 12), (4, 6, 12), "color")     # 그림자
    draw_lines(d, lines, PADX, y, f, lh, WHITE, acc, "color")

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


import re


def _lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def pick_highlight(title):
    """제목에서 색으로 강조할 단어(최대 2개): 숫자 > 핵심 이슈 단어 순"""
    toks = title.split(" ")
    scored = []
    for i, t in enumerate(toks):
        if re.search(r"\d", t):
            scored.append((-1, i))
            continue
        for rank, w in enumerate(config.BOOST_WORDS):
            if w in t:
                scored.append((rank, i))
                break
    hit = {i for _, i in sorted(scored)[:2]}
    if not hit and len(toks) >= 3:
        hit.add(len(toks) - 1)
    return hit


def _line_w(f, ln):
    return sum(f.getlength(t) for t, _ in ln) + f.getlength(" ") * (len(ln) - 1)


def layout(title, f, max_w, hl):
    """단어 단위로 줄바꿈하면서 강조 여부를 같이 들고 다님 → [[(단어, 강조?), ...], ...]"""
    sp = f.getlength(" ")
    lines, w = [[]], 0
    for i, tok in enumerate(title.split(" ")):
        pieces = [tok]
        if f.getlength(tok) > max_w:                 # 아주 긴 단어는 글자 단위로 쪼갬
            pieces, buf = [], ""
            for ch in tok:
                if f.getlength(buf + ch) <= max_w:
                    buf += ch
                else:
                    pieces.append(buf)
                    buf = ch
            pieces.append(buf)
        for pc in pieces:
            tw = f.getlength(pc)
            add = tw if not lines[-1] else tw + sp
            if lines[-1] and w + add > max_w:
                lines.append([])
                w, add = 0, tw
            lines[-1].append((pc, i in hl))
            w += add
    return lines


def clamp_lines(lines, n, f, max_w):
    if len(lines) <= n:
        return lines
    lines = lines[:n]
    t, h = lines[-1][-1]
    lines[-1][-1] = (t + "…", h)
    while _line_w(f, lines[-1]) > max_w and len(lines[-1][-1][0]) > 2:
        t, h = lines[-1][-1]
        lines[-1][-1] = (t[:-2] + "…", h)
    return lines


def fit_title(title, sizes, max_w, max_lines, hl):
    for size in sizes:
        f = font(size)
        lines = layout(title, f, max_w, hl)
        if len(lines) <= max_lines:
            return size, f, lines
    return size, f, clamp_lines(lines, max_lines + 1, f, max_w)


def draw_lines(d, lines, x0, y0, f, lh, color, acc, mode):
    """mode: color(강조 단어만 색) / block(강조 단어에 색 블록)"""
    bb = f.getbbox("가나다")
    sp = f.getlength(" ")
    on_acc = (24, 24, 24) if _lum(acc) > 175 else (255, 255, 255)
    y = y0
    for ln in lines:
        x, i = x0, 0
        while i < len(ln):
            if mode == "block" and ln[i][1]:
                j = i
                while j + 1 < len(ln) and ln[j + 1][1]:
                    j += 1
                seg = " ".join(t for t, _ in ln[i:j + 1])
                sw = f.getlength(seg)
                d.rectangle([x - 10, y + bb[1] - 8, x + sw + 10, y + bb[3] + 8], fill=acc + (255,))
                d.text((x, y), seg, font=f, fill=on_acc + (255,))
                x += sw + sp
                i = j + 1
            else:
                t, h = ln[i]
                d.text((x, y), t, font=f, fill=(acc if (h and mode == "color") else color) + (255,))
                x += f.getlength(t) + sp
                i += 1
        y += lh


EDIT_BG, LIGHT_BG = (13, 13, 18), (244, 242, 238)


def _flat_base(style):
    return Image.new("RGB", (W, H), EDIT_BG if style == "editorial" else LIGHT_BG)


def _style_editorial(item, idx, total, date_label, out_path):
    acc = art.pal(item["league"])["accent"]
    img = _flat_base("editorial")
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, W, 60):                                 # 은은한 격자
        d.line([x, 0, x, H], fill=(255, 255, 255, 7))
    for y in range(0, H, 60):
        d.line([0, y, W, y], fill=(255, 255, 255, 7))
    glow = Image.new("L", (W, H), 0)                          # 우하단 글로우
    ImageDraw.Draw(glow).ellipse([W * 0.35, H * 0.55, W * 1.3, H * 1.3], fill=130)
    img = art._glow(img, art._soft(glow, 170), acc, 0.30)
    d = ImageDraw.Draw(img, "RGBA")
    muted = (128, 128, 140, 255)

    pg = f"{idx:02d} / {total:02d}"
    pf = font(28)
    d.text((W - PAD - pf.getlength(pg), 68), pg, font=pf, fill=muted)

    hl = pick_highlight(item["title"])
    size, f, lines = fit_title(item["title"], (112, 100, 90, 80, 70, 62), W - PAD * 2, 4, hl)
    lh = int(size * 1.28)
    block = 8 + 56 + len(lines) * lh + 36 + 44
    y = max(170, int(H * 0.47 - block / 2))
    d.rectangle([PAD, y, PAD + 120, y + 8], fill=acc + (255,))            # 짧은 강조 막대
    y += 56
    draw_lines(d, lines, PAD, y, f, lh, (240, 240, 244), acc, "color")
    y += len(lines) * lh + 24
    d.text((PAD, y), "출처  " + _fit(item["source"], font(32, bold=False), W - PAD * 2 - 100),
           font=font(32, bold=False), fill=muted)

    d.text((PAD, H - 96), f"BASEBALL NEWS  ·  {item['league']}", font=font(24), fill=(96, 96, 108, 255))
    hf = font(24, bold=False)
    d.text((W - PAD - hf.getlength(config.CHANNEL_NAME), H - 96), config.CHANNEL_NAME, font=hf, fill=(96, 96, 108, 255))
    img.save(out_path)
    return img


def _style_light(item, idx, total, date_label, out_path):
    acc = art.pal(item["league"])["accent"]
    ink, gray = (24, 24, 24), (140, 136, 130)
    img = _flat_base("light")
    d = ImageDraw.Draw(img, "RGBA")
    d.text((PAD, 66), f"NEWS {idx:02d} / {total:02d}  ·  {item['league']}", font=font(28), fill=ink + (255,))
    hf = font(24, bold=False)
    d.text((W - PAD - hf.getlength(config.CHANNEL_NAME), 70), config.CHANNEL_NAME, font=hf, fill=gray + (255,))

    hl = pick_highlight(item["title"])
    size, f, lines = fit_title(item["title"], (108, 98, 88, 78, 68, 60), W - PAD * 2 - 20, 4, hl)
    lh = int(size * 1.36)
    block = len(lines) * lh + 48 + 112
    y = max(200, int(H * 0.45 - block / 2))
    draw_lines(d, lines, PAD + 10, y, f, lh, ink, acc, "block")
    y += len(lines) * lh + 48
    # 출처 콜아웃 박스 (왼쪽 강조선)
    d.rectangle([PAD, y, W - PAD, y + 104], fill=_mix(acc, LIGHT_BG, 0.86) + (255,))
    d.rectangle([PAD, y, PAD + 6, y + 104], fill=acc + (255,))
    cf = font(34)
    d.text((PAD + 36, y + 30), "출처  " + _fit(item["source"], cf, W - PAD * 2 - 130), font=cf, fill=ink + (255,))

    d.line([PAD, H - 112, W - PAD, H - 112], fill=(206, 202, 196, 255), width=2)
    d.text((PAD, H - 84), date_label, font=font(26, bold=False), fill=gray + (255,))
    pg = f"{idx} / {total}"
    pf = font(28)
    d.text((W - PAD - pf.getlength(pg), H - 86), pg, font=pf, fill=ink + (255,))
    img.save(out_path)
    return img


def style_name():
    s = (getattr(config, "CARD_STYLE", "editorial") or "editorial").lower()
    return "art" if (config.SHOW_SUMMARY or s not in ("editorial", "light", "art")) and s != "light" and s != "editorial" else s


def reel_theme():
    """릴스 카드 프레임 배경/글자색: (배경, 글자색, 비활성 막대색)"""
    s = style_name()
    if s == "light":
        return LIGHT_BG, (24, 24, 24), (206, 202, 196)
    if s == "editorial":
        return EDIT_BG, (240, 240, 244), (60, 60, 72)
    return art.BG, WHITE, (52, 74, 110)


def make_card(item, idx, total, date_label, out_path):
    s = style_name()
    if config.SHOW_SUMMARY:
        s = "art"                      # 요약 줄은 art 스타일에서만 지원
    if s == "light":
        return _style_light(item, idx, total, date_label, out_path)
    if s == "editorial":
        return _style_editorial(item, idx, total, date_label, out_path)
    return _card_art(item, idx, total, date_label, out_path)
