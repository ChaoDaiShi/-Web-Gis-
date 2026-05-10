@echo off
echo ============================================
echo 校园失物招领系统 - 后端依赖一键安装脚本
echo ============================================
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未检测到Python环境，请先安装Python
    echo 建议安装Python 3.8或更高版本
    pause
    exit /b 1
)

echo 检测到Python环境，开始安装依赖...
echo.

echo 1. 使用pip安装依赖库...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo 警告: 依赖安装过程中出现错误
    echo 尝试使用国内镜像源安装...
    echo.
    
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
    
    if %errorlevel% neq 0 (
        echo.
        echo 错误: 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
)

echo.
echo 2. 验证安装结果...
python -c "import flask; import flask_sqlalchemy; import flask_cors; import pymysql; import requests; print('✓ 所有依赖库安装成功！')"

if %errorlevel% neq 0 (
    echo.
    echo 警告: 部分依赖库可能未正确安装
    echo 请手动检查安装情况
)

echo.
echo 3. 安装完成！
echo.
echo 下一步操作：
echo 1. 确保MySQL数据库已启动并创建compus数据库
echo 2. 运行 python init_messages.py 初始化数据库表
echo 3. 运行 python Start.py 启动后端服务
echo.
echo ============================================
pause