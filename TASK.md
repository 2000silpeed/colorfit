# ColorFit TASK.md — 구현 태스크 관리

> **최종 수정:** 2026-03-23 | **상태 범례:** ⬜ TODO · 🔄 진행중 · ✅ 완료 · ⏸ 보류 · ❌ 취소
> **관련 문서:** [PRD.md](./PRD.md) · [TRD.md](./TRD.md) · [ColorFit_상세기획서_v1.0.md](./docs/ColorFit_상세기획서_v1.0.md)
>
> 이 파일은 구현의 단일 소스(Single Source of Truth)입니다.
> 태스크 완료 시 즉시 상태를 업데이트하고, 필요 시 PRD/TRD도 동기화하세요.

---

## 진행 현황 요약

| 주차 | 기간 | 목표 | 진행률 |
|------|------|------|--------|
| W0 | ~3/23 | 기획·설계 완료 | ✅ 100% |
| W1 | 3/24~3/28 | 프로젝트 셋업 + 데이터 수집 + 온보딩 UI | 🔄 진행중 |
| W2 | 3/31~4/4 | 추천 엔진 코어 + 코디 피드 UI | ⬜ 0% |
| W3 | 4/7~4/11 | 가격 비교 + 유사 상품 + 아이템 상세 | ⬜ 0% |
| W4 | 4/14~4/18 | 결정 지원 + 통합 테스트 | ⬜ 0% |
| W5 | 4/21~4/25 | 버그 수정 + 발표 준비 | ⬜ 0% |

---

## W0: 기획·설계 (완료)

| # | 태스크 | 상태 | 산출물 |
|---|--------|------|--------|
| W0-1 | 페르소나·여정·기능 리스트 정리 | ✅ | unified_user_journey.md |
| W0-2 | 상세 기획서 작성 | ✅ | ColorFit_상세기획서_v1.0.md |
| W0-3 | PRD 작성 | ✅ | PRD.md |
| W0-4 | TRD 작성 | ✅ | TRD.md |
| W0-5 | TASK 작성 | ✅ | TASK.md (이 파일) |

---

## W1: 프로젝트 셋업 + 데이터 수집 + 온보딩 UI (3/24~3/28)

### W1-A: 프로젝트 초기 셋업

| # | 태스크 | 상태 | 담당 | 의존성 | 비고 |
|---|--------|------|------|--------|------|
| W1-A1 | Git 저장소 생성 + monorepo 구조 설정 | ✅ | — | — | `frontend/` + `backend/` + `docs/` |
| W1-A2 | Next.js 15 프로젝트 초기화 (App Router + TS + Tailwind) | ✅ | FE | W1-A1 | `npx create-next-app@latest` |
| W1-A3 | FastAPI 프로젝트 초기화 (가상환경 + requirements.txt) | ⬜ | BE | W1-A1 | Python 3.13 |
| W1-A4 | PostgreSQL DB 생성 (Supabase 또는 Docker) | ⬜ | BE | — | |
| W1-A5 | DB 스키마 마이그레이션 (users, products, outfits, reactions) | ⬜ | BE | W1-A4 | TRD 3.1 참조 |
| W1-A6 | Redis 셋업 (Upstash 또는 Docker) | ⬜ | BE | — | |
| W1-A7 | 환경 변수 설정 (.env.local, .env) | ⬜ | ALL | W1-A2, W1-A3 | API 키, DB URL, OAuth 키 |
| W1-A8 | CORS 설정 + FastAPI 기본 라우터 구조 | ⬜ | BE | W1-A3 | |
| W1-A9 | Vercel 배포 연결 (FE) | ⬜ | FE | W1-A2 | |
| W1-A10 | Railway 배포 연결 (BE) | ⬜ | BE | W1-A3 | |

### W1-B: 데이터 수집 + 전처리

| # | 태스크 | 상태 | 담당 | 의존성 | 비고 |
|---|--------|------|------|--------|------|
| W1-B1 | 12-tone 팔레트 JSON 데이터 구축 (12파일) | ⬜ | BE | — | TRD 3.2 참조. 톤당 20~30개 대표색 |
| W1-B2 | 네이버 쇼핑 API 수집 스크립트 (`collect_naver.py`) | ⬜ | BE | W1-A7 | 카테고리×시즌 쿼리, 20,000건 목표 |
| W1-B3 | 무신사 크롤링 스크립트 (`crawl_musinsa.py`) | ⬜ | BE | — | robots.txt 준수, 5,000건 목표 |
| W1-B4 | 이미지 색상 추출 모듈 (`color_extractor.py`) | ⬜ | BE | — | K-means top 3 → 대표 HEX |
| W1-B5 | 색상 → 톤 매핑 모듈 (`color_matcher.py`) | ⬜ | BE | W1-B1 | HEX → 12-tone 유클리드 거리 |
| W1-B6 | 상품 전처리 스크립트 (`preprocess.py`) | ⬜ | BE | W1-B2~B5 | HTML 제거, 카테고리 정규화, 톤 매핑 |
| W1-B7 | 코디 조합 생성 스크립트 (`generate_outfits.py`) | ⬜ | BE | W1-B6 | 상의+하의 조합, 톤 일치 필터, 800~1,500 세트 |
| W1-B8 | 시드 데이터 DB 삽입 (`seed_data.py`) | ⬜ | BE | W1-B6, W1-B7, W1-A5 | products + outfits 테이블 |

### W1-C: 온보딩 UI

| # | 태스크 | 상태 | 담당 | 의존성 | 비고 |
|---|--------|------|------|--------|------|
| W1-C1 | 랜딩 페이지 (`/`) | ⬜ | FE | W1-A2 | 헤드라인 + CTA "무료로 시작하기" |
| W1-C2 | 온보딩 Step 1: 12-tone 스와치 그리드 (`/onboarding/step1`) | ⬜ | FE | W1-B1 | 12개 톤 카드, 1탭 선택, 대표색 프리뷰 |
| W1-C3 | 온보딩 Step 2: TPO + 스타일 무드 (`/onboarding/step2`) | ⬜ | FE | — | 8종 TPO 버튼 + 6종 무드 칩 |
| W1-C4 | 온보딩 Step 3: 예산 슬라이더 (`/onboarding/step3`) | ⬜ | FE | — | 듀얼 슬라이더 min/max |
| W1-C5 | 온보딩 프로그레스 바 + 스킵 옵션 | ⬜ | FE | — | Step 1/3 표시, "나중에 할래요" |
| W1-C6 | `POST /api/onboarding` API | ⬜ | BE | W1-A5 | 프로필 저장 |
| W1-C7 | 온보딩 완료 → 피드 리다이렉트 연결 | ⬜ | FE | W1-C2~C6 | |

**W1 마일스톤 (M1):** 상품 DB 20,000건 + 코디 800세트 + 온보딩 3 Step 동작
**완료 기준:** 온보딩 3단계 입력 → DB 저장 → `/feed` 리다이렉트

---

## W2: 추천 엔진 코어 + 코디 피드 UI (3/31~4/4)

### W2-A: 추천 엔진

| # | 태스크 | 상태 | 담당 | 의존성 | 비고 |
|---|--------|------|------|--------|------|
| W2-A1 | OutfitScorer 모듈 (`scoring.py`) | ⬜ | BE | W1-B5 | PCF×0.35 + OF×0.25 + CH×0.20 + PE×0.20 |
| W2-A2 | personalColorFit 계산 로직 | ⬜ | BE | W1-B5 | 코디 아이템 tone vs 사용자 tone 거리 |
| W2-A3 | occasionFit 계산 로직 | ⬜ | BE | — | TPO 태그 매칭 비율 |
| W2-A4 | colorHarmony 계산 로직 | ⬜ | BE | — | 60-30-10 법칙 기반 |
| W2-A5 | priceEfficiency 계산 로직 | ⬜ | BE | — | 예산 대비 효율 |
| W2-A6 | Reranker (isComplete 가산 + dislike 제외 + 다양성) | ⬜ | BE | W2-A1 | |
| W2-A7 | ReasonGenerator 모듈 (`reason_generator.py`) | ⬜ | BE | W2-A1 | 상위 2개 기여 요인 → 자연어 템플릿 |
| W2-A8 | FeedBuilder 통합 모듈 (`feed_builder.py`) | ⬜ | BE | W2-A1~A7 | 필터→스코어→리랭크→이유생성 파이프라인 |
| W2-A9 | `GET /api/feed` API (페이지네이션, TPO 필터, 예산 필터) | ⬜ | BE | W2-A8 | Redis 캐시 5분 |
| W2-A10 | scoring 유닛 테스트 | ⬜ | BE | W2-A1~A5 | pytest |

### W2-B: 코디 피드 UI

| # | 태스크 | 상태 | 담당 | 의존성 | 비고 |
|---|--------|------|------|--------|------|
| W2-B1 | OutfitCard 컴포넌트 | ⬜ | FE | — | 이미지+1줄요약+가격+이유+save/dislike |
| W2-B2 | TPOTabs 컴포넌트 | ⬜ | FE | — | 상단 가로 스크롤 탭, 활성 상태 |
| W2-B3 | BudgetSlider 컴포넌트 (피드 상단) | ⬜ | FE | — | 변경 시 피드 리패칭 |
| W2-B4 | 피드 페이지 (`/feed`) + 무한 스크롤 | ⬜ | FE | W2-A9, W2-B1~B3 | @tanstack/react-query |
| W2-B5 | save 버튼 동작 (낙관적 업데이트) | ⬜ | FE | — | 하트 토글 + POST /api/reaction |
| W2-B6 | dislike 버튼/스와이프 (피드에서 즉시 제거) | ⬜ | FE | — | framer-motion 스와이프 제스처 |
| W2-B7 | `POST /api/reaction` API | ⬜ | BE | W1-A5 | save/dislike/view_reason 저장 |
| W2-B8 | 하단 탭바 (홈, 피드, 저장, 마이) | ⬜ | FE | — | |

**W2 마일스톤 (M2+M3):** 온보딩 → 개인화 코디 피드 전환 + 추천 이유 2줄 표시
**완료 기준:** /feed에서 TPO 탭 전환 + 코디 카드 + 추천 이유 + save/dislike 동작

---

## W3: 가격 비교 + 유사 상품 + 아이템 상세 (4/7~4/11)

### W3-A: 백엔드

| # | 태스크 | 상태 | 담당 | 의존성 | 비고 |
|---|--------|------|------|--------|------|
| W3-A1 | `GET /api/outfit/{id}` API (코디 상세) | ⬜ | BE | W1-B8 | 코디+아이템+점수+이유 |
| W3-A2 | `GET /api/item/{id}` API (아이템 상세 + 판매처 가격) | ⬜ | BE | W1-B8 | Exact 판매처 리스트 |
| W3-A3 | SimilarFinder 모듈 (`similar_finder.py`) | ⬜ | BE | W1-B5 | 카테고리+색상 유사도 기반, 상위 5개 |
| W3-A4 | `GET /api/item/{id}/similar` API | ⬜ | BE | W3-A3 | match_type(exact/similar) + 유사도% |
| W3-A5 | 코디 전체 최저가 합산 로직 | ⬜ | BE | W3-A2 | 아이템별 최저 가격 합산 |
| W3-A6 | 톤 설명 API `GET /api/tone/{tone_id}` | ⬜ | BE | W1-B1 | static JSON 서빙 |

### W3-B: 프론트엔드

| # | 태스크 | 상태 | 담당 | 의존성 | 비고 |
|---|--------|------|------|--------|------|
| W3-B1 | 코디 상세 페이지 (`/outfit/[id]`) | ⬜ | FE | W3-A1 | 전체 이미지+이유+뱃지+아이템 캐러셀 |
| W3-B2 | ScoreBadge 컴포넌트 | ⬜ | FE | — | PCF/OF 바 차트 (0~100) |
| W3-B3 | ReasonCard 컴포넌트 (2줄 + 상세 펼치기) | ⬜ | FE | — | 펼치기 시 view_reason 이벤트 발생 |
| W3-B4 | 아이템 캐러셀 컴포넌트 | ⬜ | FE | — | 가로 스크롤, 각 아이템 탭 → 상세 이동 |
| W3-B5 | 아이템 상세 페이지 (`/item/[id]`) | ⬜ | FE | W3-A2 | 상품 정보 + 가격 비교 테이블 |
| W3-B6 | PriceCompareTable 컴포넌트 | ⬜ | FE | — | Exact/Similar 구분, 최저가 강조 |
| W3-B7 | SimilarProductList 컴포넌트 | ⬜ | FE | W3-A4 | 유사 상품 카드 리스트, 유사도% |
| W3-B8 | 외부 링크 버튼 (새 탭 or 인앱 브라우저) | ⬜ | FE | — | 클릭 이벤트 로깅 |
| W3-B9 | 톤 설명 페이지 (`/profile` 내 또는 별도) | ⬜ | FE | W3-A6 | 대표색 스와치 + 추천/비추천 |
| W3-B10 | 저장 목록 페이지 (`/saved`) | ⬜ | FE | W2-B7 | 저장한 코디 리스트 |

**W3 마일스톤 (M4):** 코디 상세 + 아이템 상세 + 가격 비교 + 유사 상품 + 외부 링크 동작
**완료 기준:** 피드→코디 상세→아이템 상세→가격 비교→외부 링크 전체 플로우 동작

---

## W4: 결정 지원 + 인증 + 통합 테스트 (4/14~4/18)

### W4-A: 결정 지원 기능

| # | 태스크 | 상태 | 담당 | 의존성 | 비고 |
|---|--------|------|------|--------|------|
| W4-A1 | TopPick 모듈 (`top_pick.py`) | ⬜ | BE | W2-A1 | 저장 중 total_score max 선정 |
| W4-A2 | `GET /api/top-pick` API | ⬜ | BE | W4-A1 | 1개 코디 + 강조 이유 |
| W4-A3 | A vs B 비교 모듈 | ⬜ | BE | W2-A1 | 4축 나란히 비교 + 가장 큰 차이 축 판정 |
| W4-A4 | `POST /api/compare` API | ⬜ | BE | W4-A3 | {outfit_a_id, outfit_b_id} → 비교 결과 |
| W4-A5 | One-shot 추천 로직 (오늘의 컬러핏) | ⬜ | BE | W2-A8 | 현재 TPO 추론 + 최적 1~3개 |

### W4-B: 결정 지원 UI

| # | 태스크 | 상태 | 담당 | 의존성 | 비고 |
|---|--------|------|------|--------|------|
| W4-B1 | Top Pick UI (저장 목록 내 강조 카드) | ⬜ | FE | W4-A2 | "가장 잘 어울리는 코디" 배너 |
| W4-B2 | A vs B 비교 페이지 (`/compare`) | ⬜ | FE | W4-A4 | CompareView 컴포넌트, 축별 바 비교 |
| W4-B3 | "오늘의 컬러핏" 버튼 (홈/피드 상단) | ⬜ | FE | W4-A5 | 1~3개 즉시 노출 |

### W4-C: 인증

| # | 태스크 | 상태 | 담당 | 의존성 | 비고 |
|---|--------|------|------|--------|------|
| W4-C1 | 카카오 OAuth 연동 (BE) | ⬜ | BE | W1-A7 | REST API 방식 |
| W4-C2 | 구글 OAuth 연동 (BE) | ⬜ | BE | W1-A7 | |
| W4-C3 | JWT 토큰 발급/검증 미들웨어 | ⬜ | BE | — | python-jose |
| W4-C4 | 로그인 UI (소셜 버튼) | ⬜ | FE | W4-C1~C2 | 카카오/구글 버튼 |
| W4-C5 | 게스트 모드 처리 (저장 시 가입 유도 모달) | ⬜ | FE | W4-C4 | |
| W4-C6 | 자동 로그인 (토큰 저장 + 재방문 시 복원) | ⬜ | FE | W4-C3 | localStorage |
| W4-C7 | 마이페이지 (`/profile`) + 로그아웃 | ⬜ | FE | W4-C4 | 프로필 요약 + 온보딩 수정 링크 |

### W4-D: 통합 테스트

| # | 태스크 | 상태 | 담당 | 의존성 | 비고 |
|---|--------|------|------|--------|------|
| W4-D1 | E2E 시나리오 테스트: 온보딩→피드→상세→외부 링크 | ⬜ | ALL | W3 완료 | 수동 테스트 |
| W4-D2 | E2E 시나리오 테스트: save→저장목록→Top Pick | ⬜ | ALL | W4-A~B 완료 | 수동 테스트 |
| W4-D3 | E2E 시나리오 테스트: A vs B 비교 | ⬜ | ALL | W4-B2 | 수동 테스트 |
| W4-D4 | 모바일 반응형 검수 (Chrome DevTools) | ⬜ | FE | — | iPhone SE/14, Galaxy S24 |
| W4-D5 | 성능 테스트 (Lighthouse) | ⬜ | FE | — | LCP ≤ 3초 목표 |
| W4-D6 | API 에러 핸들링 점검 | ⬜ | BE | — | 400/401/404/500 응답 |

**W4 마일스톤 (M5):** 전체 MVP 완성 — 핵심 플로우 + 결정 지원 + 인증 동작
**완료 기준:** PRD 섹션 9 릴리스 기준 전체 체크

---

## W5: 버그 수정 + 발표 준비 (4/21~4/25)

| # | 태스크 | 상태 | 담당 | 의존성 | 비고 |
|---|--------|------|------|--------|------|
| W5-1 | W4-D 테스트에서 발견된 버그 수정 | ⬜ | ALL | W4-D | |
| W5-2 | UI 폴리시 (간격, 폰트, 색상 일관성) | ⬜ | FE | — | |
| W5-3 | 데모 시나리오 확정 (A 진단러 + D 결정 피로형) | ⬜ | ALL | — | |
| W5-4 | 발표 자료 작성 (9슬라이드) | ⬜ | ALL | — | |
| W5-5 | 데모 영상 녹화 (2분) | ⬜ | ALL | W5-3 | |
| W5-6 | 최종 배포 확인 (Vercel + Railway 프로덕션) | ⬜ | ALL | — | |

**W5 마일스톤 (M6):** 발표 준비 완료
**완료 기준:** 발표 자료 + 데모 영상 + 프로덕션 배포 완료

---

## MVP 크리티컬 패스 + 병렬 실행 전략

> **MVP 데모 플로우:** 랜딩 → 온보딩(3step) → 코디 피드(TPO탭+카드+이유+save/dislike) → 코디 상세 → 아이템 상세 → 가격 비교 → 외부 링크
> **릴리스 기준 (PRD §9):** 온보딩→피드 전환 / 피드 20개+이유 / 아이템+가격+외부링크 / save·dislike / 소셜 로그인 1개+ / 모바일 반응형

---

### Phase 1: 기반 셋업 (W1 전반)

```
🟦 BE 트랙                          🟩 FE 트랙                        🟨 데이터 트랙
─────────────────────────          ─────────────────────────        ─────────────────────────
W1-A3  FastAPI 초기화               W1-C1  랜딩 페이지                W1-B1  12-tone 팔레트 JSON
W1-A4  PostgreSQL DB 생성           W1-C3  온보딩 Step2 (TPO+무드)
W1-A5  DB 스키마 마이그레이션        W1-C4  온보딩 Step3 (예산)
W1-A7  환경 변수 설정               W1-C5  프로그레스 바+스킵
W1-A8  CORS + 라우터 구조
```

**⚡ 병렬:** BE/FE/데이터 3트랙 동시 진행 가능
**📌 주의:** W1-C2(톤 스와치 그리드)는 W1-B1(팔레트 JSON) 완료 후 진행
**⏸ 후순위 이동:** W1-A6(Redis), W1-A9(Vercel 배포), W1-A10(Railway 배포) → Phase 5로 이동

---

### Phase 2: 데이터 파이프라인 + 온보딩 완성 (W1 후반)

```
🟦 BE 트랙                                    🟩 FE 트랙
──────────────────────────────────           ─────────────────────────
W1-B2  네이버 쇼핑 API 수집  ──┐             W1-C2  온보딩 Step1 (톤 선택) ← W1-B1
W1-B3  무신사 크롤링        ──┤ (병렬)       W1-C6  POST /api/onboarding ← W1-A5
W1-B4  이미지 색상 추출     ──┘             W1-C7  온보딩 완료 → 피드 리다이렉트
W1-B5  색상→톤 매핑         ← W1-B1
W1-B6  상품 전처리          ← W1-B2~B5
W1-B7  코디 조합 생성       ← W1-B6
W1-B8  시드 데이터 DB 삽입  ← W1-B6,B7,A5
```

**⚡ 병렬:** B2+B3+B4 동시 수집 가능 / FE 온보딩 마무리는 BE와 병렬
**🎯 Phase 2 완료 = M1 마일스톤:** 온보딩 3step → DB 저장 → /feed 리다이렉트

---

### Phase 3: 추천 엔진 + 피드 UI (W2)

```
🟦 BE 트랙 (순차)                              🟩 FE 트랙 (mock 데이터로 선행 가능)
──────────────────────────────────           ─────────────────────────────────
W2-A1  OutfitScorer 모듈                     W2-B1  OutfitCard 컴포넌트         ──┐
W2-A2  personalColorFit ──┐                  W2-B2  TPOTabs 컴포넌트            ──┤ (병렬)
W2-A3  occasionFit      ──┤ (병렬)           W2-B3  BudgetSlider 컴포넌트       ──┘
W2-A4  colorHarmony     ──┤                  W2-B5  save 버튼 (낙관적 업데이트) ──┐ (병렬)
W2-A5  priceEfficiency  ──┘                  W2-B6  dislike 버튼/스와이프       ──┘
W2-A7  ReasonGenerator                       W2-B4  피드 페이지 + 무한 스크롤   ← BE API 연동
W2-A8  FeedBuilder 통합
W2-A9  GET /api/feed API
W2-B7  POST /api/reaction API
```

**⚡ 병렬:** A2~A5 스코어링 4축 동시 개발 / B1~B3 컴포넌트 mock으로 선행 개발 / B5+B6 병렬
**📌 순차:** A1→(A2~A5)→A7→A8→A9 → B4(API 연동) 순서 준수
**🎯 Phase 3 완료 = M2+M3 마일스톤:** 피드 TPO 탭 + 코디 카드 + 추천 이유 + save/dislike

---

### Phase 4: 상세 페이지 + 가격 비교 (W3)

```
🟦 BE 트랙                                    🟩 FE 트랙
──────────────────────────────────           ─────────────────────────────────
W3-A1  GET /api/outfit/{id}  ──┐             W3-B2  ScoreBadge 컴포넌트        ──┐
W3-A2  GET /api/item/{id}   ──┤ (병렬)       W3-B3  ReasonCard 컴포넌트        ──┤ (병렬)
W3-A3  SimilarFinder 모듈   ──┘             W3-B4  아이템 캐러셀 컴포넌트     ──┤
W3-A4  GET /api/item/{id}/similar            W3-B6  PriceCompareTable          ──┤
W3-A5  코디 전체 최저가 합산                  W3-B8  외부 링크 버튼             ──┘
                                              W3-B1  코디 상세 페이지 ← A1 연동
                                              W3-B5  아이템 상세 페이지 ← A2 연동
                                              W3-B7  SimilarProductList ← A4 연동
```

**⚡ 병렬:** A1+A2+A3 동시 개발 / B2~B4+B6+B8 컴포넌트 mock 선행
**🎯 Phase 4 완료 = M4 마일스톤:** 피드→코디상세→아이템상세→가격비교→외부링크 전체 플로우

---

### Phase 5: 인증 + 배포 + 통합 테스트 (W4)

```
🟦 BE 트랙                          🟩 FE 트랙                        🟧 인프라 트랙
─────────────────────────          ─────────────────────────        ─────────────────────────
W4-C1  카카오 OAuth (BE)            W4-C4  로그인 UI (소셜 버튼)     W1-A9   Vercel 배포 연결
W4-C2  구글 OAuth (BE)   (병렬)     W4-C5  게스트 모드+가입 유도      W1-A10  Railway 배포 연결
W4-C3  JWT 미들웨어                 W4-C6  자동 로그인                W1-A6   Redis 셋업 (캐시)
W4-D6  API 에러 핸들링 점검         W4-C7  마이페이지+로그아웃
                                    W4-D1  E2E: 온보딩→피드→상세→링크
                                    W4-D4  모바일 반응형 검수
```

**⚡ 병렬:** C1+C2 소셜 로그인 동시 / 인프라 배포는 독립 진행 / Redis는 이 시점에 추가
**📌 인증 최소 조건:** 카카오 OR 구글 1개만 완성해도 MVP 릴리스 가능
**🎯 Phase 5 완료 = M5 마일스톤:** PRD §9 릴리스 기준 전체 충족

---

### Phase 6: Should — 여유 시 구현

| 우선순위 | 태스크 | 이유 |
|---------|--------|------|
| S1 | W2-B8 하단 탭바 | 내비게이션 UX 개선, 데모 임팩트 큼 |
| S2 | W3-B10 저장 목록 페이지 | save 기능의 완성도 |
| S3 | W2-A6 Reranker | 피드 품질 향상 |
| S4 | W4-A1~A2 Top Pick | 결정 지원 핵심 |
| S5 | W4-A3~A4, W4-B2 A vs B 비교 | 결정 지원 차별화 |
| S6 | W4-A5, W4-B3 오늘의 컬러핏 | 재방문 유도 |
| S7 | W3-A6, W3-B9 톤 설명 페이지 | 교육 콘텐츠 |
| S8 | W2-A10 scoring 유닛 테스트 | 품질 보증 |
| S9 | W4-D2~D3, D5 추가 테스트 | E2E + 성능 |

### Phase 7: Could — 스코프 아웃 후보

- F-23 시즌 태그 필터
- F-29 추천 이유 3레이어 상세
- F-30 구매 후 피드백
- F-31 진단 결과 카드

---

### 스코프 컷 기준

| 상황 | 대응 |
|------|------|
| W2 끝까지 Phase 3 미완 | Phase 6 전체 DROP, 인증을 카카오 1개로 축소 |
| W3 끝까지 Phase 4 미완 | Phase 6 전체 DROP, E2E 테스트 수동으로 최소화 |
| W4 초반 Phase 5 진입 불가 | 게스트 모드만 유지, 소셜 로그인 DROP, 로컬 배포로 데모 |

---

## 변경 로그

| 날짜 | 태스크 | 변경 내용 |
|------|--------|----------|
| 2026-03-23 | — | TASK.md v1.0 초안 작성 |
| 2026-03-23 | W1-A1 | Git 초기화 + monorepo 구조 생성 완료. 상세기획서를 docs/로 이동 |
| 2026-03-23 | W1-A2 | Next.js 16 + React 19 + TS + Tailwind 4 + Zustand + React Query + Framer Motion 설치. TRD 디렉토리 구조 생성, types/index.ts, lib/api.ts, lib/store.ts, providers.tsx 작성 |
| 2026-03-23 | — | 우선순위 섹션 전면 재구성: Phase 1~7 실행 전략 + 병렬 트랙 + 스코프 컷 기준 추가. Redis/배포를 Phase 5로 이동, 결정 지원을 Should(Phase 6)로 하향 |

---

> **규칙:**
> 1. 태스크 시작 시 상태를 ⬜→🔄로 변경
> 2. 태스크 완료 시 상태를 🔄→✅로 변경 + 날짜 기록
> 3. 스코프 변경 시 변경 로그에 사유 기록
> 4. PRD/TRD에 영향을 주는 변경이 있으면 해당 문서도 즉시 업데이트
> 5. 매일 스탠드업 시 이 파일 기준으로 진행 상황 공유
