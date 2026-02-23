#!/bin/bash
# Windows 경로 변환
if [[ "$PWD" == /mnt/* ]]; then
    WIN_DIR="$(echo "$PWD" | sed 's|/mnt/c|C:|' | sed 's|/|\\|g')"
    IS_WSL=true
else
    WIN_DIR="$(cd "$(dirname "$0")" && pwd)"
    IS_WSL=false
fi

PROJECT="C:\\Workspace\\AX_Project"

echo "============================================"
echo "  소상공인 AI 상권분석 플랫폼 실행"
echo "============================================"
echo ""

echo "[1/4] 기존 프로세스 종료 중..."
cmd.exe /c "for /f \"tokens=5\" %a in ('netstat -ano ^| findstr \":8002.*LISTENING\"') do taskkill /F /PID %a" 2>/dev/null
cmd.exe /c "for /f \"tokens=5\" %a in ('netstat -ano ^| findstr \":3000.*LISTENING\"') do taskkill /F /PID %a" 2>/dev/null
cmd.exe /c "for /f \"tokens=5\" %a in ('netstat -ano ^| findstr \":3001.*LISTENING\"') do taskkill /F /PID %a" 2>/dev/null
sleep 2
echo "  완료"

echo "[2/4] 백엔드 서버 시작 (port 8002)..."
cmd.exe /c "start \"AX-Backend\" cmd /k \"cd /d ${PROJECT}\\backend && venv\\Scripts\\activate && uvicorn main:app --host 127.0.0.1 --port 8002 --reload\"" &

echo "[3/4] 백엔드 준비 대기 중..."
while ! curl -s http://localhost:8002/ >/dev/null 2>&1; do
    echo "  로딩 중..."
    sleep 5
done
echo "  백엔드 준비 완료"

echo "[4/4] 프론트엔드 서버 시작 (port 3000)..."
cmd.exe /c "start \"AX-Frontend\" cmd /k \"cd /d ${PROJECT}\\frontend && npx vite --host 127.0.0.1\"" &
sleep 3

echo ""
echo "============================================"
echo "  실행 완료!"
echo "  프론트엔드: http://localhost:3000"
echo "  백엔드:     http://localhost:8002"
echo "  API 문서:   http://localhost:8002/docs"
echo "  ML 상태:    http://localhost:8002/api/admin/ml/status"
echo "============================================"
