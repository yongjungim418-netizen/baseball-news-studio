# Baseball News Studio — 하루 5장 카드뉴스 + 요약 릴스 자동 생성

KBO·MLB·NPB 뉴스를 수집 → 5개 선별(KBO 2 / MLB 2 / NPB 1) → 고정 양식 카드(출처 표기) 5장 → 9:16 요약 릴스(mp4) → 인스타 캡션까지 만듭니다.

## 실행 (내 PC) — 폰으로 쓰려면 DEPLOY.md 를 보세요
```
pip install -r requirements.txt
# FFmpeg 필요 (리눅스: apt install ffmpeg / 맥: brew install ffmpeg)
export ADMIN_PASSWORD=원하는비밀번호 CHANNEL_NAME=@내채널
python app.py          # http://localhost:5000
```
- 처음엔 **샘플로 테스트** 버튼으로 카드/릴스가 잘 나오는지 확인하세요.
- **오늘 뉴스 만들기** = 실제 수집(인터넷 필요).
- 매일 자동 실행: `AUTO_DAILY=1` (config.py 의 DAILY_HOUR/MINUTE, 기본 07:30 KST). 서버가 24시간 켜져 있어야 합니다.
  크론을 쓸 경우: `python run_daily.py`

## 승인 흐름
카드 확인 → 마음에 안 드는 뉴스는 **다른 뉴스로 교체** → **승인** → ZIP(카드 5장 + 릴스 + 캡션) 받아서 인스타에 업로드.

## 설정 (config.py)
- `FEEDS`: 뉴스 RSS 목록. 소스 추가/수정 가능 (처음엔 Google News 검색 RSS + 연합뉴스 스포츠).
- `QUOTA`: 리그별 개수, `MAX_AGE_HOURS`: 기사 최대 나이.
- 한글 폰트: 서버에 Noto Sans CJK / 나눔고딕이 없으면 `fonts/` 폴더에 .ttf/.otf 를 넣으세요
  (굵은 글씨용 파일 이름에 `Bold` 포함).

## 요약 품질 올리기 (선택)
`ANTHROPIC_API_KEY` 를 설정하면 Claude 가 제목 번역 + 핵심 3줄 요약을 만듭니다.
설정하지 않으면 RSS 에 들어있는 문구만 사용하므로 요약 줄이 비거나 짧을 수 있습니다.
요약은 제공된 제목·요약문만 근거로 쓰도록 했지만, **승인 단계에서 사실 확인**을 권장합니다.

## 저작권
기사 본문·사진은 쓰지 않고, 새로 쓴 요약 + 출처 매체명/원문 링크만 사용합니다.

## 아직 안 된 것 (다음 단계)
- 인스타 자동 게시 (Meta Graph API: 프로페셔널 계정 + 페이스북 페이지 연결 + 공개 URL 필요)
- 릴스 배경음악 (저작권 때문에 무음 + 앱에서 인기 음원 추가를 권장)
