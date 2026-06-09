import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

def add_tags():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 检查tags表是否存在
        cursor.execute("SHOW TABLES LIKE 'tags'")
        if cursor.fetchone() is None:
            # 创建tags表
            cursor.execute("""
                CREATE TABLE tags (
                    tag_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    description VARCHAR(200),
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ 创建tags表成功")
        
        # 添加标签数据
        tags_data = [
            ("全部", "全部帖子"),
            ("校园生活", "校园生活相关"),
            ("学习交流", "学习交流相关"),
            ("失物招领", "失物招领相关"),
            ("二手交易", "二手交易相关"),
            ("活动公告", "活动公告相关")
        ]
        
        for name, desc in tags_data:
            cursor.execute("SELECT COUNT(*) FROM tags WHERE name = %s", (name,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO tags (name, description) VALUES (%s, %s)", (name, desc))
                print(f"✅ 添加标签: {name}")
            else:
                print(f"ℹ️ 标签已存在: {name}")
        
        conn.commit()
        print("\n✅ 标签数据添加完成！")
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_tags()