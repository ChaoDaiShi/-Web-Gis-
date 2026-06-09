@echo off
chcp 65001>nul
cd /d "frontend"
start /b npm run dev
timeout 2
start http://localhost:5173
pause