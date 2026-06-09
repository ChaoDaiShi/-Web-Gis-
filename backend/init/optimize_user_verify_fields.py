# -*- coding: utf-8 -*-
"""
数据库优化迁移脚本 - 问题4：删除 user_verify 冗余联系信息字段
1. 删除 user_verify 表中的 phone, email 列
2. 联系方式通过 user_id 关联 user 表获取
"""

import pymysql
from config import DB_CONFIG


def drop_column_if_exists(cursor, conn, table, column):
    """如果列存在则删除"""
    try:
        cursor.execute(f"SHOW COLUMNS FROM {table} LIKE '{column}'")
        if cursor.fetchone():
            cursor.execute(f"ALTER TABLE {table} DROP COLUMN {column}")
            conn.commit()
            print(f"  ✓ 已删除 {table}.{column}")
        else:
            print(f"  - {table}.{column} 不存在，跳过")
    except Exception as e:
        print(f"  ✗ 删除 {table}.{column} 失败: {e}")


def main():
    print("=" * 50)
    print("数据库优化迁移 - 问题4：user_verify 冗余字段清理")
    print("=" * 50)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("\n[步骤] 删除 user_verify.phone 和 user_verify.email...")
        drop_column_if_exists(cursor, conn, 'user_verify', 'phone')
        drop_column_if_exists(cursor, conn, 'user_verify', 'email')
        
        print("\n" + "=" * 50)
        print("清理完成！user_verify 的联系方式现在通过 user 表获取。")
        
    except Exception as e:
        print(f"\n✗ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        print("\n迁移脚本执行完毕。")


if __name__ == '__main__':
    main()
