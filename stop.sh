#!/bin/bash
echo "서버 종료 중..."
cmd.exe /c "for /f \"tokens=5\" %a in ('netstat -ano ^| findstr \":8002.*LISTENING\"') do taskkill /F /PID %a" 2>/dev/null
cmd.exe /c "for /f \"tokens=5\" %a in ('netstat -ano ^| findstr \":3000.*LISTENING\"') do taskkill /F /PID %a" 2>/dev/null
cmd.exe /c "for /f \"tokens=5\" %a in ('netstat -ano ^| findstr \":3001.*LISTENING\"') do taskkill /F /PID %a" 2>/dev/null
echo "완료."
