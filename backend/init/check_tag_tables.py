import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

def check_tag_tables():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 检查post_tag表结构
        print("=== post_tag表结构 ===")
        cursor.execute("DESCRIBE post_tag")
        for row in cursor.fetchall():
            print(row)
        
        # 查询post_tag现有数据
        cursor.execute("SELECT * FROM post_tag LIMIT 10")
        print("\n=== post_tag表现有数据 ===")
        for row in cursor.fetchall():
            print(row)
        
        # 检查tags表结构
        print("\n=== tags表结构 ===")
        cursor.execute("DESCRIBE tags")
        for row in cursor.fetchall():
            print(row)
        
        # 查询tags现有数据
        cursor.execute("SELECT * FROM tags")
        print("\n=== tags表现有数据 ===")
        for row in cursor.fetchall():
            print(row)
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_tag_tables()