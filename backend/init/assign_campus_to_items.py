
# -*- coding: utf-8 -*-
"""
为现有物品分配校区的脚本
根据物品坐标或默认方式分配校区
"""

import pymysql
from config import DB_CONFIG


def assign_campus_to_items():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        print("正在为现有物品分配校区...")
        
        # 获取所有校区配置
        cursor.execute("""
            SELECT id, name, center_lng, center_lat, sw_lng, sw_lat, ne_lng, ne_lat
            FROM map_config
        """)
        campuses = cursor.fetchall()
        
        if not campuses:
            print("没有找到校区配置！")
            return
        
        print(f"找到 {len(campuses)} 个校区:")
        for campus in campuses:
            print(f"  校区 {campus['id']}: {campus['name']}")
        
        # 获取所有物品
        cursor.execute("""
            SELECT li.item_id, l.longitude, l.latitude
            FROM lost_item li
            LEFT JOIN location l ON li.location_id = l.location_id
            ORDER BY li.item_id
        """)
        items = cursor.fetchall()
        
        print(f"\n找到 {len(items)} 个物品")
        
        assigned_count = 0
        for item in items:
            item_id = item['item_id']
            
            # 检查是否已经有关联
            cursor.execute("""
                SELECT COUNT(*) as count FROM item_campus WHERE item_id = %s
            """, (item_id,))
            if cursor.fetchone()['count'] > 0:
                continue
            
            campus_id = None
            
            # 如果有坐标，根据坐标判断校区
            if item['longitude'] and item['latitude']:
                lng = float(item['longitude'])
                lat = float(item['latitude'])
                
                for campus in campuses:
                    if (campus['sw_lng'] <= lng <= campus['ne_lng'] and
                        campus['sw_lat'] <= lat <= campus['ne_lat']):
                        campus_id = campus['id']
                        break
            
            # 如果没有坐标或找不到匹配校区，使用第一个校区
            if not campus_id:
                campus_id = campuses[0]['id']
            
            # 创建关联
            try:
                cursor.execute("""
                    INSERT INTO item_campus (item_id, campus_id)
                    VALUES (%s, %s)
                """, (item_id, campus_id))
                assigned_count += 1
            except Exception as e:
                print(f"物品 {item_id} 分配失败: {e}")
        
        conn.commit()
        print(f"\n成功为 {assigned_count} 个物品分配了校区")
        
        # 检查报修
        print("\n正在为现有报修分配校区...")
        cursor.execute("SELECT COUNT(*) as count FROM repair")
        repair_count = cursor.fetchone()['count']
        
        if repair_count > 0:
            cursor.execute("SELECT repair_id FROM repair")
            repairs = cursor.fetchall()
            
            assigned_repair_count = 0
            for repair in repairs:
                repair_id = repair['repair_id']
                
                cursor.execute("""
                    SELECT COUNT(*) as count FROM repair_campus WHERE repair_id = %s
                """, (repair_id,))
                if cursor.fetchone()['count'] > 0:
                    continue
                
                # 默认分配到第一个校区
                campus_id = campuses[0]['id']
                try:
                    cursor.execute("""
                        INSERT INTO repair_campus (repair_id, campus_id)
                        VALUES (%s, %s)
                    """, (repair_id, campus_id))
                    assigned_repair_count += 1
                except Exception as e:
                    print(f"报修 {repair_id} 分配失败: {e}")
            
            conn.commit()
            print(f"成功为 {assigned_repair_count} 个报修分配了校区")
        
        # 显示结果
        print("\n分配结果:")
        cursor.execute("""
            SELECT ic.campus_id, mc.name, COUNT(ic.item_id) as count
            FROM item_campus ic
            JOIN map_config mc ON ic.campus_id = mc.id
            GROUP BY ic.campus_id, mc.name
        """)
        results = cursor.fetchall()
        
        for row in results:
            print(f"  校区 {row['campus_id']} ({row['name']}): {row['count']} 个物品")
        
    except Exception as e:
        print(f"分配校区失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    assign_campus_to_items()

