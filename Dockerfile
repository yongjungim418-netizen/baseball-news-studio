FROM python:3.12-slim

# FFmpeg(릴스) + 한글 폰트(카드 이미지)
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg fonts-noto-cjk \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PYTHONUNBUFFERED=1 DATA_DIR=/data
RUN mkdir -p /data

# 작업 상태(JOB)를 프로세스 안에 보관하므로 worker 는 반드시 1개, 스레드로 동시 처리
CMD ["sh", "-c", "gunicorn -w 1 --threads 4 --timeout 120 -b 0.0.0.0:${PORT:-5000} app:app"]
