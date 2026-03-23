# ColorFit TRD (Technical Requirements Document)

> **최종 수정:** 2026-03-23 | **상태:** Draft → 구현 중
> **관련 문서:** [PRD.md](./PRD.md) · [TASK.md](./TASK.md) · [ColorFit_상세기획서_v1.0.md](./docs/ColorFit_상세기획서_v1.0.md)

---

## 1. 기술 스택

### 1.1 전체 구성

```
┌─────────────────────────────────────────────┐
│  Frontend       Next.js 15 + React 19 + TS  │
│                 TailwindCSS 4 + Framer Motion│
├─────────────────────────────────────────────┤
│  Hosting        Vercel (FE) + Railway (BE)  │
├─────────────────────────────────────────────┤
│  Backend        Python 3.13 + FastAPI 0.115 │
│                 Pydantic v2 + SQLAlchemy 2.0 │
├─────────────────────────────────────────────┤
│  Data           PostgreSQL 17 + Redis 7.4   │
│                 Supabase (managed PG)        │
├─────────────────────────────────────────────┤
│  External       Naver Shopping API           │
│                 Kakao/Google OAuth            │
└─────────────────────────────────────────────┘
```

### 1.2 핵심 라이브러리

| 계층 | 라이브러리 | 버전 | 용도 |
|------|-----------|------|------|
| FE | next | 15.2 | SSR + App Router |
| FE | react | 19 | UI |
| FE | typescript | 5.6 | 타입 |
| FE | tailwindcss | 4.0 | 스타일링 |
| FE | framer-motion | 11 | 애니메이션 (스와이프 등) |
| FE | zustand | 5 | 클라이언트 상태 관리 |
| FE | @tanstack/react-query | 5 | 서버 상태 + 캐싱 |
| BE | fastapi | 0.115 | REST API |
| BE | pydantic | 2.10 | 스키마 검증 |
| BE | sqlalchemy | 2.0 | ORM |
| BE | httpx | 0.28 | 비동기 HTTP (외부 API) |
| BE | pillow | 11.1 | 이미지 색상 추출 |
| BE | numpy | 2.2 | 색상 거리 계산 |
| BE | scikit-learn | 1.6 | K-means 클러스터링 |
| BE | redis[hiredis] | 5.2 | 캐싱 클라이언트 |
| BE | python-jose | 3.3 | JWT 토큰 |

## 2. 시스템 아키텍처

### 2.1 4-Layer Architecture

```
┌──────────────────────────────────────────────────┐
│                   UI Layer                        │
│  Pages: 온보딩(3), 피드, 코디상세, 아이템상세,    │
│         저장목록, 비교, 마이페이지                  │
│  Components: OutfitCard, ToneSwatchGrid,          │
│              ScoreBadge, PriceTable, TPOTabs      │
└─────────────────────┬────────────────────────────┘
                      │ REST API (JSON)
┌─────────────────────┼────────────────────────────┐
│                 API Layer                          │
│  Routers: auth, onboarding, feed, outfit,         │
│           item, reaction, top_pick, compare        │
│  Middleware: CORS, Auth(JWT), RateLimit            │
└─────────────────────┬────────────────────────────┘
                      │
┌─────────────────────┼────────────────────────────┐
│          Recommendation Engine                     │
│  ColorMatcher → OutfitScorer → Reranker           │
│  → ReasonGenerator → SimilarFinder → TopPicker    │
└─────────────────────┬────────────────────────────┘
                      │
┌─────────────────────┼────────────────────────────┐
│                Data Layer                          │
│  PostgreSQL: users, products, outfits, reactions   │
│  Redis: feed_cache, session                        │
│  External: Naver Shopping API, OAuth providers     │
│  Static: 12-tone palette JSON                      │
└──────────────────────────────────────────────────┘
```

### 2.2 설계 원칙

| 원칙 | 규칙 |
|------|------|
| Speed First | 피드 로딩 ≤ 3초, TPO 전환 ≤ 500ms, 이미지 lazy+WebP |
| Explainability | 모든 추천에 reasons 2줄 필수 동반 |
| Modularity | 스코어링/필터/정렬/이유생성 각각 독립 모듈 |

## 3. 데이터 모델

### 3.1 DB 스키마

```sql
-- users
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255) UNIQUE,
    nickname      VARCHAR(50),
    provider      VARCHAR(20),       -- kakao | google | guest
    provider_id   VARCHAR(100),
    tone_id       VARCHAR(30),       -- e.g. summer_cool_soft
    tpo_list      TEXT[],            -- e.g. {office, date}
    style_moods   TEXT[],            -- e.g. {casual, minimal}
    budget_min    INT DEFAULT 30000,
    budget_max    INT DEFAULT 100000,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- products
CREATE TABLE products (
    id              VARCHAR(50) PRIMARY KEY,
    name            VARCHAR(500) NOT NULL,
    brand           VARCHAR(100),
    category        VARCHAR(20) NOT NULL,  -- top|bottom|outer|onepiece|shoes|bag|acc
    color_hex       VARCHAR(7),
    tone_id         VARCHAR(30),
    price           INT NOT NULL,
    mall_name       VARCHAR(50),
    mall_url        TEXT,
    image_url       TEXT,
    tags            TEXT[],
    last_observed_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_products_tone ON products(tone_id);
CREATE INDEX idx_products_category ON products(category);

-- outfits
CREATE TABLE outfits (
    id                  VARCHAR(50) PRIMARY KEY,
    item_ids            TEXT[] NOT NULL,
    total_price         INT,
    lowest_total_price  INT,
    is_complete_outfit  BOOLEAN DEFAULT false,
    tags                TEXT[],
    scores              JSONB,    -- {pcf, of, ch, pe, total}
    reasons             TEXT[],
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- reactions
CREATE TABLE reactions (
    id          SERIAL PRIMARY KEY,
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    outfit_id   VARCHAR(50) REFERENCES outfits(id),
    type        VARCHAR(15) NOT NULL,  -- save|dislike|click|view_reason|purchase_feedback
    metadata    JSONB,                 -- e.g. {feedback: "good", reason: "color"}
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_reactions_user ON reactions(user_id, type);
```

### 3.2 12-tone 팔레트 데이터 (static JSON)

```
data/palettes/
├── spring_warm_light.json
├── spring_warm_bright.json
├── spring_warm_mute.json
├── summer_cool_light.json
├── summer_cool_soft.json
├── summer_cool_mute.json
├── autumn_warm_deep.json
├── autumn_warm_mute.json
├── autumn_warm_bright.json
├── winter_cool_deep.json
├── winter_cool_bright.json
└── winter_cool_light.json
```

각 파일 구조:
```json
{
  "tone_id": "summer_cool_soft",
  "name_ko": "여름쿨소프트",
  "season": "summer",
  "temperature": "cool",
  "depth": "soft",
  "description": "차갑고 부드러운 색이 피부를 투명하게 만들어요",
  "palette": [
    {"hex": "#B0A6C6", "name": "라벤더"},
    {"hex": "#9FB5D4", "name": "파우더 블루"},
    {"hex": "#D4A5B0", "name": "소프트 핑크"}
  ],
  "recommended_colors": ["#B0A6C6", "#9FB5D4", "#C8BFD4"],
  "avoid_colors": ["#FF6B00", "#8B6914", "#556B2F"],
  "compatible_tones": ["summer_cool_light", "winter_cool_light"]
}
```

## 4. API 설계

### 4.1 엔드포인트

| Method | Path | 설명 | Auth | 캐시 |
|--------|------|------|------|------|
| POST | `/api/auth/kakao` | 카카오 로그인 | — | — |
| POST | `/api/auth/google` | 구글 로그인 | — | — |
| POST | `/api/auth/logout` | 로그아웃 | JWT | — |
| GET | `/api/auth/me` | 내 프로필 | JWT | — |
| POST | `/api/onboarding` | 온보딩 저장 | JWT/Guest | — |
| PATCH | `/api/onboarding` | 온보딩 수정 | JWT | — |
| GET | `/api/feed?tpo=office&page=1` | 코디 피드 | JWT/Guest | Redis 5분 |
| GET | `/api/outfit/{id}` | 코디 상세 | JWT/Guest | Redis 10분 |
| GET | `/api/item/{id}` | 아이템 상세 + 가격 | JWT/Guest | Redis 10분 |
| GET | `/api/item/{id}/similar` | 유사 상품 | JWT/Guest | Redis 30분 |
| POST | `/api/reaction` | save/dislike/view_reason | JWT | — |
| GET | `/api/saved` | 저장 목록 | JWT | — |
| GET | `/api/top-pick` | Top Pick 1개 | JWT | — |
| POST | `/api/compare` | A vs B 비교 | JWT | — |
| GET | `/api/tone/{tone_id}` | 톤 설명 | — | Static |

### 4.2 주요 응답 스키마

**GET /api/feed 응답:**
```json
{
  "outfits": [
    {
      "id": "outfit_001",
      "image_url": "https://cdn.colorfit.ai/...",
      "summary": "여름쿨소프트 데이트룩 — 라벤더 블라우스 + 아이보리 슬랙스",
      "total_price": 77900,
      "lowest_total_price": 71200,
      "scores": {
        "personal_color_fit": 94.2,
        "occasion_fit": 88.0,
        "total": 89.1
      },
      "reasons": [
        "여름쿨소프트 핵심 컬러 라벤더 계열로 피부톤이 밝아 보여요",
        "데이트 룩에 적합한 부드러운 실루엣 조합이에요"
      ],
      "is_complete_outfit": true,
      "item_count": 2,
      "is_saved": false
    }
  ],
  "total": 156,
  "page": 1,
  "has_next": true
}
```

**POST /api/reaction 요청:**
```json
{
  "outfit_id": "outfit_001",
  "type": "save"
}
```

## 5. 추천 엔진

### 5.1 파이프라인

```
Request → ProfileLoad → CandidateFilter → Scorer → Reranker → ReasonGen → Response
```

| 단계 | 입력 | 출력 | 상세 |
|------|------|------|------|
| ProfileLoad | user_id | UserProfile | DB에서 tone/tpo/budget/moods 로드 |
| CandidateFilter | 전체 outfits | 200~500 후보 | tone 범위 + tpo 태그 + 가격 범위 |
| Scorer | 후보 | 점수 부여 코디 | PCF×0.35 + OF×0.25 + CH×0.20 + PE×0.20 |
| Reranker | 점수 코디 | 정렬된 상위 50 | isComplete 가산 + dislike 제외 + 다양성 |
| ReasonGen | 상위 코디 | 코디+이유 | 상위 2개 기여 요인 → 자연어 템플릿 |

### 5.2 스코어링 상세

| 축 | 가중치 | 계산 방식 |
|---|--------|----------|
| personalColorFit (PCF) | 0.35 | 코디 아이템 tone vs 사용자 tone 유클리드 거리 → 0~100 |
| occasionFit (OF) | 0.25 | TPO 태그 매칭 비율 × 100 |
| colorHarmony (CH) | 0.20 | 아이템 간 색상 조화도 (60-30-10 법칙) |
| priceEfficiency (PE) | 0.20 | 예산 내 80~100, 초과 시 감점 |

### 5.3 유사 상품 매칭

- 입력: product_id
- 필터: 동일 category + tone 거리 ≤ 임계값
- 정렬: 색상 유사도 × 0.6 + 가격 유사도 × 0.4
- 출력: 상위 5개 + match_type (exact/similar) + 유사도 %

### 5.4 Top Pick / A vs B

- **Top Pick:** saved 코디 중 total_score max → 1개 + 강조 이유
- **A vs B:** 두 코디의 4축 점수 나란히 비교 → 가장 큰 차이 축 기반 판정

## 6. 프론트엔드 구조

### 6.1 디렉토리

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                  # 랜딩
│   ├── onboarding/
│   │   ├── step1/page.tsx        # 톤 선택
│   │   ├── step2/page.tsx        # TPO + 무드
│   │   └── step3/page.tsx        # 예산
│   ├── feed/page.tsx             # 코디 피드
│   ├── outfit/[id]/page.tsx      # 코디 상세
│   ├── item/[id]/page.tsx        # 아이템 상세
│   ├── saved/page.tsx            # 저장 목록
│   ├── compare/page.tsx          # A vs B
│   └── profile/page.tsx          # 마이페이지
├── components/
│   ├── OutfitCard.tsx
│   ├── ToneSwatchGrid.tsx
│   ├── ScoreBadge.tsx
│   ├── PriceCompareTable.tsx
│   ├── SimilarProductList.tsx
│   ├── TPOTabs.tsx
│   ├── BudgetSlider.tsx
│   ├── ReasonCard.tsx
│   └── CompareView.tsx
├── lib/
│   ├── api.ts                    # API client (fetch wrapper)
│   └── store.ts                  # Zustand store
├── hooks/
│   ├── useFeed.ts
│   ├── useOutfit.ts
│   └── useReaction.ts
└── types/
    └── index.ts
```

### 6.2 핵심 타입

```typescript
// types/index.ts

export interface UserProfile {
  id: string;
  toneId: string;
  tpoList: string[];
  styleMoods: string[];
  budgetMin: number;
  budgetMax: number;
}

export interface OutfitCard {
  id: string;
  imageUrl: string;
  summary: string;
  totalPrice: number;
  lowestTotalPrice: number;
  scores: {
    personalColorFit: number;
    occasionFit: number;
    total: number;
  };
  reasons: string[];
  isCompleteOutfit: boolean;
  itemCount: number;
  isSaved: boolean;
}

export interface ProductDetail {
  id: string;
  name: string;
  brand: string;
  category: string;
  colorHex: string;
  toneId: string;
  price: number;
  mallName: string;
  mallUrl: string;
  imageUrl: string;
}

export interface PriceEntry {
  mallName: string;
  price: number;
  url: string;
  matchType: 'exact' | 'similar';
  similarity?: number;
}

export interface CompareResult {
  comparison: Record<string, { A: number; B: number }>;
  winner: 'A' | 'B';
  reason: string;
}
```

## 7. 백엔드 구조

### 7.1 디렉토리

```
backend/
├── app/
│   ├── main.py                   # FastAPI app + CORS + middleware
│   ├── config.py                 # 환경 변수
│   ├── routers/
│   │   ├── auth.py               # 소셜 로그인
│   │   ├── onboarding.py         # 프로필 저장/수정
│   │   ├── feed.py               # 코디 피드
│   │   ├── outfit.py             # 코디 상세
│   │   ├── item.py               # 아이템 상세 + 가격 + 유사
│   │   ├── reaction.py           # save/dislike/view_reason
│   │   ├── top_pick.py           # Top Pick + One-shot
│   │   └── compare.py            # A vs B
│   ├── services/
│   │   ├── scoring.py            # OutfitScorer
│   │   ├── color_matcher.py      # 색상→톤 매핑
│   │   ├── similar_finder.py     # 유사 상품 검색
│   │   ├── reason_generator.py   # 추천 이유 생성
│   │   ├── top_pick.py           # Top Pick 선정
│   │   └── feed_builder.py       # 피드 조합 (필터+스코어+리랭크)
│   ├── models/                   # SQLAlchemy models
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── outfit.py
│   │   └── reaction.py
│   ├── schemas/                  # Pydantic schemas
│   │   ├── user.py
│   │   ├── outfit.py
│   │   ├── item.py
│   │   └── reaction.py
│   └── db/
│       ├── database.py           # DB 연결
│       └── palettes.py           # 12-tone 팔레트 로더
├── scripts/
│   ├── collect_naver.py          # 네이버 쇼핑 수집
│   ├── crawl_musinsa.py          # 무신사 크롤링
│   ├── preprocess.py             # 전처리 + 색상 추출
│   ├── generate_outfits.py       # 코디 조합 생성
│   └── seed_data.py              # 시드 데이터 삽입
├── data/
│   └── palettes/                 # 12-tone JSON 파일들
├── tests/
│   ├── test_scoring.py
│   ├── test_color_matcher.py
│   └── test_feed.py
├── requirements.txt
└── Dockerfile
```

## 8. 인프라 & 배포

### 8.1 환경 구성

| 환경 | 프론트엔드 | 백엔드 | DB |
|------|-----------|--------|-----|
| Local | `next dev` (3000) | `uvicorn` (8000) | Docker PG + Redis |
| Staging | Vercel Preview | Railway Dev | Supabase Dev |
| Production | Vercel Prod | Railway Prod | Supabase Prod |

### 8.2 비용 예상 (월)

| 서비스 | 플랜 | 비용 |
|--------|------|------|
| Vercel | Free / Pro | $0~$20 |
| Railway | Starter | $5~$10 |
| Supabase | Free | $0 |
| Upstash Redis | Free | $0 |
| Cloudflare Images | Free | $0 |
| **합계** | | **$5~$30** |

### 8.3 CI/CD

- **프론트:** Vercel Git Integration (push → auto deploy)
- **백엔드:** Railway Git Integration (push → auto deploy)
- **DB 마이그레이션:** Alembic (수동 실행, W1에 초기 스키마)

## 9. 데이터 수집 파이프라인

### 9.1 수집 전략

| 소스 | 방법 | 규모 | 일정 |
|------|------|------|------|
| 네이버 쇼핑 API | REST API 호출 | 20,000 상품 | W1 (3일) |
| 무신사 | 정적 크롤링 | 5,000 상품 | W1 (2일) |
| 12-tone 팔레트 | 수동 구축 | 12톤 × 20~30색 | W1 (0.5일) |
| 코디 조합 | 자동 생성 스크립트 | 800~1,500 코디 | W1 (1일) |

### 9.2 전처리 흐름

```
Raw Product → HTML 태그 제거 → 브랜드/카테고리 정규화
  → 이미지 색상 추출 (K-means top 3) → 색상 → 톤 매핑
  → TPO/시즌 태그 자동 부여 → DB 저장
```

## 10. 테스트 전략

| 레벨 | 대상 | 도구 | 기준 |
|------|------|------|------|
| Unit | scoring, color_matcher, reason_generator | pytest | 핵심 모듈 커버리지 ≥ 80% |
| API | 각 엔드포인트 정상/에러 응답 | pytest + httpx | 전체 엔드포인트 통과 |
| E2E | 온보딩→피드→상세→외부링크 플로우 | 수동 테스트 | 핵심 시나리오 3개 통과 |
| Performance | 피드 로딩 시간 | Lighthouse | LCP ≤ 3초 |

---

> **변경 이력**
> | 날짜 | 변경 내용 | 작성자 |
> |------|----------|--------|
> | 2026-03-23 | v1.0 초안 작성 | — |
