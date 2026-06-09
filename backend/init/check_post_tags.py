import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

def check_post_tags():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 检查post_tags表结构
        cursor.execute("DESCRIBE post_tags")
        print("=== post_tags表结构 ===")
        for row in cursor.fetchall():
            print(row)
        
        # 查询现有数据
        cursor.execute("SELECT * FROM post_tags LIMIT 10")
        print("\n=== post_tags表现有数据 ===")
        for row in cursor.fetchall():
            print(row)
            
        # 检查tags表是否存在
        cursor.execute("SHOW TABLES LIKE 'tags'")
        result = cursor.fetchone()
        print(f"\n=== tags表是否存在: {'存在' if result else '不存在'} ===")
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_post_tags()