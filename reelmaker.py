"""카드 5장 → 9:16 요약 릴스(mp4). FFmpeg 필요.

저사양 서버(무료 플랜)에서도 돌도록 프레임을 한 장씩 FFmpeg 로 흘려보내는 방식입니다.
(페이드 전환도 파이썬에서 계산 → FFmpeg 은 인코딩만, 스레드 1개)
"""
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image, ImageDraw

import cardmaker as cm
import config

RW, RH = 1080, 1920
FPS = 24
ENC = ["-preset", "ultrafast", "-tune", "stillimage", "-crf", "22",
       "-x264-params", "ref=1:rc-lookahead=0:bframes=0:threads=1"]


def _frame_base():
    img = Image.new("RGB", (RW, RH), cm.NAVY)
    ImageDraw.Draw(img).rectangle([0, 0, 18, RH], fill=cm.ORANGE)
    return img


def _centered(d, text, f, y, fill):
    d.text(((RW - f.getlength(text)) / 2, y), text, font=f, fill=fill)


def intro_frame(items, date_label):
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
    return img


def card_frame(card_img, idx, total):
    img = _frame_base()
    d = ImageDraw.Draw(img)
    img.paste(card_img, (0, 285))
    _centered(d, f"오늘의 야구 뉴스  {idx}/{total}", cm.font(40), 150, cm.WHITE)
    seg_w = (RW - 200 - (total - 1) * 16) / total
    for i in range(total):
        x = 100 + i * (seg_w + 16)
        d.rounded_rectangle([x, 1730, x + seg_w, 1742], radius=6,
                            fill=cm.ORANGE if i < idx else (52, 74, 110))
    return img


def outro_frame():
    img = _frame_base()
    d = ImageDraw.Draw(img)
    _centered(d, "내일도 야구 소식", cm.font(88), 700, cm.WHITE)
    _centered(d, "저장하고 팔로우하세요", cm.font(60), 840, cm.ORANGE)
    _centered(d, config.CHANNEL_NAME, cm.font(48, bold=False), 960, cm.SOFT)
    return img


def make_reel(items, card_images, date_label, out_dir: Path):
    t0 = time.time()
    print("[reel] 시작", flush=True)

    n = len(card_images)
    makers = [lambda: intro_frame(items, date_label)]
    durs = [config.REEL_INTRO_SECONDS]
    for i, img in enumerate(card_images, 1):
        makers.append(lambda i=i, img=img: card_frame(img, i, n))
        durs.append(config.REEL_CARD_SECONDS)
    makers.append(outro_frame)
    durs.append(config.REEL_OUTRO_SECONDS)

    out_path = out_dir / "reel.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{RW}x{RH}", "-framerate", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-c:v", "libx264"] + ENC + [
           "-pix_fmt", "yuv420p", "-threads", "1", "-filter_threads", "1",
           "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(out_path)]
    if shutil.which("nice"):          # 웹 서버가 멈추지 않도록 우선순위를 낮춤
        cmd = ["nice", "-n", "10"] + cmd

    err = tempfile.TemporaryFile()
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=err)
    nf = max(1, round(config.REEL_FADE * FPS))
    try:
        img = makers[0]()
        for i in range(len(makers)):
            raw = img.tobytes()
            for _ in range(round(durs[i] * FPS)):
                proc.stdin.write(raw)
            del raw
            if i < len(makers) - 1:                      # 다음 장으로 페이드
                nxt = makers[i + 1]()
                for k in range(1, nf + 1):
                    proc.stdin.write(Image.blend(img, nxt, k / (nf + 1)).tobytes())
                img = nxt
        proc.stdin.close()
    except BrokenPipeError:
        pass
    finally:
        rc = proc.wait()
    if rc != 0:
        err.seek(0)
        raise RuntimeError("영상 인코딩 실패: " + err.read().decode(errors="ignore")[-300:])
    print(f"[reel] 완료 {time.time() - t0:.0f}초", flush=True)
    return out_path
