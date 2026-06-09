
# -*- coding: utf-8 -*-
"""
验证校区关联功能的脚本
"""

import pymysql
import sys
sys.path.insert(0, 'f:\\工程实践2\\校园失物招领与位置追踪系统\\后端\\init')
from config import DB_CONFIG


def verify_campus_association():
    print("=== 验证校区关联功能 ===\n")
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 1. 检查item_campus表是否存在
        print("1. 检查 item_campus 表...")
        cursor.execute("SHOW TABLES LIKE 'item_campus'")
        if cursor.fetchone():
            print("✓ item_campus 表存在")
            
            # 查看item_campus中的数据
            cursor.execute("SELECT COUNT(*) as count FROM item_campus")
            count = cursor.fetchone()['count']
            print(f"  - item_campus 中有 {count} 条关联记录")
            
            if count > 0:
                cursor.execute("""
                    SELECT ic.item_id, ic.campus_id, mc.name as campus_name, li.title
                    FROM item_campus ic
                    JOIN map_config mc ON ic.campus_id = mc.id
                    LEFT JOIN lost_item li ON ic.item_id = li.item_id
                    LIMIT 5
                """)
                sample = cursor.fetchall()
                print("\n  示例记录:")
                for row in sample:
                    print(f"    - 物品 {row['item_id']} ({row['title']}) 关联到校区 {row['campus_id']} ({row['campus_name']})")
        else:
            print("✗ item_campus 表不存在")
            
        print("\n2. 检查 repair_campus 表...")
        cursor.execute("SHOW TABLES LIKE 'repair_campus'")
        if cursor.fetchone():
            print("✓ repair_campus 表存在")
            
            cursor.execute("SELECT COUNT(*) as count FROM repair_campus")
            count = cursor.fetchone()['count']
            print(f"  - repair_campus 中有 {count} 条关联记录")
        else:
            print("✗ repair_campus 表不存在")
            
        print("\n3. 检查校区数据...")
        cursor.execute("SELECT id, name FROM map_config")
        campuses = cursor.fetchall()
        print(f"  校区数: {len(campuses)}")
        for campus in campuses:
            print(f"    - 校区 {campus['id']}: {campus['name']}")
            
            # 检查每个校区的物品数
            cursor.execute("""
                SELECT COUNT(*) as count FROM item_campus WHERE campus_id = %s
            """, (campus['id'],))
            item_count = cursor.fetchone()['count']
            print(f"      关联物品数: {item_count}")
            
        print("\n=== 验证完成 ===")
        
    except Exception as e:
        print(f"\n✗ 验证失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    verify_campus_association()
