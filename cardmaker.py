"""카드뉴스(1080x1350) 이미지 생성"""
import glob
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

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


def make_card(item, idx, total, date_label, out_path):
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 18, H], fill=ORANGE)                      # 좌측 오렌지 바
    d.rectangle([18, 0, W, 262], fill=NAVY2)                      # 상단 영역

    d.text((PAD, 74), "BASEBALL NEWS STUDIO", font=font(28), fill=MUTED)
    page = f"{idx}/{total}"
    d.text((W - PAD - font(30).getlength(page), 72), page, font=font(30), fill=WHITE)

    # 리그 배지
    bf = font(38)
    bw = int(bf.getlength(item["league"])) + 56
    d.rounded_rectangle([PAD, 160, PAD + bw, 228], radius=34, fill=ORANGE)
    d.text((PAD + 28, 170), item["league"], font=bf, fill=NAVY)

    # 제목: 길면 폰트를 줄여 5줄 안에 맞춤
    max_w = W - PAD * 2
    for size in (74, 66, 58, 50):
        f = font(size)
        lines = wrap(item["title"], f, max_w)
        if len(lines) <= 5:
            break
    lines = clamp(lines, 5, f, max_w)
    y = 306
    for ln in lines:
        d.text((PAD, y), ln, font=f, fill=WHITE)
        y += int(size * 1.28)

    d.rectangle([PAD, y + 24, PAD + 140, y + 32], fill=ORANGE)
    y += 80

    # 요약 (불릿)
    sf = font(40, bold=False)
    for s in item["lines"][:3]:
        wl = clamp(wrap(s, sf, max_w - 44), 2, sf, max_w - 44)
        if y + len(wl) * 58 > 1120:
            break
        d.rectangle([PAD, y + 20, PAD + 14, y + 34], fill=ORANGE)
        for ln in wl:
            d.text((PAD + 44, y), ln, font=sf, fill=SOFT)
            y += 58
        y += 22

    # 하단: 출처
    d.line([PAD, 1176, W - PAD, 1176], fill=(52, 74, 110), width=2)
    d.text((PAD, 1200), "출처", font=font(30), fill=ORANGE)
    src = item["source"]
    while font(36).getlength(src) > max_w - 110 and len(src) > 3:
        src = src[:-1]
    d.text((PAD + 90, 1196), src, font=font(36), fill=WHITE)
    d.text((PAD, 1264), f"{date_label}  ·  {config.CHANNEL_NAME}", font=font(28, bold=False), fill=MUTED)

    img.save(out_path)
    return img
