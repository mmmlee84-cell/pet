# 펫로드 (PetRoad) — Streamlit 버전 🐾

내 반려동물 프로필 기준으로 **입장 가능 / 조건부 / 불가**를 도착 전에 판정하는 반려동물 동반여행 앱.
한국관광공사 TourAPI 「반려동물 동반여행 서비스」(KorPetTourService) 기반.

> Next.js 버전(`../app`, `../components` 등)과 **동일한 판정 로직을 파이썬으로 포팅**한 독립 실행 앱입니다.

## 실행

```bash
# 프로젝트 루트에서
python -m venv .venv
.venv\Scripts\activate            # (PowerShell) 또는  source .venv/bin/activate
pip install -r streamlit_app/requirements.txt

streamlit run streamlit_app/app.py
```

브라우저에서 `http://localhost:8501` 자동 오픈. **API 키 없이도 목업 12곳으로 전체 기능이 동작합니다.**

## API 키 (선택)

`streamlit_app/.env` (`.env.example` 복사):

```
TOUR_API_KEY=공공데이터포털_서비스키_Decoding값
PETROAD_DATA_SOURCE=auto
```

- 발급: [data.go.kr](https://www.data.go.kr) → "한국관광공사 반려동물 동반여행 서비스" 활용신청 → 일반 인증키(Decoding)
- 키를 넣으면 자동으로 실데이터로 전환됩니다(사이드바에 소스 표시). 호출 실패 시 목업으로 폴백.

## 배포 (Streamlit Community Cloud)

키는 **코드/깃에 넣지 않고** Streamlit Secrets 로 주입합니다. 키 우선순위:
**사이드바 입력 > Streamlit Secrets > 로컬 `.env`**

1. GitHub 저장소에 푸시 (`.env*`, `.streamlit/secrets.toml`, `.venv/` 는 `.gitignore` 로 제외됨)
2. [share.streamlit.io](https://share.streamlit.io) → **New app**
   - Main file path: **`streamlit_app/app.py`**
   - (의존성은 `streamlit_app/requirements.txt` 자동 인식)
3. 앱 **Settings → Secrets** 에 아래를 붙여넣기 (TOML 형식):
   ```toml
   TOUR_API_KEY = "공공데이터포털_Decoding_서비스키"
   ```
4. 저장하면 `st.secrets` 로 자동 로드되어 🟢 실데이터로 동작합니다.

> 로컬에서 Secrets 를 테스트하려면 `streamlit_app/.streamlit/secrets.toml` 을 만들어
> (예시: `.streamlit/secrets.toml.example`) 같은 내용을 넣으면 됩니다. **커밋 금지.**

## 기능

- **내 반려동물 프로필** (사이드바, 다중 등록·전환)
- **탐색** — 검색·카테고리·필터("우리 아이 통과만" 등) + `st.map` 판정 색상 핀 + 판정 카드
- **동반조건 상세** — 체중/크기/캐리어/목줄/입마개/접종/요금/실내외/구비시설 + 신뢰 정보
- **즐겨찾기 / 내 코스** (통과 코스 자동 생성 포함) · **현장 검증 제보**
- 상단 대문 이미지: 프로젝트 루트 `dc.png`

## 구조

```
streamlit_app/
  app.py               Streamlit UI (헤더/사이드바/탐색·즐겨찾기·코스 탭)
  petroad/
    models.py          도메인 모델(dataclass)
    normalize.py       자유 텍스트 → 구조화 정책 (핵심)
    evaluate.py        통과 판정 (NO > UNKNOWN > COND > OK)
    tourapi.py         KorPetTourService1 클라이언트 + 목업 폴백
    mock_places.py     시연 장소 12곳
  tests/test_core.py   pytest (정규화·판정·목업 분포 4/5/3)
```

## 테스트

```bash
pip install pytest
pytest streamlit_app/tests -q
```
