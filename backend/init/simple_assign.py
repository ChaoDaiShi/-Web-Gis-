
# -*- coding: utf-8 -*-
import pymysql
from config import DB_CONFIG

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

try:
    print("获取校区信息...")
    cursor.execute("SELECT id, name FROM map_config")
    campuses = cursor.fetchall()
    
    for campus in campuses:
        print(f"校区 {campus[0]}: {campus[1]}")
    
    print("\n获取物品信息...")
    cursor.execute("SELECT item_id FROM lost_item")
    items = cursor.fetchall()
    
    print(f"找到 {len(items)} 个物品")
    
    # 为所有物品分配到第一个校区
    campus_id = campuses[0][0]
    
    assigned = 0
    for item in items:
        item_id = item[0]
        cursor.execute("INSERT IGNORE INTO item_campus (item_id, campus_id) VALUES (%s, %s)", 
                      (item_id, campus_id))
        if cursor.rowcount > 0:
            assigned += 1
    
    conn.commit()
    print(f"\n已为 {assigned} 个物品分配到校区 {campus_id}")
    
    # 为报修分配校区
    cursor.execute("SELECT repair_id FROM repair")
    repairs = cursor.fetchall()
    
    assigned_repair = 0
    for repair in repairs:
        repair_id = repair[0]
        cursor.execute("INSERT IGNORE INTO repair_campus (repair_id, campus_id) VALUES (%s, %s)", 
                      (repair_id, campus_id))
        if cursor.rowcount > 0:
            assigned_repair += 1
    
    conn.commit()
    print(f"已为 {assigned_repair} 个报修分配到校区 {campus_id}")
    
    print("\n最终结果:")
    cursor.execute("SELECT campus_id, COUNT(*) FROM item_campus GROUP BY campus_id")
    for row in cursor.fetchall():
        print(f"校区 {row[0]}: {row[1]} 个物品")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
finally:
    cursor.close()
    conn.close()

