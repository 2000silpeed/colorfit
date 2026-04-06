#!/bin/bash
# ColorFit 백엔드 + 프론트엔드 종료
set -e

echo "=== ColorFit 프로세스 종료 ==="

# 백엔드 (uvicorn)
BACKEND_PIDS=$(lsof -ti :8000 2>/dev/null || true)
if [ -n "$BACKEND_PIDS" ]; then
    echo "백엔드 종료 (port 8000): PID $BACKEND_PIDS"
    echo "$BACKEND_PIDS" | xargs kill 2>/dev/null || true
else
    echo "백엔드: 실행 중이 아님"
fi

# 프론트엔드 (next dev)
FRONTEND_PIDS=$(lsof -ti :3000 2>/dev/null || true)
if [ -n "$FRONTEND_PIDS" ]; then
    echo "프론트엔드 종료 (port 3000): PID $FRONTEND_PIDS"
    echo "$FRONTEND_PIDS" | xargs kill 2>/dev/null || true
else
    echo "프론트엔드: 실행 중이 아님"
fi

echo "완료"
