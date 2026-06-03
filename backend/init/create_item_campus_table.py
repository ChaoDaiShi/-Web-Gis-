
# -*- coding: utf-8 -*-
"""
创建物品与校区关联表的脚本
"""

import pymysql
from config import DB_CONFIG


def create_item_campus_table():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 创建物品-校区关联表
        print("正在创建 item_campus 关联表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS item_campus (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_id INT NOT NULL COMMENT '物品ID',
                campus_id INT NOT NULL COMMENT '校区ID',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES lost_item(item_id) ON DELETE CASCADE,
                FOREIGN KEY (campus_id) REFERENCES map_config(id) ON DELETE CASCADE,
                UNIQUE KEY unique_item_campus (item_id, campus_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='物品与校区关联表';
        """)
        
        # 创建报修-校区关联表
        print("正在创建 repair_campus 关联表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repair_campus (
                id INT AUTO_INCREMENT PRIMARY KEY,
                repair_id INT NOT NULL COMMENT '报修ID',
                campus_id INT NOT NULL COMMENT '校区ID',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (repair_id) REFERENCES repair(repair_id) ON DELETE CASCADE,
                FOREIGN KEY (campus_id) REFERENCES map_config(id) ON DELETE CASCADE,
                UNIQUE KEY unique_repair_campus (repair_id, campus_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报修与校区关联表';
        """)
        
        conn.commit()
        print("✓ 关联表创建成功！")
        
        # 显示当前数据
        print("\n检查现有数据:")
        cursor.execute("SELECT id, name FROM map_config")
        campuses = cursor.fetchall()
        for campus in campuses:
            print(f"  校区 {campus[0]}: {campus[1]}")
        
        cursor.execute("SELECT COUNT(*) FROM lost_item")
        item_count = cursor.fetchone()[0]
        print(f"\n  物品总数: {item_count}")
        
        cursor.execute("SELECT COUNT(*) FROM repair")
        repair_count = cursor.fetchone()[0]
        print(f"  报修总数: {repair_count}")
        
    except Exception as e:
        print(f"✗ 创建关联表失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def migrate_existing_data():
    """迁移现有数据：将 lost_item 表中的 campus_id 迁移到 item_campus 表"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        print("\n正在迁移现有数据...")
        
        # 检查 lost_item 表是否有 campus_id 字段
        cursor.execute("SHOW COLUMNS FROM lost_item LIKE 'campus_id'")
        has_campus_id = cursor.fetchone()
        
        if has_campus_id:
            # 获取有 campus_id 的物品
            cursor.execute("""
                SELECT item_id, campus_id 
                FROM lost_item 
                WHERE campus_id IS NOT NULL
            """)
            items = cursor.fetchall()
            
            if items:
                # 插入到 item_campus 表
                insert_count = 0
                for item in items:
                    try:
                        cursor.execute("""
                            INSERT IGNORE INTO item_campus (item_id, campus_id)
                            VALUES (%s, %s)
                        """, (item['item_id'], item['campus_id']))
                        insert_count += 1
                    except Exception as e:
                        print(f"  跳过物品 {item['item_id']}: {e}")
                
                conn.commit()
                print(f"✓ 已迁移 {insert_count} 条物品-校区关联记录")
            else:
                print("  没有找到需要迁移的物品数据")
            
            # 检查 repair 表
            cursor.execute("SHOW COLUMNS FROM repair LIKE 'campus_id'")
            has_repair_campus_id = cursor.fetchone()
            
            if has_repair_campus_id:
                cursor.execute("""
                    SELECT repair_id, campus_id 
                    FROM repair 
                    WHERE campus_id IS NOT NULL
                """)
                repairs = cursor.fetchall()
                
                if repairs:
                    insert_count = 0
                    for repair in repairs:
                        try:
                            cursor.execute("""
                                INSERT IGNORE INTO repair_campus (repair_id, campus_id)
                                VALUES (%s, %s)
                            """, (repair['repair_id'], repair['campus_id']))
                            insert_count += 1
                        except Exception as e:
                            print(f"  跳过报修 {repair['repair_id']}: {e}")
                    
                    conn.commit()
                    print(f"✓ 已迁移 {insert_count} 条报修-校区关联记录")
        
        print("\n数据迁移完成！")
        
    except Exception as e:
        print(f"✗ 数据迁移失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    create_item_campus_table()
    migrate_existing_data()

