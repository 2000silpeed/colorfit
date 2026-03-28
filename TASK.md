# ColorFit Task Tracker

**프로젝트 기간:** 5주 (W1: 3/24~3/28 ~ W5: 4/21~4/25)
**현재 상태:** W1 시작 전
**Fallback 기준:** W3 금요일에 가격비교 미완이면 Fallback 발동

---

## W1: 데이터 + 인프라 (3/24~3/28)

### Lane A: 데이터 파이프라인
- [ ] 12톤 팔레트 JSON 데이터 생성 (12톤 x 25색 = 300개 색상)
- [ ] 네이버 쇼핑 API 수집 스크립트 (`scripts/curate_by_tone.py`)
  - [ ] API 키 발급 + 연결 테스트
  - [ ] 톤별 키워드 리스트 설계
  - [ ] 4병렬 수집 로직 구현
  - [ ] 목표: 25,000개 상품 수집
- [ ] 전처리 파이프라인 (`scripts/rebuild_from_tones.py`)
  - [ ] HTML 태그 제거 + 상품명 정규화
  - [ ] 이미지 색상 추출 (K-means, PIL)
  - [ ] 12톤 매핑 (RGB 유클리드 거리)
  - [ ] 하이브리드 분류 (키워드 + LLM 폴백)
- [ ] 코디 조합 생성 (레시피 기반)
  - [ ] TPO x 무드 레시피 JSON 정의
  - [ ] 조합 알고리즘 구현
  - [ ] 목표: 1,500~1,900개 코디
- [ ] Gemini Flash 배치 평가 (`scripts/evaluate_outfits.py`)
  - [ ] 3점 미만 제거
- [ ] 브랜드 화이트리스트 JSON (120개+)

### Lane B: 인프라 셋업
- [ ] Git 초기화 + .gitignore
- [ ] Next.js 15 프로젝트 초기화 (`frontend/`)
  - [ ] TailwindCSS 4.0 설정
  - [ ] Framer Motion 설치
  - [ ] Nanum Myeongjo + Pretendard 폰트 로딩
  - [ ] 디자인 토큰 (CSS variables) 세팅
- [ ] FastAPI 프로젝트 초기화 (`backend/`)
  - [ ] Pydantic v2 + SQLAlchemy 2.0
  - [ ] 프로젝트 구조 (routers/, services/, models/, schemas/)
  - [ ] CORS 미들웨어 설정
- [ ] Supabase 프로젝트 생성 + DB 스키마 적용
  - [ ] users, products, outfits, reactions 테이블
  - [ ] style_seeds, user_preferences 테이블
  - [ ] 인덱스 (tone_id, designed_tpo, gender)
- [ ] Vercel 배포 설정 (프론트엔드)
- [ ] Railway 배포 설정 (백엔드)
- [ ] 환경변수 설정 (.env.example)

### W1 완료 기준
- [ ] 상품 DB 20,000건 이상
- [ ] 코디 1,500개 이상 (Gemini 평가 통과)
- [ ] 프론트/백엔드 빈 프로젝트 배포 성공

---

## W2: 추천 엔진 + 온보딩 (3/31~4/4)

### Lane C: 추천 엔진 코어
- [ ] `services/scoring.py` — 5축 스코어링
  - [ ] calculate_pcf() (톤 매칭 + RGB 거리)
  - [ ] calculate_of() (TPO 동의어 확장 + 매칭)
  - [ ] calculate_ch() (색상 거리 구간별)
  - [ ] calculate_pe() (예산 범위)
  - [ ] calculate_sf() (카테고리 궁합 + 실루엣 + 포멀도)
  - [ ] 테스트: 5축 각각 unit test
- [ ] `services/style_filter.py` — 규칙 기반 필터
  - [ ] detect_category() (키워드 → 캐시 → LLM)
  - [ ] category_score() (227개 매트릭스)
  - [ ] silhouette_score() (15개 규칙)
  - [ ] formality_score() (표준편차)
  - [ ] 55점 컷오프
  - [ ] 테스트: 경계값 + edge case
- [ ] `services/feed_builder.py` — 7단계 파이프라인
  - [ ] Hard Filter 체인 (H1~H8)
  - [ ] Soft Score 계산
  - [ ] 리랭킹 (완성도 가산 + dislike 제외 + 다양성)
  - [ ] 테스트: 통합 테스트 (정상 코디 통과, 부적합 코디 필터링)
- [ ] `services/reason_generator.py` — 추천 이유 2줄
  - [ ] 5축 가중 기여도 → 상위 2개 축 선택
  - [ ] high/mid 템플릿 분기 (75점 기준)
- [ ] `routers/feed.py` — GET /api/feed
- [ ] `routers/outfit.py` — GET /api/outfit/{id}
- [ ] 스코어 프리컴퓨팅 스크립트 (전체 코디 사전 스코어링)

### Lane D: 온보딩 + 피드 UI
- [ ] 온보딩 Step 1: 성별 선택
- [ ] 온보딩 Step 2: 퍼스널컬러 12톤 선택
- [ ] 온보딩 Step 3: TPO + 무드 선택 (성별별 분화)
- [ ] 온보딩 Step 4: 예산 설정 (듀얼 슬라이더)
- [ ] 온보딩 Step 5: 비주얼 취향 분석 (4라운드)
- [ ] POST /api/onboarding 연동
- [ ] 코디 피드 화면
  - [ ] TPO 탭 필터
  - [ ] 코디 카드 컴포넌트 (이미지 + 제목 + 가격 + 이유 + 뱃지)
  - [ ] 무한 스크롤 (커서 기반 페이지네이션)
  - [ ] save(더블탭 + 하트) / dislike(좌 스와이프)
  - [ ] "오늘의 컬러핏" 특별 카드
- [ ] 코디 상세 화면
  - [ ] 히어로 이미지 + parallax
  - [ ] 5축 스코어 바 차트 (애니메이션)
  - [ ] 추천 이유 카드
  - [ ] 아이템 캐러셀
- [ ] 하단 탭바 (홈/저장/Top/마이)
- [ ] 스켈레톤 로딩 + empty state + error state

### W2 완료 기준
- [ ] 5 Step 온보딩 → 코디 피드 진입 동작
- [ ] 스코어링 기반 피드가 실제 데이터로 동작
- [ ] save/dislike 동작
- [ ] 추천 이유 2줄 노출

---

## W3: 가격비교 + 유사상품 (4/7~4/11)

- [ ] `services/similar_finder.py` — 유사 상품 매칭
  - [ ] 색상 유사도 (0.6) + 가격 유사도 (0.4)
  - [ ] Exact / Similar 구분
- [ ] `routers/item.py` — GET /api/item/{id}, GET /api/item/{id}/similar
- [ ] 아이템 상세 화면
  - [ ] 가격 비교 테이블 (판매처별)
  - [ ] 최저가 강조
  - [ ] 유사 상품 그리드
- [ ] 외부 쇼핑몰 링크 (새 탭)
- [ ] 프로필/마이페이지
  - [ ] 톤 카드 + 대표색 스와치
  - [ ] 내 정보 변경 (해당 Step 바텀시트)
  - [ ] 취향 관리 (Style Seed 시각화)
- [ ] 톤 설명 화면
- [ ] **W3 금요일 Fallback 판단 시점**

### W3 완료 기준
- [ ] 가격 비교 테이블 동작
- [ ] Exact/Similar 구분 표시
- [ ] 외부 쇼핑몰 링크 동작
- [ ] 마이페이지 동작

---

## W4: 결정 지원 + 통합 (4/14~4/18)

- [ ] `services/top_pick.py` — Top Pick 선정
  - [ ] 저장 목록 기반 / 전체 DB 기반
  - [ ] 시간대 기반 One-shot 추천
- [ ] `services/comparator.py` — A vs B 비교
- [ ] `routers/top_pick.py`, `routers/compare.py`
- [ ] 저장 목록 화면
  - [ ] 그리드 + 정렬 (최근/점수/가격)
  - [ ] Top Pick 버튼 + 모달
- [ ] A vs B 비교 화면 (좌우 분할 + 레이더 차트)
- [ ] 로그인 화면 (카카오/구글/게스트)
  - [ ] `services/jwt.py` — 소셜 로그인
  - [ ] 게스트 → 로그인 전환 (저장/Top Pick 시)
- [ ] 구매 후 피드백 바텀시트
- [ ] `services/preference_tracker.py` — 피드백 개인화 학습
- [ ] 통합 테스트
  - [ ] 온보딩 → 피드 → 상세 → 가격비교 → 외부 링크 전체 플로우
  - [ ] 저장 → Top Pick 플로우
  - [ ] Edge case: 코디 0개, 예산 초과, 톤 불일치

### W4 완료 기준
- [ ] Top Pick 동작
- [ ] A vs B 비교 동작
- [ ] 소셜 로그인 동작
- [ ] 전체 플로우 통합 테스트 통과

---

## W5: 폴리싱 + 배포 (4/21~4/25)

- [ ] 반응형 QA (375px / 768px / 1280px)
- [ ] 다크모드 구현 + 테스트
- [ ] 성능 최적화
  - [ ] 이미지 lazy loading + CDN
  - [ ] 피드 API 응답 800ms 이내 확인
  - [ ] Lighthouse 성능 점수 확인
- [ ] 버그 수정
- [ ] 프로덕션 배포
- [ ] 데모 시나리오 준비
- [ ] 발표 자료 작성

### W5 완료 기준
- [ ] 프로덕션 URL 접속 가능
- [ ] 주요 플로우 버그 없음
- [ ] 데모 준비 완료

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
1. A vs B 비교
2. Top Pick + One-shot
3. 가격비교 (외부 링크만 유지)
4. 스코어링 5축 → 3축(PCF+OF+SF)

**절대 미루지 않는 것:** 온보딩 → 코디 피드 → 추천 이유 → save/dislike → 외부 링크
