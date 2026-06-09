# -*- coding: utf-8 -*-
"""
数据库优化迁移脚本 - 问题3：清理校区ID双重存储
1. 删除 lost_item 表中的 campus_id 直接列（已用 item_campus 关联表替代）
2. 删除 repair 表中的 campus_id 直接列（已用 repair_campus 关联表替代）
注意：运行前请确保 add_campus_to_items.py 已将数据迁移到关联表
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
    print("数据库优化迁移 - 问题3：校区ID双重存储清理")
    print("=" * 50)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("\n[步骤1] 删除 lost_item.campus_id...")
        drop_column_if_exists(cursor, conn, 'lost_item', 'campus_id')
        
        print("\n[步骤2] 删除 repair.campus_id...")
        drop_column_if_exists(cursor, conn, 'repair', 'campus_id')
        
        print("\n" + "=" * 50)
        print("清理完成！campus_id 列已移除，统一使用 item_campus/repair_campus 关联表。")
        
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
