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
def _gn(q):
    """Google News 검색 RSS 주소 (최근 1일)"""
    from urllib.parse import quote_plus
    return "https://news.google.com/rss/search?q=" + quote_plus(q + " when:1d") + "&hl=ko&gl=KR&ceid=KR:ko"


# 진짜 '이슈'가 있는 기사만 잡기 위한 검색어
_ISSUE = "(계약 OR FA OR 트레이드 OR 영입 OR 방출 OR 은퇴 OR 우승 OR 감독 OR 부상 OR 드래프트 OR 포스팅 OR 선언)"

FEEDS = [
    {"name": "Google News KBO 이슈", "league": "KBO", "url": _gn("프로야구 " + _ISSUE)},
    {"name": "Google News KBO", "league": "KBO", "url": _gn("KBO 프로야구")},
    {"name": "Google News MLB 이슈", "league": "MLB", "url": _gn("메이저리그 " + _ISSUE)},
    {"name": "Google News MLB", "league": "MLB", "url": _gn("MLB 메이저리그")},
    {"name": "Google News NPB 이슈", "league": "NPB", "url": _gn("일본프로야구 " + _ISSUE)},
    {"name": "Google News NPB", "league": "NPB", "url": _gn("NPB 일본프로야구")},
    {"name": "연합뉴스 스포츠", "filter": True, "url": "https://www.yna.co.kr/rss/sports.xml"},
]

# ---- 뉴스 품질 필터 (자유롭게 추가/수정) ----
def _env_list(name):
    return [x.strip() for x in os.getenv(name, "").split(",") if x.strip()]

# 이 단어가 제목에 있으면 무조건 버림 (도박/스팸)
BLOCK_WORDS = ["토토", "배팅", "베팅", "승부예측", "프로토", "먹튀", "카지노", "슬롯", "무료픽", "픽스터",
               "스포츠분석", "분석픽", "놀이터", "메이저사이트", "총판", "파워볼", "사다리", "[광고]", "[AD]"] + _env_list("BLOCK_EXTRA")
BLOCK_SOURCES = ["토토", "먹튀", "놀이터", "블로그", "tistory", "나무위키"]
# 알맹이 없는 기사 (사진/일정/중계 안내 등)
LOW_VALUE_PREFIXES = ["[포토]", "[사진]", "[영상]", "[화보]", "[카드뉴스]", "[오늘의", "[운세]", "[부고]", "[인사]"]
LOW_VALUE_WORDS = ["경기 일정", "편성표", "중계 방송", "선발 라인업", "선발 예고", "순위표", "오늘의 경기", "경기 결과 모음"]
# 점수 가산: 믿을 만한 매체 / 진짜 이슈 단어 / 감점 단어
TRUSTED_SOURCES = ["연합뉴스", "뉴시스", "뉴스1", "스포츠조선", "스포츠동아", "스포츠서울", "스포츠경향", "일간스포츠",
                   "OSEN", "스타뉴스", "마이데일리", "스포티비뉴스", "엑스포츠뉴스", "엠스플뉴스", "조선일보", "중앙일보",
                   "동아일보", "한국일보", "경향신문", "한겨레", "매일경제", "한국경제", "KBS", "MBC", "SBS", "YTN",
                   "국민일보", "문화일보", "세계일보", "서울신문", "이데일리", "머니투데이", "헤럴드경제"]
BOOST_WORDS = ["FA", "계약", "재계약", "트레이드", "영입", "방출", "은퇴", "우승", "한국시리즈", "월드시리즈", "일본시리즈",
               "포스팅", "선언", "감독", "부상", "수술", "신인", "드래프트", "MVP", "골든글러브", "합의", "발표", "확정",
               "단독", "속보", "승격", "복귀", "이적", "연장 계약", "공식"]
WEAK_WORDS = ["중계", "예상 라인업", "프리뷰", "하이라이트", "다시보기", "사진", "화보", "응원", "이벤트"]
# 내가 더 보고 싶은 단어 (예: 팀/선수 이름). Render 환경변수 PREFER_WORDS 에 쉼표로 넣어도 됩니다.
PREFER_WORDS = _env_list("PREFER_WORDS")

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
