"""카드 5장 → 9:16 요약 릴스(mp4). FFmpeg 필요."""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

import cardmaker as cm
import config

RW, RH = 1080, 1920


def _frame_base():
    img = Image.new("RGB", (RW, RH), cm.NAVY)
    ImageDraw.Draw(img).rectangle([0, 0, 18, RH], fill=cm.ORANGE)
    return img


def _centered(d, text, f, y, fill):
    d.text(((RW - f.getlength(text)) / 2, y), text, font=f, fill=fill)


def intro_frame(items, date_label, path):
    img = _frame_base()
    d = ImageDraw.Draw(img)
    _centered(d, "BASEBALL NEWS STUDIO", cm.font(34), 360, cm.MUTED)
    _centered(d, "오늘의 야구 뉴스", cm.font(104), 470, cm.WHITE)
    d.rectangle([RW / 2 - 70, 650, RW / 2 + 70, 660], fill=cm.ORANGE)
    _centered(d, f"{date_label} TOP {len(items)}", cm.font(60), 710, cm.ORANGE)
    y = 900
    for it in items:
        label = f'{it["league"]}  {it["title"]}'
        f = cm.font(36, bold=False)
        while f.getlength(label) > RW - 200 and len(label) > 6:
            label = label[:-2] + "…"
        _centered(d, label, f, y, cm.SOFT)
        y += 78
    img.save(path)


def card_frame(card_img, idx, total, path):
    img = _frame_base()
    d = ImageDraw.Draw(img)
    img.paste(card_img, (0, 285))
    _centered(d, f"오늘의 야구 뉴스  {idx}/{total}", cm.font(40), 150, cm.WHITE)
    seg_w = (RW - 200 - (total - 1) * 16) / total
    for i in range(total):
        x = 100 + i * (seg_w + 16)
        d.rounded_rectangle([x, 1730, x + seg_w, 1742], radius=6,
                            fill=cm.ORANGE if i < idx else (52, 74, 110))
    img.save(path)


def outro_frame(path):
    img = _frame_base()
    d = ImageDraw.Draw(img)
    _centered(d, "내일도 야구 소식", cm.font(88), 700, cm.WHITE)
    _centered(d, "저장하고 팔로우하세요", cm.font(60), 840, cm.ORANGE)
    _centered(d, config.CHANNEL_NAME, cm.font(48, bold=False), 960, cm.SOFT)
    img.save(path)


def make_reel(items, card_images, date_label, out_dir: Path):
    frames_dir = out_dir / "_frames"
    frames_dir.mkdir(exist_ok=True)
    paths, durs = [], []

    p = frames_dir / "00_intro.png"
    intro_frame(items, date_label, p)
    paths.append(p); durs.append(config.REEL_INTRO_SECONDS)
    for i, img in enumerate(card_images, 1):
        p = frames_dir / f"{i:02d}_card.png"
        card_frame(img, i, len(card_images), p)
        paths.append(p); durs.append(config.REEL_CARD_SECONDS)
    p = frames_dir / "99_outro.png"
    outro_frame(p)
    paths.append(p); durs.append(config.REEL_OUTRO_SECONDS)

    f = config.REEL_FADE
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for path, d in zip(paths, durs):
        cmd += ["-framerate", "30", "-loop", "1", "-t", f"{d + f:.2f}", "-i", str(path)]
    cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]

    # 페이드 전환 체인
    parts, prev, total = [], "[0:v]", durs[0] + f
    for i in range(1, len(paths)):
        offset = total - f
        out = f"[v{i}]"
        parts.append(f"{prev}[{i}:v]xfade=transition=fade:duration={f}:offset={offset:.2f}{out}")
        prev = out
        total = offset + durs[i] + f
    parts.append(f"{prev}format=yuv420p,fps=30[v]")

    out_path = out_dir / "reel.mp4"
    cmd += ["-filter_complex", ";".join(parts), "-map", "[v]", "-map", f"{len(paths)}:a",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac",
            "-shortest", "-movflags", "+faststart", str(out_path)]
    subprocess.run(cmd, check=True)
    return out_path
