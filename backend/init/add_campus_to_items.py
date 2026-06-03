
import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'mapuser',
    'password': '123456',
    'database': 'compus',
    'charset': 'utf8mb4',
    'port': 3306
}

def add_campus_to_items():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 1. 给 lost_item 表添加 campus_id 字段
        print("正在添加 campus_id 字段到 lost_item 表...")
        try:
            cursor.execute("""
                ALTER TABLE lost_item 
                ADD COLUMN IF NOT EXISTS campus_id INT
            """)
            print("✓ campus_id 字段添加成功")
        except Exception as e:
            print(f"字段添加结果: {e}")
            pass
        
        # 2. 给 repair 表添加 campus_id 字段
        print("\n正在添加 campus_id 字段到 repair 表...")
        try:
            cursor.execute("""
                ALTER TABLE repair 
                ADD COLUMN IF NOT EXISTS campus_id INT
            """)
            print("✓ campus_id 字段添加成功")
        except Exception as e:
            print(f"字段添加结果: {e}")
            pass
        
        conn.commit()
        print("\n数据库更新完成！")
        
        # 3. 显示当前数据检查
        print("\n检查当前校区数据:")
        cursor.execute("SELECT id, name FROM map_config")
        campuses = cursor.fetchall()
        for campus in campuses:
            print(f"  校区 {campus[0]}: {campus[1]}")
        
        print(f"\n当前物品数量:")
        cursor.execute("SELECT COUNT(*) FROM lost_item")
        count = cursor.fetchone()[0]
        print(f"  物品总数: {count}")
        
    except Exception as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_campus_to_items()
