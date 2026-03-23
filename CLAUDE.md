# CLAUDE.md

## Key Documents (항상 최신 유지)

- `TASK.md` — **구현의 Single Source of Truth**. 태스크 시작(⬜→🔄), 완료(🔄→✅) 즉시 반영
- `PRD.md` — 제품 요구사항. 기능 수락 기준, KPI, 릴리스 체크리스트
- `TRD.md` — 기술 설계. 아키텍처, DB 스키마, API 설계, FE/BE 디렉토리 구조
- `docs/ColorFit_상세기획서_v1.0.md` — 전체 기획서 (참조용, 페르소나/시나리오/스코어링 알고리즘 상세)

**규칙:** 코드 변경 시 TASK.md 상태를 반드시 업데이트. PRD/TRD에 영향을 주는 변경은 해당 문서도 함께 수정.

## Architecture (계획)

```
Frontend (Next.js 15 + React 19 + TS + TailwindCSS 4)
    ↕ REST API (JSON)
Backend (Python 3.13 + FastAPI 0.115 + Pydantic v2)
    ↕
Recommendation Engine (ColorMatcher → OutfitScorer → Reranker → ReasonGenerator)
    ↕
Data (PostgreSQL 17 + Redis 7.4 + Naver Shopping API + 12-tone Palette JSON)
```

프론트: `frontend/` (App Router), 백엔드: `backend/` (FastAPI)

## Commands

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (W1-A2 이후)
cd frontend
npm install
npm run dev
```

## Tech Stack

- **FE:** Next.js 15, React 19, TypeScript 5.6, TailwindCSS 4, Framer Motion 11, Zustand 5, @tanstack/react-query 5
- **BE:** Python 3.13, FastAPI 0.115, SQLAlchemy 2.0, Pydantic v2, httpx 0.28, Pillow 11, NumPy 2.2, scikit-learn 1.6
- **DB:** PostgreSQL 17 (Supabase), Redis 7.4 (Upstash)
- **Deploy:** Vercel (FE) + Railway (BE)

## Core Domain Concepts

- **12-tone:** 봄/여름/가을/겨울 × 라이트/뮤트/딥 등 12종 퍼스널컬러 분류
- **스코어링 4축:** personalColorFit(0.35) + occasionFit(0.25) + colorHarmony(0.20) + priceEfficiency(0.20)
- **추천 이유(reasons):** 상위 2개 기여 요인을 자연어 템플릿으로 변환하여 항상 동반
- **Exact/Similar:** 동일 상품 다른 판매처(Exact) vs 유사 색상·카테고리 대체재(Similar)

## Coding Conventions

- 한국어로 대화
- 함수/변수: camelCase (JS/TS), snake_case (Python)
- 컴포넌트: PascalCase
- 들여쓰기: 2 spaces (JS/TS), 4 spaces (Python)
- 불필요한 주석 금지
- 명시적 요청 없이 git commit/push 금지
- .env 파일이나 민감 정보 커밋 금지
- 테스트는 가상환경 하에서 진행
