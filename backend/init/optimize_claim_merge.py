# -*- coding: utf-8 -*-
"""
数据库优化迁移脚本 - 问题2：合并 claim 和 claim_form 表
1. 将 claim 表数据迁移到 claim_form 表
2. 删除 claim 表
"""

import pymysql
from config import DB_CONFIG


def migrate_claim_to_claim_form(cursor, conn):
    """将 claim 表中的数据迁移到 claim_form 表"""
    print("\n正在检查 claim 表...")
    try:
        cursor.execute("SHOW TABLES LIKE 'claim'")
        if not cursor.fetchone():
            print("  - claim 表不存在，跳过")
            return

        # 查找 claim 中有但 claim_form 中没有的数据
        cursor.execute("""
            SELECT c.item_id, c.claimer_id, c.claim_reason, c.status, c.created_at
            FROM claim c
            LEFT JOIN claim_form cf ON cf.item_id = c.item_id AND cf.user_id = c.claimer_id
            WHERE cf.claim_id IS NULL
        """)
        missing = cursor.fetchall()
        
        if missing:
            for row in missing:
                item_id, claimer_id, claim_reason, status, created_at = row
                # 状态映射：claim.status = 'approved'/'pending' → claim_form.status = 1/0
                form_status = 1 if status == 'approved' else 0
                cursor.execute("""
                    INSERT INTO claim_form (item_id, user_id, claim_reason, status, create_time)
                    VALUES (%s, %s, %s, %s, %s)
                """, (item_id, claimer_id, claim_reason or '', form_status, created_at))
            conn.commit()
            print(f"  ✓ 已迁移 {len(missing)} 条 claim 记录到 claim_form")
        else:
            print("  ✓ claim 数据已全部在 claim_form 中")
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
    print("数据库优化迁移 - 问题2：合并 claim → claim_form")
    print("=" * 50)
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("\n[步骤1] 迁移 claim 数据到 claim_form...")
        migrate_claim_to_claim_form(cursor, conn)
        
        print("\n[步骤2] 删除旧 claim 表...")
        drop_table_if_exists(cursor, conn, 'claim')
        
        print("\n" + "=" * 50)
        print("迁移完成！")
        
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
