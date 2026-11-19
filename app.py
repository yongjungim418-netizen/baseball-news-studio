"""Baseball News Studio - 관리자 웹사이트 (Flask)
실행: python app.py  →  브라우저에서 http://localhost:5000
"""
import io
import json
import threading
import time
import zipfile
from datetime import datetime
from functools import wraps
from zoneinfo import ZoneInfo

from flask import (Flask, abort, jsonify, redirect, render_template, request,
                   send_file, send_from_directory, session, url_for)

import config
import db
import pipeline

app = Flask(__name__, template_folder=".")
app.secret_key = config.SECRET_KEY
db.init()

JOB = {"running": False, "msg": "", "error": ""}
_lock = threading.Lock()
JOB_FILE = config.DATA_DIR / "job.json"


def _save_job(running):
    try:
        JOB_FILE.write_text(json.dumps({"running": running}))
    except Exception:
        pass


def _recover():
    """서버가 작업 도중 재시작됐으면(메모리 부족 등) 화면에 알려준다."""
    try:
        if json.loads(JOB_FILE.read_text()).get("running"):
            JOB["error"] = "이전 작업이 도중에 끊겼습니다. 서버가 재시작된 것 같습니다(메모리 부족일 수 있음)."
            _save_job(False)
    except Exception:
        pass


_recover()


def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*a, **k)
    return w


def start_job(fn, label):
    with _lock:
        if JOB["running"]:
            return False
        JOB.update(running=True, msg=label, error="")
    _save_job(True)

    def run():
        try:
            msgs = fn()
            JOB["msg"] = " / ".join(m for m in (msgs or []) if m)
        except Exception as e:
            JOB["error"] = str(e)
        finally:
            JOB["running"] = False
            _save_job(False)
    threading.Thread(target=run, daemon=True).start()
    return True


@app.route("/healthz")
def healthz():
    return "ok"


@app.route("/login", methods=["GET", "POST"])
def login():
    err = ""
    if request.method == "POST":
        if request.form.get("password") == config.ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("index"))
        err = "비밀번호가 맞지 않습니다."
    return render_template("login.html", err=err)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    date = pipeline.today()
    out = config.OUTPUT_DIR / date
    items, caption, status, v = [], "", None, 0
    if (out / "items.json").exists():
        items = json.loads((out / "items.json").read_text(encoding="utf-8"))
        caption = (out / "caption.txt").read_text(encoding="utf-8")
        v = int((out / "reel.mp4").stat().st_mtime) if (out / "reel.mp4").exists() else 0
        with db.conn() as c:
            row = c.execute("SELECT status FROM batches WHERE date=?", (date,)).fetchone()
            status = row["status"] if row else "draft"
    return render_template("index.html", date=date, items=items, caption=caption,
                           status=status, v=v, job=JOB, channel=config.CHANNEL_NAME)


@app.route("/api/status")
@login_required
def status():
    return jsonify(JOB)


@app.route("/api/run", methods=["POST"])
@login_required
def api_run():
    demo = request.form.get("demo") == "1"
    ok = start_job(lambda: pipeline.run_all(demo=demo), "뉴스 수집 · 카드 · 릴스 만드는 중…")
    return jsonify(started=ok)


@app.route("/api/replace/<int:aid>", methods=["POST"])
@login_required
def api_replace(aid):
    ok = start_job(lambda: pipeline.replace_article(aid) and [], "다른 뉴스로 교체하는 중…")
    return jsonify(started=ok)


@app.route("/api/approve", methods=["POST"])
@login_required
def api_approve():
    with db.conn() as c:
        c.execute("UPDATE batches SET status='approved', updated_at=? WHERE date=?",
                  (datetime.now(ZoneInfo(config.TZ)).isoformat(), pipeline.today()))
    return jsonify(ok=True)


@app.route("/media/<date>/<path:name>")
@login_required
def media(date, name):
    return send_from_directory(config.OUTPUT_DIR / date, name)


@app.route("/download/<date>")
@login_required
def download(date):
    folder = config.OUTPUT_DIR / date
    if not folder.exists():
        abort(404)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(folder.iterdir()):
            if f.name != "items.json":
                z.write(f, f.name)
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True,
                     download_name=f"baseball_news_{date}.zip")


def _scheduler():
    last = None
    while True:
        now = datetime.now(ZoneInfo(config.TZ))
        if (now.hour, now.minute) == (config.DAILY_HOUR, config.DAILY_MINUTE) and last != now.date():
            last = now.date()
            start_job(lambda: pipeline.run_all(), "자동 실행 중…")
        time.sleep(20)


if config.AUTO_DAILY:
    threading.Thread(target=_scheduler, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(__import__("os").getenv("PORT", "5000")))
