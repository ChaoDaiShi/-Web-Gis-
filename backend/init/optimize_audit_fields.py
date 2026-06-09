# -*- coding: utf-8 -*-
"""
数据库优化迁移脚本 - 问题1：清理审核字段冗余
1. 删除 lost_item 表中的 audit_time, audit_remark, audit_by 冗余列
2. 删除 claim_form 表中的 audit_time, audit_remark 冗余列
3. 删除未使用的 temp_admin_requests 表
4. 确保现有 lost_item 审核数据已迁移到 audit 统一表
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


def migr_lost_item_audit_to_unified(cursor, conn):
    """将 lost_item 中的审核数据迁移到 audit 统一表（如果还没有的话）"""
    print("\n正在检查 lost_item 审核数据...")
    try:
        # 检查 lost_item 是否有 audit_status 列
        cursor.execute("SHOW COLUMNS FROM lost_item LIKE 'audit_status'")
        if not cursor.fetchone():
            print("  - lost_item 无 audit_status 列，跳过")
            return

        # 查找有审核状态但 audit 表中没有对应记录的物品
        cursor.execute("""
            SELECT li.item_id, li.publisher_id, li.audit_status, li.create_time
            FROM lost_item li
            LEFT JOIN audit a ON a.target_type = 'lost_item' AND a.target_id = li.item_id
            WHERE a.audit_id IS NULL
        """)
        missing = cursor.fetchall()
        
        if missing:
            for row in missing:
                item_id, publisher_id, status, create_time = row
                cursor.execute("""
                    INSERT IGNORE INTO audit (target_type, target_id, requester_id, status, create_time, update_time)
                    VALUES ('lost_item', %s, %s, %s, %s, NOW())
                """, (item_id, publisher_id, status or 'pending', create_time))
            conn.commit()
            print(f"  ✓ 已补迁移 {len(missing)} 条 lost_item 审核记录到 audit 表")
        else:
            print("  ✓ lost_item 审核数据已全部同步到 audit 表")
    except Exception as e:
        print(f"  ✗ 迁移失败: {e}")
        conn.rollback()


def drop_table_if_exists(cursor, conn, table):
    """如果表存在则删除"""
    try:
        cursor.execute(f"SHOW TABLES LIKE '{table}'")
        if cursor.fetchone():
            cursor.execute(f"DROP TABLE {table}")
            conn.commit()
            print(f"  ✓ 已删除表 {table}")
        else:
            print(f"  - 表 {table} 不存在，跳过")
    except Exception as e:
        print(f"  ✗ 删除表 {table} 失败: {e}")


def main():
    print("=" * 50)
    print("数据库优化迁移 - 问题1：审核字段清理")
    print("=" * 50)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 步骤1：先确保数据已同步到 audit 表
        print("\n[步骤1] 同步审核数据到 audit 统一表...")
        migr_lost_item_audit_to_unified(cursor, conn)
        
        # 步骤2：删除 lost_item 的冗余审核列
        print("\n[步骤2] 删除 lost_item 冗余审核列...")
        drop_column_if_exists(cursor, conn, 'lost_item', 'audit_time')
        drop_column_if_exists(cursor, conn, 'lost_item', 'audit_remark')
        drop_column_if_exists(cursor, conn, 'lost_item', 'audit_by')
        
        # 步骤3：删除 claim_form 的冗余审核列
        print("\n[步骤3] 删除 claim_form 冗余审核列...")
        drop_column_if_exists(cursor, conn, 'claim_form', 'audit_time')
        drop_column_if_exists(cursor, conn, 'claim_form', 'audit_remark')
        
        # 步骤4：删除未使用的 temp_admin_requests 表
        print("\n[步骤4] 删除未使用的 temp_admin_requests 表...")
        drop_table_if_exists(cursor, conn, 'temp_admin_requests')
        
        # 显示清理后的表结构
        print("\n" + "=" * 50)
        print("清理完成！当前 lost_item 表结构：")
        cursor.execute("SHOW COLUMNS FROM lost_item")
        for col in cursor.fetchall():
            print(f"  - {col[0]} ({col[1]})")
        
        print("\n当前 claim_form 表结构：")
        cursor.execute("SHOW COLUMNS FROM claim_form")
        for col in cursor.fetchall():
            print(f"  - {col[0]} ({col[1]})")
        
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
