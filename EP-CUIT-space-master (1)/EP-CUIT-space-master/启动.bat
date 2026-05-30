@echo off
chcp 65001>nul
echo 正在启动前后端服务...

:: 启动 后端.bat（后台运行，不卡主窗口）
start  "后端服务" cmd /k "houduan.bat"

:: 启动 前端.bat（后台运行，不卡主窗口）
start  "前端服务" cmd /k "qianduan.bat"

echo 启动完成！
exit