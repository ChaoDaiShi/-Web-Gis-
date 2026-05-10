#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校园失物招领系统 - 环境诊断脚本
用于检测和诊断后端服务启动问题
"""

import sys
import os
import socket
import subprocess
from pathlib import Path

# 设置标准输出编码
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("校园失物招领系统 - 环境诊断工具")
print("=" * 60)
print()

# 1. 检查Python版本
print("【1】检查Python环境...")
print(f"Python版本: {sys.version}")
print(f"Python路径: {sys.executable}")
print()

# 2. 检查依赖库
print("【2】检查依赖库安装情况...")
required_packages = {
    'flask': 'Flask',
    'flask_sqlalchemy': 'Flask-SQLAlchemy',
    'flask_cors': 'Flask-CORS',
    'pymysql': 'PyMySQL',
    'werkzeug': 'Werkzeug',
    'requests': 'requests'
}

missing_packages = []
for module_name, package_name in required_packages.items():
    try:
        __import__(module_name)
        print(f"[OK] {package_name} 已安装")
    except ImportError:
        print(f"[FAIL] {package_name} 未安装")
        missing_packages.append(package_name)

if missing_packages:
    print(f"\n警告: 缺少以下依赖库: {', '.join(missing_packages)}")
    print("请运行: pip install -r requirements.txt")
else:
    print("\n[OK] 所有依赖库已正确安装")
print()

# 3. 检查数据库连接
print("【3】检查数据库连接...")
try:
    import pymysql
    
    DB_CONFIG = {
        "host": "localhost",
        "user": "mapuser",
        "password": "123456",
        "database": "compus",
        "charset": "utf8mb4"
    }
    
    print(f"数据库主机: {DB_CONFIG['host']}")
    print(f"数据库用户: {DB_CONFIG['user']}")
    print(f"数据库名称: {DB_CONFIG['database']}")
    
    try:
        conn = pymysql.connect(**DB_CONFIG, connect_timeout=5)
        print("[OK] 数据库连接成功")
        
        # 检查表是否存在
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"[OK] 数据库中有 {len(tables)} 个表")
        
        # 检查user表
        cursor.execute("SHOW TABLES LIKE 'user'")
        if cursor.fetchone():
            print("[OK] user表存在")
            cursor.execute("SELECT COUNT(*) FROM user")
            count = cursor.fetchone()[0]
            print(f"  - user表中有 {count} 条记录")
        else:
            print("[FAIL] user表不存在，请先创建用户表")
        
        cursor.close()
        conn.close()
        
    except pymysql.err.OperationalError as e:
        error_code = e.args[0]
        if error_code == 1045:
            print("[FAIL] 数据库认证失败: 用户名或密码错误")
            print(f"  当前配置: 用户={DB_CONFIG['user']}, 密码={DB_CONFIG['password']}")
        elif error_code == 2003:
            print("[FAIL] 无法连接到MySQL服务器")
            print("  请检查MySQL服务是否已启动")
        elif error_code == 1049:
            print(f"[FAIL] 数据库 '{DB_CONFIG['database']}' 不存在")
            print("  请先创建数据库: CREATE DATABASE compus;")
        else:
            print(f"[FAIL] 数据库连接失败: {e}")
    except Exception as e:
        print(f"[FAIL] 数据库连接异常: {e}")
        
except ImportError:
    print("[FAIL] PyMySQL未安装，无法检查数据库连接")
print()

# 4. 检查端口占用
print("【4】检查端口占用情况...")
def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        result = sock.connect_ex(('127.0.0.1', port))
        if result == 0:
            print(f"[OK] 端口 {port} 已被占用")
            try:
                # 尝试访问服务
                import requests
                response = requests.get(f'http://127.0.0.1:{port}/', timeout=2)
                print(f"  - 服务响应状态: {response.status_code}")
            except:
                print("  - 无法获取服务状态")
            return True
        else:
            print(f"[FAIL] 端口 {port} 未被占用")
            return False
    finally:
        sock.close()

port_5000_used = check_port(5000)
print()

# 5. 检查后端服务文件
print("【5】检查后端服务文件...")
backend_files = [
    'Start.py',
    'DenluZhuChe.py',
    'map_service.py',
    'message_service.py',
    'requirements.txt'
]

for file_name in backend_files:
    if os.path.exists(file_name):
        print(f"[OK] {file_name} 存在")
    else:
        print(f"[FAIL] {file_name} 不存在")
print()

# 6. 诊断结果和建议
print("=" * 60)
print("诊断结果和建议")
print("=" * 60)

issues = []

if missing_packages:
    issues.append("依赖库未完全安装")

try:
    conn = pymysql.connect(**DB_CONFIG, connect_timeout=5)
    conn.close()
except:
    issues.append("数据库连接失败")

if not port_5000_used:
    issues.append("后端服务未启动")

if issues:
    print("\n发现以下问题:")
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue}")
    
    print("\n解决步骤:")
    
    if "依赖库未完全安装" in issues:
        print("\n【解决依赖问题】")
        print("运行以下命令安装依赖:")
        print("  pip install -r requirements.txt")
        print("或使用国内镜像:")
        print("  pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/")
    
    if "数据库连接失败" in issues:
        print("\n【解决数据库问题】")
        print("1. 确保MySQL服务已启动")
        print("2. 创建数据库:")
        print("   CREATE DATABASE compus CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print("3. 创建用户并授权:")
        print("   CREATE USER 'mapuser'@'localhost' IDENTIFIED BY '123456';")
        print("   GRANT ALL PRIVILEGES ON compus.* TO 'mapuser'@'localhost';")
        print("   FLUSH PRIVILEGES;")
    
    if "后端服务未启动" in issues:
        print("\n【启动后端服务】")
        print("运行以下命令启动服务:")
        print("  python Start.py")
else:
    print("\n[OK] 未发现明显问题")
    print("\n如果仍然无法登录，请检查:")
    print("1. 浏览器控制台的详细错误信息")
    print("2. 后端服务的日志输出")
    print("3. 防火墙或安全软件是否阻止了连接")

print("\n" + "=" * 60)
input("\n按回车键退出...")