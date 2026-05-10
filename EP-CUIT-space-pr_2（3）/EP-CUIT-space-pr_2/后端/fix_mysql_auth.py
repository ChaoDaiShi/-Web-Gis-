#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复MySQL用户认证问题
MySQL 8.0+ 默认使用 caching_sha2_password 认证方式
需要修改为 mysql_native_password
"""

import subprocess
import sys

print("=" * 60)
print("修复MySQL用户认证问题")
print("=" * 60)
print()

# 尝试找到MySQL安装路径
mysql_paths = [
    "C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin\\mysql.exe",
    "C:\\Program Files\\MySQL\\MySQL Server 9.0\\bin\\mysql.exe",
    "C:\\Program Files (x86)\\MySQL\\MySQL Server 8.0\\bin\\mysql.exe",
    "C:\\ProgramData\\MySQL\\MySQL Server 8.0\\bin\\mysql.exe",
]

mysql_path = None
for path in mysql_paths:
    if subprocess.run(["where", path], capture_output=True).returncode == 0:
        mysql_path = path
        break

if not mysql_path:
    print("未找到MySQL客户端路径，请手动执行以下SQL语句:")
    print()
    print("1. 打开MySQL命令行客户端")
    print("2. 执行以下命令:")
    print("   ALTER USER 'mapuser'@'localhost' IDENTIFIED WITH mysql_native_password BY '123456';")
    print("   FLUSH PRIVILEGES;")
    print()
    print("3. 然后重启后端服务")
    input("\n按回车键退出...")
    sys.exit()

print(f"找到MySQL客户端: {mysql_path}")
print()

# 提示输入root密码
root_password = input("请输入MySQL root密码（直接回车表示无密码）: ").strip()

# 构建SQL命令
sql_commands = [
    "ALTER USER 'mapuser'@'localhost' IDENTIFIED WITH mysql_native_password BY '123456';",
    "FLUSH PRIVILEGES;"
]

# 执行SQL命令
print("\n正在修复用户认证...")
for sql in sql_commands:
    if root_password:
        result = subprocess.run(
            [mysql_path, "-u", "root", f"-p{root_password}", "-e", sql],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
    else:
        result = subprocess.run(
            [mysql_path, "-u", "root", "-e", sql],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
    
    if result.returncode == 0:
        print(f"  [OK] 执行成功: {sql.strip()}")
    else:
        print(f"  [FAIL] 执行失败: {sql.strip()}")
        print(f"        错误信息: {result.stderr}")

print()
print("=" * 60)
print("修复完成！")
print("=" * 60)
print("\n请重启后端服务测试连接:")
print("  python Start.py")
print()
input("按回车键退出...")