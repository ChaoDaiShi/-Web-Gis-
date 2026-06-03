# -*- coding: utf-8 -*-
"""
校园失物招领系统 - 初始化脚本
用于Gitee下载后第一次部署时的数据库初始化

使用方法:
    python main.py [options]
    
    options:
        -h, --help          显示帮助信息
        -a, --all           执行所有初始化（默认）
        -d, --database      只创建数据库和基础表
        -t, --tables        只创建数据表
        -i, --initial       只插入初始数据
        -c, --check         检查数据库连接
"""

import argparse
import pymysql
from config import DB_CONFIG

def check_database_connection():
    """检查数据库连接"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        conn.close()
        print("✓ 数据库连接成功")
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        print("\n请确保:")
        print("  1. MySQL服务已启动")
        print("  2. 数据库 'compus' 已创建")
        print("  3. 用户名和密码正确")
        return False

def create_database():
    """创建数据库（如果不存在）"""
    try:
        # 不指定数据库连接
        config = DB_CONFIG.copy()
        del config['database']
        
        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} DEFAULT CHARACTER SET utf8mb4")
        conn.close()
        print(f"✓ 数据库 '{DB_CONFIG['database']}' 创建/检查成功")
        return True
    except Exception as e:
        print(f"✗ 创建数据库失败: {e}")
        return False

def run_sql_script(script_name, description):
    """运行指定的初始化脚本"""
    try:
        exec(f"from {script_name} import main")
        print(f"\n{'='*60}")
        print(f"正在{description}...")
        print('='*60)
        exec(f"main()")
        print(f"\n✓ {description}完成")
        return True
    except ImportError as e:
        print(f"✗ 导入脚本失败: {script_name} - {e}")
        return False
    except Exception as e:
        print(f"✗ {description}失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='校园失物招领系统初始化脚本')
    parser.add_argument('-a', '--all', action='store_true', default=True, help='执行所有初始化（默认）')
    parser.add_argument('-d', '--database', action='store_true', help='只创建数据库')
    parser.add_argument('-t', '--tables', action='store_true', help='只创建数据表')
    parser.add_argument('-i', '--initial', action='store_true', help='只插入初始数据')
    parser.add_argument('-c', '--check', action='store_true', help='检查数据库连接')
    
    args = parser.parse_args()
    
    print('='*60)
    print('校园失物招领系统 - 数据库初始化工具')
    print('='*60)
    print(f"\n目标数据库: {DB_CONFIG['database']}")
    print(f"数据库用户: {DB_CONFIG['user']}")
    print(f"数据库主机: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print()
    
    # 检查连接
    if not check_database_connection():
        return
    
    # 如果只检查连接
    if args.check:
        print("\n✓ 数据库连接正常，初始化脚本可以运行")
        return
    
    # 创建数据库
    if args.all or args.database:
        create_database()
    
    # 创建数据表
    if args.all or args.tables:
        scripts = [
            ('init_tables', '创建数据表'),
        ]
        for script, desc in scripts:
            run_sql_script(script, desc)
    
    # 插入初始数据
    if args.all or args.initial:
        scripts = [
            ('init_data', '插入初始数据'),
        ]
        for script, desc in scripts:
            run_sql_script(script, desc)
    
    print('\n' + '='*60)
    print('初始化完成！')
    print('='*60)
    print('\n下一步操作:')
    print('  1. 启动后端服务: cd .. && python Start.py')
    print('  2. 启动前端服务: cd 前端/lost-found && npm run dev')
    print('  3. 访问首页: http://localhost:5173')
    print('\n默认管理员账号:')
    print('  用户名: admin')
    print('  密码: admin')

if __name__ == '__main__':
    main()
