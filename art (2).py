"""야구 테마 일러스트 배경 (Pillow 로 직접 그림 → 저작권 걱정 없음).

내 사진을 쓰고 싶으면 backgrounds 폴더 또는 프로젝트 루트에 bg_1.jpg, bg_2.jpg … 를 넣으세요.
(사진이 있으면 일러스트 대신 어둡게 처리해서 배경으로 씁니다)
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import config

BG = (9, 17, 33)   # 카드 하단 패널 기본색
PALETTES = {
    "KBO": {"accent": (255, 122, 26), "dark": (8, 18, 42), "mid": (22, 54, 118), "glow": (70, 130, 255)},
    "MLB": {"accent": (244, 72, 84), "dark": (8, 14, 44), "mid": (26, 44, 122), "glow": (90, 140, 255)},
    "NPB": {"accent": (255, 200, 64), "dark": (34, 8, 20), "mid": (126, 24, 46), "glow": (255, 120, 96)},
}
KINDS = ["ball", "diamond", "lights"]
_IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def pal(league):
    return PALETTES.get(league, PALETTES["KBO"])


def _vgrad(w, h, top, bottom):
    g = Image.linear_gradient("L").resize((w, h))
    return Image.composite(Image.new("RGB", (w, h), bottom), Image.new("RGB", (w, h), top), g)


def _soft(mask, radius):
    """저해상도에서 블러 → 되돌리기 (빠르고 메모리 적게 씀)"""
    w, h = mask.size
    s = 4
    m = mask.resize((max(1, w // s), max(1, h // s)), Image.BILINEAR)
    m = m.filter(ImageFilter.GaussianBlur(max(0.5, radius / s)))
    return m.resize((w, h), Image.BILINEAR)


def _glow(base, mask, color, strength=1.0):
    m = mask.point(lambda v: int(min(255, v * strength)))
    layer = Image.composite(Image.new("RGB", base.size, color), Image.new("RGB", base.size, (0, 0, 0)), m)
    return ImageChops.screen(base, layer)


# ---------------------------------------------------------------- 야구공
def _ball_layer(R, angle):
    S = 2
    size = int(2 * R * S + 8)
    c, r = size / 2, R * S
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([c - r, c - r, c + r, c + r], fill=(246, 242, 230, 255))
    red = (206, 40, 50, 255)
    for sign in (-1, 1):
        ccx, rr = c + sign * 1.7 * r, 1.4 * r
        phi = 0 if sign == -1 else math.pi
        pts = []
        for deg in range(-75, 76):
            a = phi + math.radians(deg)
            x, y = ccx + rr * math.cos(a), c + rr * math.sin(a)
            if math.hypot(x - c, y - c) < r * 0.985:
                pts.append((x, y))
        if len(pts) > 1:
            d.line(pts, fill=red, width=max(2, int(r * 0.03)))
        for deg in range(-75, 76, 5):
            a = phi + math.radians(deg)
            x, y = ccx + rr * math.cos(a), c + rr * math.sin(a)
            if math.hypot(x - c, y - c) < r * 0.93:
                ux, uy = math.cos(a), math.sin(a)
                t = r * 0.11
                d.line([(x - ux * t, y - uy * t), (x + ux * t, y + uy * t)], fill=red, width=max(2, int(r * 0.022)))
    layer = layer.rotate(angle, resample=Image.BICUBIC)
    # 입체감: 좌상단에서 빛이 오는 그림자
    rg = Image.radial_gradient("L").resize((size * 2, size * 2))
    sh = int(size * 0.16)
    rg = rg.crop((size // 2 + sh, size // 2 + sh, size // 2 + sh + size, size // 2 + sh + size))
    alpha = rg.point(lambda v: int(max(0, v - 105) * 1.7))
    shade = Image.new("RGBA", (size, size), (8, 12, 34, 0))
    shade.putalpha(alpha)
    layer = Image.alpha_composite(layer, shade)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([c - r, c - r, c + r, c + r], fill=255)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
    return layer.resize((size // S, size // S), Image.LANCZOS)


def _scene_ball(w, h, fh, p, rng):
    base = _vgrad(w, h, p["dark"], p["mid"])
    R = int(fh * 0.34)
    cx, cy = int(w * 0.70), int(fh * 0.53)
    # 속도감 줄무늬
    streaks = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(streaks)
    for _ in range(16):
        y = rng.randint(0, int(fh * 1.1))
        x0 = rng.randint(-200, int(w * 0.35))
        ln = rng.randint(300, 700)
        d.line([(x0, y), (x0 + ln, y - int(ln * 0.21))], fill=rng.randint(40, 120), width=rng.randint(3, 9))
    base = _glow(base, _soft(streaks, 6), p["glow"], 0.8)
    halo = Image.new("L", (w, h), 0)
    ImageDraw.Draw(halo).ellipse([cx - R * 1.6, cy - R * 1.6, cx + R * 1.6, cy + R * 1.6], fill=150)
    base = _glow(base, _soft(halo, 90), p["glow"], 0.7)
    base = _glow(base, _soft(halo.point(lambda v: v // 2), 60), p["accent"], 0.35)
    ball = _ball_layer(R, rng.randint(-25, 25))
    base.paste(ball.convert("RGB"), (cx - ball.width // 2, cy - ball.height // 2), ball)
    return base


# ---------------------------------------------------------------- 그라운드(다이아몬드)
def _scene_diamond(w, h, fh, p, rng):
    base = _vgrad(w, h, p["dark"], p["mid"])
    D = int(min(w * 0.36, fh * 0.42))
    cx, cy = int(w * 0.62), int(fh * 0.60)
    pts = [(cx, cy - D), (cx + D, cy), (cx, cy + D), (cx - D, cy)]
    fill = Image.new("L", (w, h), 0)
    ImageDraw.Draw(fill).polygon(pts, fill=80)
    base = _glow(base, fill, p["glow"], 0.6)

    lines = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(lines)
    d.line(pts + [pts[0]], fill=255, width=7)
    k = 0.5
    inner = [(cx, cy - D * k), (cx + D * k, cy), (cx, cy + D * k), (cx - D * k, cy)]
    d.line(inner + [inner[0]], fill=150, width=4)
    d.ellipse([cx - D * 0.08, cy - D * 0.08, cx + D * 0.08, cy + D * 0.08], fill=255)   # 마운드
    home = (cx, cy + D)
    d.line([home, (home[0] - w, home[1] - w)], fill=200, width=5)                        # 파울 라인
    d.line([home, (home[0] + w, home[1] - w)], fill=200, width=5)
    for rr in (1.45, 1.85, 2.25):                                                        # 외야 곡선
        R = D * rr
        d.arc([home[0] - R, home[1] - R, home[0] + R, home[1] + R], start=215, end=325, fill=110, width=4)
    for bx, by in (pts[0], pts[1], pts[3]):                                              # 베이스
        s = D * 0.07
        d.polygon([(bx, by - s), (bx + s, by), (bx, by + s), (bx - s, by)], fill=255)
    base = _glow(base, _soft(lines, 22), p["accent"], 1.0)
    base = Image.composite(Image.new("RGB", (w, h), (255, 255, 255)), base, lines.point(lambda v: int(v * 0.9)))
    return base


# ---------------------------------------------------------------- 야간 조명 + 관중
def _scene_lights(w, h, fh, p, rng):
    base = _vgrad(w, h, p["dark"], p["mid"])
    beams = Image.new("L", (w, h), 0)
    bd = ImageDraw.Draw(beams)
    lamps = Image.new("L", (w, h), 0)
    ld = ImageDraw.Draw(lamps)
    for side in (0, 1):
        x0 = int(w * (0.20 if side == 0 else 0.80))
        y0 = int(fh * 0.30)
        tx = int(w * (0.58 if side == 0 else 0.42))
        bd.polygon([(x0 - 40, y0), (x0 + 40, y0), (tx + int(w * 0.36), fh + 80), (tx - int(w * 0.36), fh + 80)], fill=95)
        for r in range(3):
            for c in range(4):
                lx, ly = x0 - 54 + c * 36, y0 - 38 + r * 36
                ld.ellipse([lx - 13, ly - 13, lx + 13, ly + 13], fill=255)
    base = _glow(base, _soft(beams, 34), p["glow"], 1.0)
    base = _glow(base, _soft(lamps, 26), (255, 255, 255), 1.0)
    base = Image.composite(Image.new("RGB", (w, h), (255, 255, 255)), base, lamps.point(lambda v: int(v * 0.95)))
    floor = Image.new("L", (w, h), 0)
    ImageDraw.Draw(floor).ellipse([w * 0.1, fh * 0.86, w * 0.9, fh * 1.25], fill=140)
    base = _glow(base, _soft(floor, 60), p["accent"], 0.55)
    d = ImageDraw.Draw(base)
    crowd = (5, 9, 20)
    top = int(fh * 0.93)
    for x in range(-20, w + 30, 20):
        y = top + rng.randint(-34, 22)
        rad = rng.randint(14, 22)
        d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=crowd)
    d.rectangle([0, top + 12, w, h], fill=crowd)
    return base


_SCENES = {"ball": _scene_ball, "diamond": _scene_diamond, "lights": _scene_lights}


# ---------------------------------------------------------------- 내 사진 배경(선택)
def _photos():
    files = []
    for folder in (config.BASE / "backgrounds", config.BASE):
        if folder.exists():
            for f in sorted(folder.iterdir()):
                if f.suffix.lower() in _IMG_EXT and (folder.name == "backgrounds" or f.name.lower().startswith("bg_")):
                    files.append(f)
    return files


def _photo_scene(w, h, p, idx, files):
    img = Image.open(files[(idx - 1) % len(files)]).convert("RGB")
    s = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * s) + 1, int(img.height * s) + 1), Image.LANCZOS)
    l, t = (img.width - w) // 2, (img.height - h) // 3
    img = img.crop((l, t, l + w, t + h))
    img = Image.blend(img, Image.new("RGB", (w, h), p["dark"]), 0.5)
    return _glow(img, Image.linear_gradient("L").resize((w, h)).point(lambda v: 255 - v // 2).point(lambda v: v // 6), p["glow"], 0.5)


def render_scene(w, h, league, idx, fh=None):
    """w x h 크기의 배경 이미지. fh = 그림이 주로 보이는 높이(그 아래는 글자/어둡게 덮임)"""
    p = pal(league)
    fh = fh or int(h * 0.56)
    photos = _photos()
    if photos:
        base = _photo_scene(w, h, p, idx, photos)
    else:
        rng = random.Random(idx * 7919 + len(league) * 31)
        base = _SCENES[KINDS[(idx - 1) % len(KINDS)]](w, h, fh, p, rng)
    noise = Image.effect_noise((w, h), 30).convert("RGB")      # 아주 약한 필름 질감
    return Image.blend(base, noise, 0.03)
