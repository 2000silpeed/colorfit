# ColorFit

AI 퍼스널컬러 기반 패션 의사결정 엔진

## 기술 스택

- **Frontend:** Next.js 15 + React 19 + TypeScript + TailwindCSS
- **Backend:** Python 3.13 + FastAPI 0.115 + SQLAlchemy 2.0
- **DB:** PostgreSQL 17 (Supabase)

## 실행 방법

### 전체 시작 (백엔드 + 프론트엔드)

```bash
bash scripts/start.sh
```

- 백엔드: http://localhost:8000
- 프론트엔드: http://localhost:3000

### 종료

```bash
bash scripts/stop.sh
```

### 개별 실행

**백엔드:**

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**프론트엔드:**

```bash
cd frontend
npm run dev
```
