# 서버에 올리기 (폰으로 접속하려면)

필요한 것: GitHub 계정 + Render(또는 Railway) 계정

## 1. GitHub에 올리기 (폰 브라우저 가능)
1. ZIP을 폰 파일 앱에서 압축 해제합니다.
2. github.com 에서 새 저장소(Private 권장)를 만듭니다.
3. `uploading an existing file`(또는 `Add file → Upload files`)에서 압축 푼 **파일 16개 전부**를 선택해 올리고 Commit 합니다.
   (폴더가 없는 구조라 파일만 고르면 됩니다. `Dockerfile` 도 꼭 포함하세요.)

## 2. Render 에서 배포
1. render.com → New → **Blueprint** → 위 저장소 선택. (`render.yaml` 이 자동 적용됨)
2. 입력 칸이 나오면:
   - `ADMIN_PASSWORD`: 관리자 비밀번호 (필수, 길게)
   - `CHANNEL_NAME`: 예) @내_야구_채널
   - `ANTHROPIC_API_KEY`: 선택 (넣으면 요약이 좋아집니다)
3. 배포가 끝나면 `https://baseball-news-studio-xxxx.onrender.com` 주소가 생깁니다. 폰 브라우저로 접속하세요.

## 주의
- 무료 플랜은 잠들고(자동 실행이 안 돌고) 디스크가 지워지므로, 매일 자동 실행을 쓰려면 유료 상시 실행 플랜이 필요합니다.
- 자동 실행 시간은 `config.py` 의 `DAILY_HOUR`/`DAILY_MINUTE` (한국 시간 07:30).
- Railway 를 쓰려면 같은 저장소를 연결하고(Dockerfile 자동 인식), Volume 을 `/data` 에 붙이고, 위 환경변수를 같은 이름으로 넣으세요.
- 서버를 공개하므로 비밀번호는 꼭 직접 정한 값으로 설정하세요. 기본값이면 서버가 시작되지 않게 막아뒀습니다.
