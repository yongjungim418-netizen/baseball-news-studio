import os
from pathlib import Path

BASE = Path(__file__).parent
# 서버에서는 DATA_DIR 을 영구 디스크 경로(예: /data)로 지정하세요. 재배포해도 기록이 남습니다.
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE)))
OUTPUT_DIR = DATA_DIR / "output"
DB_PATH = DATA_DIR / "studio.db"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TZ = "Asia/Seoul"
CHANNEL_NAME = os.getenv("CHANNEL_NAME", "@hanwha_kimyongjun0315")   # 카드/릴스 하단에 표시
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me")   # 관리자 로그인 비밀번호
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")

# 인터넷에 공개되는 서버(PORT 환경변수가 있는 호스팅)에서는 기본 비밀번호로 시작하지 않음
if os.getenv("PORT") and ADMIN_PASSWORD == "change-me":
    raise RuntimeError("ADMIN_PASSWORD 환경변수를 설정하세요 (기본 비밀번호로는 서버를 시작할 수 없습니다).")

# 매일 자동 실행 (서버가 계속 켜져 있어야 함). 켜려면 AUTO_DAILY=1
AUTO_DAILY = os.getenv("AUTO_DAILY", "0") == "1"
DAILY_HOUR, DAILY_MINUTE = 7, 30

# 카드에 요약 줄을 넣을지 여부. 기본은 제목만 크게 (켜려면 SHOW_SUMMARY=1)
SHOW_SUMMARY = os.getenv("SHOW_SUMMARY", "0") == "1"

CARDS_PER_DAY = 5
QUOTA = {"KBO": 2, "MLB": 2, "NPB": 1}   # 리그별 기본 개수 (부족하면 다른 리그로 채움)
MAX_AGE_HOURS = 36                        # 이보다 오래된 기사는 제외

# 뉴스 소스 (RSS). 자유롭게 추가/수정하세요.
# league 가 있으면 그 리그로 고정, filter=True 면 키워드로 리그를 판별(야구 기사만 통과)
FEEDS = [
    {"name": "Google News KBO", "league": "KBO",
     "url": "https://news.google.com/rss/search?q=KBO+%ED%94%84%EB%A1%9C%EC%95%BC%EA%B5%AC+when:1d&hl=ko&gl=KR&ceid=KR:ko"},
    {"name": "Google News MLB", "league": "MLB",
     "url": "https://news.google.com/rss/search?q=MLB+%EB%A9%94%EC%9D%B4%EC%A0%80%EB%A6%AC%EA%B7%B8+when:1d&hl=ko&gl=KR&ceid=KR:ko"},
    {"name": "Google News NPB", "league": "NPB",
     "url": "https://news.google.com/rss/search?q=NPB+%EC%9D%BC%EB%B3%B8%ED%94%84%EB%A1%9C%EC%95%BC%EA%B5%AC+when:1d&hl=ko&gl=KR&ceid=KR:ko"},
    {"name": "연합뉴스 스포츠", "filter": True,
     "url": "https://www.yna.co.kr/rss/sports.xml"},
]

LEAGUE_KEYWORDS = {
    "MLB": ["MLB", "메이저리그", "다저스", "양키스", "샌디에이고", "오타니", "김하성", "이정후"],
    "NPB": ["NPB", "일본프로야구", "요미우리", "한신", "소프트뱅크", "일본 프로야구"],
    "KBO": ["KBO", "프로야구", "LG 트윈스", "삼성 라이온즈", "KIA", "두산 베어스", "SSG", "롯데 자이언츠",
            "한화 이글스", "NC 다이노스", "키움", "KT 위즈", "야구"],
}

# (선택) Claude API 로 한국어 요약 품질 올리기: 환경변수 ANTHROPIC_API_KEY 설정
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")

# 릴스 설정
REEL_CARD_SECONDS = 4.0
REEL_INTRO_SECONDS = 2.5
REEL_OUTRO_SECONDS = 2.5
REEL_FADE = 0.5
