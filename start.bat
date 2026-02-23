@echo off
chcp 65001 >nul 2>&1
title AX Project Launcher

echo ============================================
echo   소상공인 AI 상권분석 플랫폼 실행
echo ============================================
echo.

:: 기존 프로세스 종료
echo [1/4] 기존 프로세스 종료 중...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8002.*LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3001.*LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo   완료

:: 백엔드 실행
echo [2/4] 백엔드 서버 시작 (port 8002)...
cd /d "%~dp0backend"
start "AX-Backend" cmd /k "call venv\Scripts\activate && uvicorn main:app --host 127.0.0.1 --port 8002 --reload"

:: 백엔드 대기
echo [3/4] 백엔드 준비 대기 중...
:wait_backend
timeout /t 3 /nobreak >nul
curl -s http://localhost:8002/ >nul 2>&1
if errorlevel 1 (
    echo   아직 로딩 중...
    goto wait_backend
)
echo   백엔드 준비 완료

:: 프론트엔드 실행
echo [4/4] 프론트엔드 서버 시작 (port 3000)...
cd /d "%~dp0frontend"
start "AX-Frontend" cmd /k "npx vite --host 127.0.0.1"
timeout /t 3 /nobreak >nul

echo.
echo ============================================
echo   실행 완료!
echo   프론트엔드: http://localhost:3000
echo   백엔드:     http://localhost:8002
echo   API 문서:   http://localhost:8002/docs
echo   ML 상태:    http://localhost:8002/api/admin/ml/status
echo ============================================
echo.
echo 브라우저를 열고 있습니다...
start http://localhost:3000
echo.
pause
