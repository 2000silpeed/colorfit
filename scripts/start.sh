#!/bin/bash
# ColorFit 백엔드 + 프론트엔드 시작
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== ColorFit 백엔드 시작 (port 8000) ==="
cd "$PROJECT_ROOT/backend"
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "백엔드 PID: $BACKEND_PID"

echo "=== ColorFit 프론트엔드 시작 (port 3000) ==="
cd "$PROJECT_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!
echo "프론트엔드 PID: $FRONTEND_PID"

echo ""
echo "백엔드:   http://localhost:8000"
echo "프론트엔드: http://localhost:3000"
echo ""
echo "종료: scripts/stop.sh"

wait
