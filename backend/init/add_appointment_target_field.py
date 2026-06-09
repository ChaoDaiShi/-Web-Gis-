"""添加预约表的 target_user_id 字段"""
import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

def add_target_user_field():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 检查字段是否存在
        cursor.execute("""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'compus' AND TABLE_NAME = 'appointment' AND COLUMN_NAME = 'target_user_id'
        """)
        
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE appointment 
                ADD COLUMN target_user_id INT NULL COMMENT '预约目标用户ID（失主）',
                ADD FOREIGN KEY (target_user_id) REFERENCES user(user_id)
            """)
            conn.commit()
            print("✅ 已添加 target_user_id 字段")
        else:
            print("ℹ️ target_user_id 字段已存在")
        
        # 检查 messages 表是否有 related_id 和 related_type 字段
        cursor.execute("""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'compus' AND TABLE_NAME = 'messages' AND COLUMN_NAME = 'related_id'
        """)
        
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE messages 
                ADD COLUMN related_id INT NULL COMMENT '关联ID',
                ADD COLUMN related_type VARCHAR(50) NULL COMMENT '关联类型'
            """)
            conn.commit()
            print("✅ 已添加 messages 表的关联字段")
        else:
            print("ℹ️ messages 表关联字段已存在")
        
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_target_user_field()
