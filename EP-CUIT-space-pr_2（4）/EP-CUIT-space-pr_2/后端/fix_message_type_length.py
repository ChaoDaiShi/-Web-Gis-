import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        ALTER TABLE messages MODIFY COLUMN message_type VARCHAR(20) NOT NULL DEFAULT 'system';
    """)
    
    conn.commit()
    print("✓ 修改 message_type 字段长度成功！")
    
except Exception as e:
    print(f"✗ 修改失败: {e}")
    if conn:
        conn.rollback()
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
