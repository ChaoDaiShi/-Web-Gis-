import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

def remove_added_fields():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("正在移除 lost_item 表中新增的字段...")
        
        # 检查并删除 images 字段
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'compus' AND TABLE_NAME = 'lost_item' AND COLUMN_NAME = 'images'
        """)
        if cursor.fetchone()[0] > 0:
            cursor.execute("ALTER TABLE lost_item DROP COLUMN images")
            print("✅ 已删除 images 字段")
        else:
            print("ℹ️ images 字段不存在")
        
        # 检查并删除 claimer_id 字段
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'compus' AND TABLE_NAME = 'lost_item' AND COLUMN_NAME = 'claimer_id'
        """)
        if cursor.fetchone()[0] > 0:
            cursor.execute("ALTER TABLE lost_item DROP COLUMN claimer_id")
            print("✅ 已删除 claimer_id 字段")
        else:
            print("ℹ️ claimer_id 字段不存在")
        
        # 检查并删除 publish_time 字段
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'compus' AND TABLE_NAME = 'lost_item' AND COLUMN_NAME = 'publish_time'
        """)
        if cursor.fetchone()[0] > 0:
            cursor.execute("ALTER TABLE lost_item DROP COLUMN publish_time")
            print("✅ 已删除 publish_time 字段")
        else:
            print("ℹ️ publish_time 字段不存在")
        
        conn.commit()
        print("\n✅ lost_item 表字段清理完成！")
        
        # 显示当前表结构
        cursor.execute("SHOW COLUMNS FROM lost_item")
        print("\n当前 lost_item 表结构：")
        for col in cursor.fetchall():
            print(f"  - {col[0]} ({col[1]})")
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    remove_added_fields()