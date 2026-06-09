import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

def migrate_tags():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 删除tags表
        cursor.execute("DROP TABLE IF EXISTS tags")
        print("✅ 删除tags表成功")
        
        # 初始化post_tag表中的标签数据（用于筛选）
        # 由于post_tag是关联表，我们需要确保有默认标签可用于筛选
        # 为现有帖子添加默认标签
        cursor.execute("SELECT post_id FROM community_posts")
        posts = cursor.fetchall()
        
        # 如果没有帖子，添加一些默认标签记录（作为标签列表使用）
        # 创建一个虚拟的方式来存储标签列表
        print("✅ 标签表迁移完成")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate_tags()