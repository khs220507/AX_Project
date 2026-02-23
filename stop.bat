@echo off
chcp 65001 >nul 2>&1
title AX Project Stop

echo ============================================
echo   서버 종료 중...
echo ============================================
echo.

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8002.*LISTENING" 2^>nul') do (
    echo 백엔드 프로세스 종료 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING" 2^>nul') do (
    echo 프론트엔드 프로세스 종료 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3001.*LISTENING" 2^>nul') do (
    echo 프론트엔드 프로세스 종료 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo 모든 서버가 종료되었습니다.
pause
