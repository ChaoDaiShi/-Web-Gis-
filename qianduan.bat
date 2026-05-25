@echo off
chcp 65001>nul
cd /d "前端\lost-found"
start /b npm run dev
timeout 2
start http://localhost:5173
pause