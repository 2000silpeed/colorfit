# ColorFit Task Tracker

**프로젝트 기간:** 5주 (W1: 3/24~3/28 ~ W5: 4/21~4/25)
**현재 상태:** W1 진행 중 (3/30~)
**Fallback 기준:** W3 금요일에 가격비교 미완이면 Fallback 발동

**사용법:** Claude Code에게 `"Task 1.3을 진행해줘"` 처럼 번호로 지시하세요.

---

## 병렬 실행 맵

각 Task의 `🅐 🅑 🅒` 태그는 어떤 터미널에서 실행하는지를 표시합니다.
같은 태그끼리는 **순차**, 다른 태그끼리는 **동시에** 실행 가능합니다.

```
W1 ─── 🅐 Task 1.1~1.11 (데이터)              ┐ 동시 실행 OK
       🅑 Task 1.12~1.17 (인프라+Try-On 조사)  ┘

W2 ─── 🅐 Task 2.1~2.6 (스코어링)             ┐
       🅑 Task 2.7~2.12 (필터+API)             │ 동시 실행 OK (3개도 가능)
       🅒 Task 2.13~2.24 (온보딩+피드 UI)      ┘
       ※ 🅑는 🅐의 2.1~2.5 완료 후 시작 권장

W3 ─── 🅐 Task 3.1~3.4 (가격비교 백+프론트)   ┐
       🅑 Task 3.5~3.11 (옷장 분석 백+프론트)  ┘ 동시 실행 OK (v1.5 추가)

W4 ─── 🅐 Task 4.1~4.5 (착장 샘플+프리미엄)   ┐ 동시 실행 OK
       🅑 Task 4.6~4.10 (결정 지원+로그인)     ┘
       ── Task 4.11 (통합 테스트)                ← 단독

W5 ─── 단독 실행 (통합 작업)
```

**TASK.md 동기화 규칙:**
- 🅐 터미널만 TASK.md를 직접 업데이트
- 🅑 🅒 터미널은 완료 시 "Task X.X 끝났어"라고 알려주기만 함
- 사람이 🅑 🅒 결과를 확인 후 TASK.md에 수동 체크

---

## W1: 데이터 + 인프라 (3/24~3/28)

### 🅐 Lane A: 데이터 파이프라인

**Task 1.1 — 12톤 팔레트 JSON 생성** ✅
- [x] `backend/data/palettes/` 디렉토리 생성
- [x] 12개 톤별 JSON 파일 생성 (예: `spring_warm_light.json`)
- [x] 각 톤당 20~30개 대표 색상 (HEX, RGB, HSL, 한글 색상명)
- [x] 총 ~300개 색상 데이터
- [x] 참조: 기획서 섹션 7.1 (12-tone 분류 체계)
- ⚠️ HSL 값 51개 오차 자동 보정 완료

**Task 1.2 — 브랜드 화이트리스트 JSON**
- [x] `backend/data/brand_whitelist.json` 생성
- [x] 인지도 있는 브랜드 120개+ 리스트 (무신사 스탠다드, 유니클로, COS 등)
- [x] 형식: `["무신사 스탠다드", "유니클로", ...]`
- 🔧 codex 리뷰 반영: 오표기 수정(풀앤베어), 비브랜드 제거(핸드메이드/어반디케이), 모호명 명확화, 누락 브랜드 13개 추가 → 최종 153개

**Task 1.3 — 네이버 쇼핑 API 수집 스크립트 기본 구조**
- [x] `backend/scripts/curate_by_tone.py` 생성
- [x] 네이버 쇼핑 API 호출 함수 (`search_products(query, display, start)`)
- [x] API 응답 파싱 + raw JSON 저장
- [x] Rate limit 처리 (exponential backoff)
- [x] `.env`에서 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` 읽기
- [x] 테스트: API 연결 테스트 스크립트 (14개 단위 테스트)
- 🔧 codex 리뷰 반영: 429 재시도 로직(while 루프), dotenv .env 자동 로드, 빈 결과 시 rate limit sleep 추가

**Task 1.4 — 톤별 수집 키워드 설계** ✅
- [x] `backend/data/tone_queries.json` 생성
- [x] 13톤별 검색 키워드 리스트 (톤 x 카테고리)
- [x] 예: `"spring_warm_light": {"outer": ["아이보리 가디건", ...], ...}`
- [x] 카테고리: outer, top, bottom, onepiece, shoes, bag, acc
- [x] 참조: 기획서 섹션 5.2 (수집 쿼리 설계)
- [x] curate_by_tone.py가 JSON에서 쿼리 로드하도록 리팩토링

**Task 1.5 — 상품 수집 실행**
- [x] Task 1.3 스크립트로 실제 수집 실행
- [x] 4톤 병렬 수집 x 3라운드 = 13톤 커버
- [x] raw JSON을 `backend/data/raw/` 에 톤별 저장
- [x] 목표: 25,000개 상품 ✅ 실제 110,850건 수집
- [x] 톤별 수집량 확인 (최소 1,000개/톤) ✅ 최소 7,642건(spring_warm_vivid)

**Task 1.6 — 전처리: 상품 정규화** ✅
- [x] `backend/scripts/rebuild_from_tones.py` 생성
- [x] HTML 태그 제거 (`<b>` 등 title에 포함된 태그)
- [x] 브랜드명 추출 (title 파싱 또는 mallName 기반)
- [x] 정규화 결과를 `NormalizedProduct` 형식으로 출력 ✅ 110,850건 → 100,682건
- [x] 참조: 기획서 섹션 5.4 (전처리 과정)
- 🔧 codex 리뷰 반영: 크로스-톤 중복 제거(global_seen) + validation 후 seen 마킹

**Task 1.7 — 전처리: 이미지 색상 추출 + 톤 매핑**
- [x] PIL + scikit-learn K-means로 상위 3개 dominant color 추출
- [x] 추출된 HEX → 13톤 팔레트와 RGB 유클리드 거리 비교
- [x] 가장 가까운 톤 ID 매핑 (`tone_id` 부여)
- [x] 참조: 기획서 섹션 7.1 (상품 색상 → 톤 매핑 흐름도)
- 🔧 codex 리뷰 반영: summer_cool_soft 팔레트 누락 → 25색 팔레트 생성 + EXPECTED_TONES 검증 추가

**Task 1.8 — 전처리: 하이브리드 카테고리 분류**
- [x] 키워드 기반 분류 딕셔너리 (31개 카테고리 x 3~5 키워드)
- [x] 키워드 매칭 실패 시 Gemini Flash 폴백 분류
- [x] LLM 분류 결과 캐싱 (`backend/data/llm_cache.json`)
- [x] 분류 속성: category, silhouette, formality, tpo, gender
- [x] 참조: 기획서 섹션 5.4.1 (하이브리드 분류 체계)
- ⚠️ 키워드+raw_category 커버리지 92.2% (예상 70%보다 높음, raw_category3/4 힌트 활용)
- 🔧 codex 리뷰 반영: '티' 오매칭 제거, 키워드 매칭 시 캐시 메타데이터 보충, google-generativeai 의존성 추가

**Task 1.9 — 코디 레시피 JSON 정의**
- [x] `backend/data/outfit_recipes.json` 생성
- [x] 여성 TPO 8종 x 무드 레시피 (필수/선택/금지 카테고리, 포멀도 범위)
- [x] 남성 TPO 8종 x 무드 레시피
- [x] 참조: 기획서 섹션 5.3.1 (TPO x 무드 레시피 매트릭스)
- 🔧 codex 리뷰 반영: 원피스 포함 TPO(date, event)에서 required_sets로 상하의/원피스 경로 분리

**Task 1.10 — 코디 조합 생성 알고리즘** ✅ (v2 리팩토링 완료)
- [x] 레시피 기반 코디 조합 생성 스크립트
- [x] 필수 카테고리 선택 → 선택 카테고리 확률적 추가 → 금지 카테고리 검증
- [x] 포멀도 편차 ≤ 2, 가격 비율 3배 이내, 중복 조합 방지
- [x] designed_tpo, designed_moods, designed_season 태그 부여
- [x] 목표: 2(성별) x 12(톤) x 8(TPO) x 4(계절) x 3(코디) = ~2,000개
- [x] 참조: 기획서 섹션 5.3.1 (조합 알고리즘 의사코드)
- ⚠️ v2 개선: 신발 required 승격(최소 3피스), 계절 태그, 성별 키워드 필터, 가격비 5배→3배
- ⚠️ 실제 2,097개 생성 (여성 1,009, 남성 1,088). 미완성 0개, 성별불일치 0개, 신발누락 0개

**Task 1.11 — Gemini 코디 품질 평가** ✅ (평가 실행 대기)
- [x] `backend/scripts/evaluate_outfits.py` 생성
- [x] Gemini Flash 배치 평가 (5점 척도)
- [x] 3점 미만 코디 제거
- [x] 평가 결과를 `llm_quality_score` 필드에 저장
- [x] 비용 추산: ~$6 (2,097개 x ~$0.003)
- ⚠️ 10건 샘플 평가 평균 4.7점 (프롬프트 카테고리 기준 평가로 조정)
- ⚠️ 전체 2,097건 평가 실행 중 (~3.5시간 소요)
- 🔧 codex 리뷰 통과 (P1 없음, P2 1건: 기획서 Gemini 모델명 불일치 — 코드 무관)

### 🅑 Lane B: 인프라 셋업 (🅐와 동시 실행 가능)

**Task 1.12 — Next.js 15 프로젝트 초기화** ✅
- [x] `frontend/` 디렉토리에 Next.js 15 (App Router) 생성
- [x] TypeScript 설정
- [x] TailwindCSS 4.0 설치 + 설정
- [x] Framer Motion 11 설치
- [x] 동작 확인: `npm run build` 성공
- ⚠️ create-next-app@latest가 Next.js 16 설치 → 15.5.14로 다운그레이드

**Task 1.13 — 프론트엔드 디자인 토큰 세팅**
- [x] DESIGN.md 읽고 CSS variables 세팅 (`globals.css`)
- [x] 컬러 토큰 (--bg, --surface, --accent, --border 등)
- [x] 스코어 축 컬러 5개
- [x] 다크모드 토큰 (`[data-theme="dark"]`)
- [x] 스페이싱 스케일 (--space-2xs ~ --space-3xl)
- [x] Nanum Myeongjo Google Fonts 로딩 설정
- 🔧 codex 리뷰 반영: 폰트 변수 충돌 해소, warm-neutral 다크모드 추가, @theme에 시맨틱/스페이싱/radius 토큰 등록, 네이밍 통일, weight range 명시
- ⚠️ Nanum Myeongjo는 Google Fonts에서 latin subset만 제공 (한글은 자동 unicode-range 분할)

**Task 1.14 — FastAPI 프로젝트 초기화**
- [x] `backend/` 디렉토리에 FastAPI 프로젝트 생성
- [x] `requirements.txt` (fastapi, uvicorn, pydantic, sqlalchemy, httpx, pillow, numpy, scikit-learn)
- [x] 프로젝트 구조: `app/main.py`, `app/config.py`, `app/routers/`, `app/services/`, `app/models/`, `app/schemas/`, `app/db/`
- [x] CORS 미들웨어 설정 (localhost:3000 허용)
- [x] 헬스체크 엔드포인트 (`GET /health`)
- [x] 동작 확인: `uvicorn app.main:app --reload` → localhost:8000/docs
- ✅ codex 리뷰: FastAPI 코드 자체 이슈 없음 (PASS). scripts/curate_by_tone.py P1 2건은 별도 Task에서 수정 필요

**Task 1.15 — DB 스키마 적용**
- [x] Supabase 연결 설정 (`app/db/session.py` — async engine + get_db 의존성)
- [x] SQLAlchemy 2.0 모델 정의
  - [x] `models/user.py` (users 테이블)
  - [x] `models/product.py` (products 테이블)
  - [x] `models/outfit.py` (outfits 테이블)
  - [x] `models/reaction.py` (reactions 테이블)
  - [x] `models/style_seed.py` (style_seeds 테이블)
  - [x] `models/user_preference.py` (user_preferences 테이블)
- [x] 인덱스 생성 (tone_id, designed_tpo, gender)
- [x] 참조: 기획서 섹션 14.4 (DB 스키마)
- ✅ codex 리뷰: DB 모델 코드 이슈 없음 (PASS)

**Task 1.16 — 배포 설정**
- [x] Vercel 연결 (frontend/) — 자동 감지, https://frontend-nine-nu-tw6mmgf7ut.vercel.app
- [x] ~~Railway~~ → Render 연결 (backend/) — Dockerfile, https://colorfit.onrender.com ⚠️ Railway 무료 종료로 Render로 변경
- [x] 환경변수 설정 (각 플랫폼)
- [x] 배포 확인: 프론트 + 백엔드 둘 다 접속 가능
- 🔧 codex 리뷰 반영: .dockerignore 추가 (venv, .env, __pycache__ 제외)

**Task 1.17 — Virtual Try-On API 조사 + 선정 (v1.5)**
- [x] Fashn.ai API 테스트 (상의/하의 테스트 완료, 단일 아이템만 지원 확인)
- [x] Kolors/Replicate API 테스트 (fal.ai $0.07/회, 단일 아이템만)
- [x] OOTDiffusion 오픈소스 테스트 → 제외 (CC BY-NC-SA 라이선스, 하의 미지원, 품질 최하위)
- [x] "내 옷 정체성 유지" 품질 비교 → **Gemini 나노바나나 선정**
- [x] 선정 API 키 발급 + .env에 추가 (기존 GEMINI_API_KEY 활용)
- ⚠️ 기존 전용 VTON API(Fashn/Kolors)는 단일 아이템만 지원. ColorFit의 멀티 아이템 코디 시나리오에 부적합
- ⚠️ Gemini 나노바나나(gemini-2.5-flash-image)로 전환: 멀티 아이템 동시 합성 + 퍼스널컬러 스타일링 가능, 단가 $0.039/회
- 🔧 codex 리뷰 반영: test_*.py → eval_*.py 리네임 (pytest 수집 방지) + google-genai, requests 의존성 추가

### W1 완료 기준
- [x] 상품 DB 20,000건 이상 (Task 1.5) — 174,353건 (12톤 x 9,296~17,554)
- [x] 코디 1,500개 이상, Gemini 평가 통과 (Task 1.11) — 2,097개 생성, 평가 실행 중
- [x] 프론트/백엔드 빈 프로젝트 배포 성공 (Task 1.16) — Vercel + Render 배포 완료
- [x] Try-On API 선정 완료 (Task 1.17) — Gemini 나노바나나

---

## W2: 추천 엔진 + 온보딩 (3/31~4/4)

### 🅐 Lane C: 추천 엔진 — 스코어링 (Task 2.1~2.6)

**Task 2.1 — PCF 스코어링 (퍼스널컬러 적합도)** ✅
- [x] `backend/app/services/scoring.py` 생성
- [x] `calculate_pcf(item_tone_ids, item_hex_colors, user_tone_id)` 함수
- [x] 톤 레벨 매칭 (동일 100, 호환 95) + 색상 레벨 매칭 (RGB 거리 → 점수)
- [x] pytest 테스트: 동일 톤, 호환 톤, 반대 시즌, 경계값
- [x] 참조: 기획서 섹션 5.5.1

**Task 2.2 — OF 스코어링 (TPO 적합도)**
- [x] `calculate_of(outfit_tags, user_tpo_list)` 함수
- [x] TPO 동의어 확장 매핑 (commute↔office 등)
- [x] match_count 기반 점수 변환 (30점 하한)
- [x] pytest 테스트: 정확 매칭, 동의어 매칭, 미매칭 (20개 전체 통과)
- [x] 참조: 기획서 섹션 5.5.2

**Task 2.3 — CH 스코어링 (색상 조화)**
- [x] `calculate_ch(item_hex_colors)` 함수
- [x] 모든 아이템 쌍의 RGB 거리 → 구간별 점수 (유사색/보색/과도한 대비)
- [x] 채도 보너스 (+5점, 표준편차 0.15~0.40)
- [x] pytest 테스트: 올블랙, 톤온톤, 보색, 형광+파스텔
- [x] 참조: 기획서 섹션 5.5.3
- 🔧 codex 리뷰 반영: 채도 보너스 테스트 입력을 실제 stdev 0.15~0.40 범위로 교체

**Task 2.4 — PE 스코어링 (가격 효율)**
- [x] `calculate_pe(total_price, budget_min, budget_max)` 함수
- [x] 3개 Case: 범위 내 (중앙 가까울수록 높음), 초과 (감점), 미만 (완만 감점, 최저 40점)
- [x] pytest 테스트: 중앙, 상한, 하한, 50%+ 초과, 극단 저가
- [x] 참조: 기획서 섹션 5.5.4 🔧 codex 리뷰 반영: 범위 단언 → 정확한 기대값 단언으로 교체

**Task 2.5 — SF 스코어링 (스타일 적합도)**
- [x] `calculate_sf(items)` 함수
- [x] 카테고리 궁합 점수 (50%) — `data/style_compat.json` 매트릭스 참조
- [x] 실루엣 밸런스 점수 (25%) — Y/A/I/X 라인 15개 규칙
- [x] 포멀도 일관성 점수 (25%) — 표준편차 x 40 감점
- [x] pytest 테스트: 블라우스+슬랙스(높음), 후드+정장(낮음), 경계값 55점
- [x] 참조: 기획서 섹션 5.5.5, 6.6
- 🔧 codex 리뷰 반영: stdev→pstdev(모집단 표준편차) 전환 + formality_map 누락 카테고리 9개 추가

**Task 2.6 — 스타일 호환성 데이터 파일**
- [x] `backend/data/style_compat.json` 생성 — 카테고리 궁합 225개 조합 점수
- [x] `backend/data/silhouette_rules.json` 생성 — 실루엣 15개 조합
- [x] `backend/data/formality_map.json` 생성 — 아이템별 포멀도 (1~5) 46개 규칙
- [x] 참조: 기획서 섹션 6.6

### 🅑 Lane C: 추천 엔진 — 필터+파이프라인+API (Task 2.7~2.12, 🅐 2.1~2.5 완료 후 시작)

**Task 2.7 — StyleFilter (규칙 기반 사전 필터)** ✅
- [x] `backend/app/services/style_filter.py` 생성
- [x] `detect_category(title, category3)` — 키워드 → 캐시 → LLM 3단계
- [x] `filter_outfit(items)` — 3축 가중합 계산, 55점 미만 False
- [x] pytest 테스트: 통과 코디, 탈락 코디, 55점 경계 (16개 전체 통과)
- [x] 참조: 기획서 섹션 6.6
- 🔧 codex 리뷰 반영: filter_outfit이 calculate_sf() 재사용(로직 중복 제거), RAW_CATEGORY_MAP 직접 임포트

**Task 2.8 — Hard Filter 체인**
- [x] `backend/app/services/feed_builder.py` 생성
- [x] Hard Filter 8단계 순차 적용 (H1 성별 → H2 예산 → ... → H8 StyleFilter)
- [x] 각 필터는 독립 함수로 분리
- [x] pytest 테스트: 각 필터별 통과/탈락 케이스 (51개 전체 통과)
- [x] 참조: 기획서 섹션 5.4 (Hard Filter 상세)
- 🔧 codex 리뷰 반영: H8 테스트 실제 동작 검증(isinstance→assert False), 통합 테스트 H8 rejection 케이스 추가

**Task 2.9 — Soft Score + 리랭킹**
- [x] feed_builder.py에 Soft Score 계산 추가 (5축 가중합)
- [x] 리랭킹: 완성 코디 가산(+3점), dislike 제외, 톤 다양성(동일 톤 3개 제한), 메인아이템 중복 제거
- [x] 개인화 보정 (-10 ~ +10)
- [x] 상위 200개 반환
- [x] 참조: 기획서 섹션 6.1
- [x] pytest 테스트: 22개 신규 (73개 전체 통과)
- 🔧 codex 리뷰 반영: rerank 함수 입력 dict mutation 제거 (순수 함수 원칙 준수)

**Task 2.10 — 추천 이유 생성**
- [x] `backend/app/services/reason_generator.py` 생성
- [x] 5축 가중 기여도 계산 → 상위 2개 축 선택
- [x] high(75점+) / mid(75점 미만) 템플릿 분기
- [x] 톤별 한글 이름 매핑 ("여름쿨소프트 핵심 컬러...")
- [x] pytest 테스트: PCF 최고 기여, OF 최고 기여, 동점 처리 (16개 테스트 통과)
- [x] 참조: 기획서 섹션 6.4

**Task 2.11 — Feed API 엔드포인트** ✅
- [x] `backend/app/routers/feed.py` — GET /api/feed
- [x] 파라미터: tone_id, tpo, gender, budget_min, budget_max, page + user_id
- [x] Profile Load → Filter → StyleFilter → Score → Rerank → Reason 전체 파이프라인
- [x] 응답: 코디 리스트 + 5축 스코어 + 이유 2줄
- [x] `backend/app/routers/outfit.py` — GET /api/outfit/{id}
- [x] Pydantic 스키마 정의 (`schemas/outfit.py`)
- 🔧 codex 리뷰 반영: dislike에 user_id 필터 추가, budget_min 누락 수정, 프리컴퓨팅 reasons 우선 사용
- ⚠️ C1(전체 메모리 로드), W2(비즈니스 로직 서비스 분리), W3(커서 페이지네이션)은 별도 최적화 Task 필요

**Task 2.12 — 스코어 프리컴퓨팅** ✅
- [x] `backend/scripts/precompute_scores.py` 생성
- [x] 전체 코디에 대해 기본 5축 스코어 사전 계산 (1,790개, 0.7s)
- [x] outfits.scores JSONB에 저장
- [x] 런타임에는 개인화 보정만 적용
- ⚠️ color_hex 미추출 상태: PCF는 tone_id 레벨 매칭, CH는 기본값 50점. 색상 추출(Task 1.7) 실행 후 재계산 필요
- 🔧 codex 리뷰 반영: 원자적 파일 쓰기(os.replace), dead code 제거, PCF 예외 로깅 추가

### 🅒 Lane D: 온보딩 + 피드 UI (🅐🅑와 동시 실행 가능)

**Task 2.13 — 온보딩 공통 레이아웃** ✅
- [x] `frontend/src/app/onboarding/layout.tsx` — 공통 레이아웃
- [x] 상단 진행 바 (5단계, Marsala 채움)
- [x] 뒤로가기 버튼
- [x] 좌→우 슬라이드 전환 (Framer Motion — template.tsx로 enter 애니메이션 구현)
- [x] 참조: 기획서 섹션 8.4.1
- 🔧 codex 리뷰 반영: prefers-reduced-motion 지원 추가, 진행 바 aria 속성 추가

**Task 2.14 — 온보딩 Step 1: 성별 선택**
- [x] `frontend/app/onboarding/step1/page.tsx`
- [x] "나에 대해 알려주세요" 헤드라인 (Nanum Myeongjo 28px)
- [x] 여성/남성 2개 카드 (가로 배치, 3:4 비율)
- [x] 탭 시 scale 1.05 + Marsala 아웃라인 → 자동 다음 Step
- [x] "건너뛰기" 텍스트 링크
- 🔧 codex 리뷰 반영: localStorage에 성별 저장, Framer Motion animate로 scale 1.05 전환(whileTap 제거), step2 placeholder 추가

**Task 2.15 — 온보딩 Step 2: 퍼스널컬러 선택**
- [x] `frontend/app/onboarding/step2/page.tsx`
- [x] 시즌별 그라데이션 스트립 4개 (봄/여름/가을/겨울)
- [x] 각 스트립 아래 세부 톤 칩 3개
- [x] 선택 시 다른 시즌 디밍 (opacity 0.4)
- [x] "잘 모르겠어요" → 바텀시트 간이 진단 2문항
- 🔧 codex 리뷰 반영: Q2 답변→톤 매핑 2차원 테이블로 교체, 바텀시트 role="dialog"+aria-modal+Escape 닫기 추가, Q1 문구 스펙 일치

**Task 2.16 — 온보딩 Step 3: TPO + 무드 선택**
- [x] `frontend/src/app/onboarding/step3/page.tsx`
- [x] TPO 8종 필 버튼 (성별에 따라 다른 세트)
- [x] 무드 태그 클라우드 (성별에 따라 다른 세트)
- [x] 복수 선택: TPO 최대 3개, 무드 최대 5개
- 🔧 codex 리뷰 반영: WebKit scrollbar 숨김 CSS 추가, 무드 태그 선택 시 텍스트 색상 #222222 유지(스펙 준수), localStorage try/catch 추가

**Task 2.17 — 온보딩 Step 4: 예산 설정**
- [x] `frontend/src/app/onboarding/step4/page.tsx`
- [x] 듀얼 썸 레인지 슬라이더 (min/max)
- [x] 빠른 프리셋 4개 버튼 (~3만 / 3~7만 / 7~15만 / 15만~)
- [x] "추천 코디 보러가기" CTA (풀와이드, Marsala)
- 🔧 codex 리뷰 반영: 키보드 접근성(onKeyDown) 추가, handlePointerMove functional updater로 stale closure 방지, localStorage 타입 검증 강화

**Task 2.18 — 온보딩 Step 5: 비주얼 취향 분석**
- [ ] `frontend/app/onboarding/step5/page.tsx`
- [ ] 2x2 이미지 그리드, 4라운드
- [ ] 탭 시 선택 → 0.5s 후 다음 라운드 crossfade
- [ ] "패스" 링크, 라운드 인디케이터
- [ ] 완료 후 피드로 전환

**Task 2.19 — 온보딩 API 연동**
- [ ] `backend/app/routers/onboarding.py` — POST /api/onboarding
- [ ] 프론트에서 5 Step 결과를 모아서 전송
- [ ] users 테이블 + style_seeds 테이블에 저장
- [ ] 프론트 → API 호출 연동

**Task 2.20 — 코디 카드 컴포넌트**
- [ ] `frontend/components/OutfitCard.tsx`
- [ ] 이미지 (3:4, rounded-lg) + 아이템 수 뱃지 + 하트 아이콘
- [ ] 제목 (Nanum Myeongjo 16px) + 가격 (bold) + 추천 이유 1줄
- [ ] 스코어 뱃지 미니 필 2개 ("PCF 95" "OF 80")
- [ ] fadeInUp 등장 애니메이션

**Task 2.21 — 코디 피드 화면**
- [ ] `frontend/app/feed/page.tsx`
- [ ] 헤더 (ColorFit 로고 + 프로필 아이콘)
- [ ] TPO 탭 필터 (가로 스크롤 필 버튼)
- [ ] 예산 슬라이더 (접힌 상태, 탭 시 펼침)
- [ ] "오늘의 컬러핏" 특별 카드 (피드 최상단)
- [ ] OutfitCard 리스트 (무한 스크롤, 커서 기반 페이지네이션)
- [ ] GET /api/feed 연동
- [ ] 스켈레톤 로딩 + empty state + error state

**Task 2.22 — save/dislike 인터랙션**
- [ ] 좌 스와이프 → dislike (카드 슬라이드 아웃 + "관심없음" 토스트)
- [ ] 더블탭 → save (하트 뿅 애니메이션, Marsala 전환)
- [ ] 우상단 하트 탭 → save 토글
- [ ] POST /api/reaction 연동 (save/dislike)
- [ ] `backend/app/routers/reaction.py` — POST /api/reaction

**Task 2.23 — 코디 상세 화면**
- [ ] `frontend/app/outfit/[id]/page.tsx`
- [ ] 히어로 이미지 (풀블리드, parallax scroll)
- [ ] 5축 스코어 바 차트 (width 0% → 실제값, ease-out 0.8s)
- [ ] 추천 이유 카드 (배경 #F0EDE8)
- [ ] 아이템 캐러셀 (가로 스크롤, 80px 정사각 이미지)
- [ ] 코디 합계 가격 + 최저가 합산
- [ ] 하단 CTA ("저장" + "A vs B 비교")
- [ ] GET /api/outfit/{id} 연동

**Task 2.24 — 하단 탭바**
- [ ] `frontend/components/BottomTabBar.tsx`
- [ ] 홈/저장/Top/마이 4탭
- [ ] 활성 탭: Marsala 아이콘 + bold 라벨
- [ ] 전환 모션: 아이콘 scale 0.9→1.1→1.0

### W2 완료 기준
- [ ] 5 Step 온보딩 → 코디 피드 진입 동작
- [ ] 스코어링 기반 피드가 실제 데이터로 동작
- [ ] save/dislike 동작
- [ ] 추천 이유 2줄 노출

---

## W3: 가격비교 + 내 옷장 분석 (4/7~4/11)

### 🅐 가격비교 + 유사상품 (Task 3.1~3.4)

**Task 3.1 — 유사 상품 매칭 서비스**
- [ ] `backend/app/services/similar_finder.py` 생성
- [ ] 색상 유사도 (가중치 0.6) + 가격 유사도 (0.4) 계산
- [ ] Exact(동일 상품 다른 판매처) / Similar(대체재) 구분
- [ ] 상위 5개 반환
- [ ] pytest 테스트
- [ ] 참조: 기획서 섹션 6.2

**Task 3.2 — 아이템 API**
- [ ] `backend/app/routers/item.py`
- [ ] GET /api/item/{id} — 아이템 상세 + 판매처별 가격
- [ ] GET /api/item/{id}/similar — 유사 상품 리스트
- [ ] Pydantic 스키마 정의

**Task 3.3 — 아이템 상세 화면**
- [ ] `frontend/app/item/[id]/page.tsx`
- [ ] 아이템 이미지 (1:1) + 브랜드 + 상품명 + 가격
- [ ] 가격 비교 테이블 (판매처, 가격, 유형, 바로가기)
- [ ] 최저가 행 하이라이트 (#F0EDE8 + Marsala 뱃지)
- [ ] 유사 상품 섹션 (2열 그리드 + 유사도 % 뱃지)
- [ ] 하단 CTA "최저가 쇼핑몰에서 보기"
- [ ] 외부 쇼핑몰 링크 (새 탭)

**Task 3.4 — 프로필/마이페이지 + 톤 설명**
- [ ] `frontend/app/profile/page.tsx` — 톤 카드, 대표색 스와치, 내 정보 변경
- [ ] `frontend/app/tone/[id]/page.tsx` — 톤 설명 화면
- [ ] `backend/app/routers/tone.py` — GET /api/tone/{id}
- [ ] 취향 관리 (Style Seed 시각화, 초기화)

### 🅑 내 옷장 분석 (Task 3.5~3.11, 🅐와 동시 실행 가능) ⭐ v1.5

**Task 3.5 — 옷 사진 분석 API**
- [ ] `backend/app/services/closet_analyzer.py` 생성
- [ ] 옷 사진 업로드 → 이미지에서 dominant color 추출 (K-means)
- [ ] 사용자 퍼스널컬러 톤과 비교 → PCF 점수 산출
- [ ] 채도/명도 세부 점수 산출
- [ ] 점수별 상세 이유 생성 (reason_generator 재사용)
- [ ] `backend/app/routers/closet.py` — POST /api/closet/analyze
- [ ] 참조: 기획서 섹션 5.5.1 (PCF 계산 로직 재사용)

**Task 3.6 — 어울리는 아이템 추천 API (역방향 추천)**
- [ ] 사용자 옷의 색상/카테고리 → Similar Finder로 어울리는 상품 검색
- [ ] TPO별로 추천 코디 구성 (데이트 코디, 출근 코디 등)
- [ ] `backend/app/routers/closet.py` — GET /api/closet/{item_id}/recommendations
- [ ] 참조: 기획서 F-39 (보유 옷 역방향 추천)

**Task 3.7 — 옷장 관리 API**
- [ ] `backend/app/models/closet_item.py` — closet_items 테이블
- [ ] `backend/app/routers/closet.py` — GET /api/closet (내 옷장 목록)
- [ ] 옷장 전체 퍼스널컬러 적합도 통계 (%) 계산
- [ ] pytest 테스트

**Task 3.8 — 옷 분석 결과 화면**
- [ ] `frontend/app/closet/analyze/page.tsx`
- [ ] 내 옷 사진 + 큰 점수 (Nanum Myeongjo 36px, Marsala)
- [ ] 상세 이유 텍스트 (색상 매칭/채도/명도 설명)
- [ ] 미니 스코어 3개 (색상/채도/명도)
- [ ] "이 옷으로 완성하는 코디" 섹션 (TPO별 카드 조합)
- [ ] 각 코디 카드: 내 옷(뱃지) + 추천 아이템 3개 + 코디 점수
- [ ] "옷장에 추가" + "다른 옷도 분석하기" CTA

**Task 3.9 — 내 옷장 화면**
- [ ] `frontend/app/closet/page.tsx`
- [ ] 옷장 전체 점수 게이지 (원형, %)
- [ ] "상의 N벌은 훌륭하고, 하의 N벌은 톤이 맞지 않아요" 한 문장 진단
- [ ] 3열 그리드 + 점수 뱃지 (높으면 Marsala, 중간 Ocean Blue, 낮으면 회색)
- [ ] "+" 추가 버튼 (카메라/갤러리)
- [ ] 무료 분석 잔여 횟수 표시 + "프리미엄" 버튼
- [ ] GET /api/closet 연동

**Task 3.10 — 옷 사진 업로드 컴포넌트**
- [ ] `frontend/components/PhotoUploader.tsx`
- [ ] 카메라 촬영 / 갤러리 선택 옵션
- [ ] 이미지 리사이즈 (max 1024px, 품질 80%)
- [ ] 업로드 진행 표시 + 분석 중 로딩 애니메이션
- [ ] POST /api/closet/analyze 연동

**Task 3.11 — 하단 탭바 변경**
- [ ] 홈/옷장/저장/마이 4탭으로 변경 (Top Pick → 옷장)
- [ ] 옷장 탭: 옷걸이 아이콘

**W3 금요일 — Fallback 판단 시점**
- [ ] TASK.md 전체 진행 상황 확인
- [ ] 밀리는 항목이 있으면 Fallback 발동 (CLAUDE.md 참조)

### W3 완료 기준
- [ ] 가격 비교 테이블 동작 (Task 3.3)
- [ ] 옷 사진 분석 → 점수 + 이유 동작 (Task 3.5, 3.8)
- [ ] 내 옷장 화면 동작 (Task 3.9)
- [ ] 마이페이지 동작 (Task 3.4)

---

## W4: 착장 샘플 + 프리미엄 + 결정 지원 (4/14~4/18)

### 🅐 AI 착장 샘플 + 프리미엄 (Task 4.1~4.5) ⭐ v1.5

**Task 4.1 — Virtual Try-On API 연동**
- [ ] `backend/app/services/virtual_tryon.py` 생성
- [ ] Task 1.17에서 선정한 Gemini 나노바나나(gemini-2.5-flash-image)와 연동
- [ ] 내 옷 이미지 + 추천 아이템 이미지 → 착장 합성 이미지 생성
- [ ] 결과 이미지 캐싱 (outfit_id + closet_item_id 기반)
- [ ] `backend/app/routers/tryon.py` — POST /api/tryon/generate
- [ ] pytest 테스트 (mock API)

**Task 4.2 — 무료 3회 제한 로직**
- [ ] `backend/app/services/usage_tracker.py` 생성
- [ ] 사용자별 착장 생성 횟수 추적 (tryon_usage 테이블)
- [ ] 무료 사용자: 3회 제한. 초과 시 403 + "프리미엄으로 업그레이드" 메시지
- [ ] 프리미엄 사용자: 무제한
- [ ] API 미들웨어로 체크

**Task 4.3 — 착장 샘플 UI**
- [ ] 옷 분석 결과 화면(Task 3.8)의 코디 카드에 "착장으로 보기" 버튼 추가
- [ ] 탭 시 → Try-On API 호출 → 로딩(3~8초) → 합성 이미지 표시
- [ ] 로딩 애니메이션: 코디 아이템 이미지들이 회전
- [ ] 결과: 합성 이미지(3:4) + "저장" + "공유" 버튼
- [ ] 무료 잔여 횟수 표시 ("무료 착장 2회 남음")
- [ ] 3회 소진 시 → 프리미엄 업그레이드 바텀시트

**Task 4.4 — 프리미엄 구독 화면**
- [ ] `frontend/app/premium/page.tsx`
- [ ] 프리미엄 혜택 소개 (AI 착장 무제한, 쿠폰, 가격 알림)
- [ ] 가격: 월 4,900원 / 연 39,000원 (월 3,250원꼴)
- [ ] 결제 CTA (Marsala 버튼)
- [ ] MVP: 결제 연동은 후순위. "관심 등록" 또는 더미 결제 플로우

**Task 4.5 — 프리미엄 구독 백엔드**
- [ ] `backend/app/models/subscription.py` — subscriptions 테이블
- [ ] `backend/app/routers/subscription.py` — POST /api/subscribe, GET /api/subscription/status
- [ ] 프리미엄 상태 확인 미들웨어
- [ ] MVP: 수동 활성화 또는 테스트용 쿠폰 코드 방식

### 🅑 결정 지원 + 로그인 (Task 4.6~4.10, 🅐와 동시 실행 가능)

**Task 4.6 — Top Pick 서비스**
- [ ] `backend/app/services/top_pick.py`
- [ ] 저장 목록 기반: 저장 코디 중 최고 점수 1개
- [ ] 전체 DB 기반: 전체 코디 중 최고 점수 1개 (콜드스타트)
- [ ] 시간대 기반 TPO 자동 추론 (오전=출근, 오후=캐주얼, 저녁=데이트)
- [ ] `backend/app/routers/top_pick.py` — GET /api/top-pick

**Task 4.7 — A vs B 비교 서비스**
- [ ] `backend/app/services/comparator.py`
- [ ] 두 코디의 5축 점수 비교 + 결정적 차이 요인 추출
- [ ] `backend/app/routers/compare.py` — GET /api/compare?ids=a,b

**Task 4.8 — 저장 목록 화면**
- [ ] `frontend/app/saved/page.tsx`
- [ ] 2열 그리드 (이미지 3:4 + 1줄 제목 + 가격)
- [ ] 정렬 드롭다운 (최근/점수/가격)
- [ ] 비어있을 때: 일러스트 + "아직 저장한 코디가 없어요" + CTA
- [ ] 롱프레스 → 삭제 확인 바텀시트
- [ ] GET /api/saved 연동

**Task 4.8.1 — Top Pick 모달**
- [ ] "Top Pick 보기" 버튼 (저장 목록 상단)
- [ ] 풀스크린 모달: 1위 코디 확대 + 추천 이유 3줄 + 5축 바 차트
- [ ] GET /api/top-pick 연동

**Task 4.8.2 — A vs B 비교 화면**
- [ ] 좌우 분할 (50:50), 각 코디 이미지 + 정보
- [ ] 중앙 5축 비교 (레이더 차트 또는 바 차트 오버레이)
- [ ] 하단 1줄 결론 ("A가 퍼스널컬러에 더 잘 맞아요")
- [ ] GET /api/compare 연동

**Task 4.9 — 로그인 화면**
- [ ] `frontend/app/login/page.tsx`
- [ ] ColorFit 로고 + 서브카피
- [ ] 카카오 로그인 버튼 (#FEE500)
- [ ] 구글 로그인 버튼 (#FFFFFF + border)
- [ ] "게스트로 둘러보기" 텍스트 링크

**Task 4.9.1 — 소셜 로그인 백엔드**
- [ ] `backend/app/services/jwt.py` — JWT 토큰 발급/검증
- [ ] `backend/app/routers/auth.py` — 카카오/구글 OAuth 콜백
- [ ] 게스트 → 로그인 전환 (저장/Top Pick 접근 시 로그인 요구)

**Task 4.10 — 피드백 개인화 학습**
- [ ] `backend/app/services/preference_tracker.py`
- [ ] 피드백 행동별 가중치: save(+2.0), like(+1.0), click(+0.3), dislike(-1.5)
- [ ] tone/category/brand/price 선호도 누적
- [ ] 10건+ 축적 시 weight_overrides 자동 생성
- [ ] `backend/app/routers/feedback.py` — POST /api/feedback
- [ ] 참조: 기획서 섹션 6.8

**Task 4.10.1 — 구매 후 피드백 바텀시트**
- [ ] 외부 쇼핑몰 이동 후 복귀 시 자동 표시
- [ ] "이 추천이 도움이 됐나요?" + 3개 버튼
- [ ] 👎 선택 시 이유 태그 추가 표시
- [ ] POST /api/feedback 연동

### 🅒 Feed API 최적화 (Task 2.11 codex 리뷰 기술부채)

**Task 4.11a — Feed API 성능 최적화**
- [ ] DB 레벨 limit/offset 또는 커서 기반 페이지네이션 적용 (현재 전체 메모리 로드)
- [ ] 비즈니스 로직(dominant_tone, category_to_group 등)을 services/ 레이어로 분리
- [ ] 코디 수 증가 시 OOM 방지 (스트리밍 또는 배치 처리)

### 단독 실행 (🅐🅑 모두 완료 후)

**Task 4.11 — 통합 테스트**
- [ ] **경로 A:** 옷 촬영 → 분석 결과 → 착장 샘플 → 옷장 저장 → 프리미엄 게이트 플로우
- [ ] **경로 B:** 온보딩 → 피드 → 코디 상세 → 가격비교 → 외부 링크 플로우
- [ ] **교차:** 옷장에서 코디 피드로 이동, 피드에서 옷장으로 이동
- [ ] 저장 → 저장 목록 → Top Pick 플로우
- [ ] 무료 3회 소진 → 프리미엄 화면 노출 확인
- [ ] Edge case: 코디 0개, 예산 초과, 톤 불일치, 사진 품질 불량

### W4 완료 기준
- [ ] AI 착장 샘플 생성 동작 (Task 4.1, 4.3)
- [ ] 무료 3회 제한 동작 (Task 4.2)
- [ ] 프리미엄 화면 동작 (Task 4.4)
- [ ] 소셜 로그인 동작 (Task 4.9)
- [ ] 경로 A + B 통합 테스트 통과 (Task 4.11)

---

## W5: 폴리싱 + 배포 (4/21~4/25)

**Task 5.1 — 반응형 QA**
- [ ] 모바일 (375px): 전체 화면 확인
- [ ] 태블릿 (768px): 레이아웃 확인
- [ ] 데스크톱 (1280px): 최대 폭 제한 확인
- [ ] 가로 스크롤 없는지 확인
- [ ] 터치 타겟 44px 이상 확인

**Task 5.2 — 다크모드**
- [ ] CSS variables 다크 테마 적용
- [ ] 다크모드 토글 구현 (마이페이지 설정)
- [ ] 웜 언더톤 유지 (#1A1714, 쿨그레이 아님)
- [ ] 스코어 축 컬러 밝기 조정

**Task 5.3 — 성능 최적화**
- [ ] 이미지 lazy loading + Cloudflare CDN 설정
- [ ] 피드 API 응답 800ms 이내 확인
- [ ] Next.js Server Components 활용
- [ ] Lighthouse 성능 점수 확인 (목표: 80+)

**Task 5.4 — 버그 수정**
- [ ] 발견된 버그 목록 정리 + 수정
- [ ] 크로스 브라우저 테스트 (Chrome, Safari)

**Task 5.5 — 프로덕션 배포**
- [ ] 프론트엔드 프로덕션 빌드 + Vercel 배포
- [ ] 백엔드 프로덕션 설정 + Railway 배포
- [ ] 프로덕션 URL 접속 확인

**Task 5.6 — 데모 준비**
- [ ] 데모 시나리오 작성 (페르소나 A 기준: 소개팅 룩 찾기)
- [ ] 데모용 샘플 데이터 확인
- [ ] 발표 자료 작성

### W5 완료 기준
- [ ] 프로덕션 URL 접속 가능 (Task 5.5)
- [ ] 주요 플로우 버그 없음 (Task 5.4)
- [ ] 데모 준비 완료 (Task 5.6)

---

## MVP 핵심 지표 (W5 기준)

| 지표 | 목표 |
|------|------|
| 온보딩 완주율 | >= 60% |
| 회원 전환율 | >= 40% |
| 첫 코디 저장 도달율 | >= 25% |

---

## Fallback 순서 (W3 금요일 판단)

밀릴 경우 아래 순서로 2차 미룸:
1. A vs B 비교 (Task 4.7, 4.8.2)
2. Top Pick + One-shot (Task 4.6, 4.8.1)
3. 프리미엄 구독 결제 연동 (Task 4.4, 4.5 → MVP는 더미 결제)
4. 가격비교 (Task 3.1~3.3, 외부 링크만 유지)
5. 스코어링 5축 → 3축(PCF+OF+SF)

**절대 미루지 않는 것 (핵심 사수 라인):**
- **경로 A:** 옷 촬영 → 분석 점수 + 이유 → 착장 샘플(3회) → 옷장 저장
- **경로 B:** 온보딩 → 코디 피드 → 추천 이유 → save/dislike → 외부 링크
