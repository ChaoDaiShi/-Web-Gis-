import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'mapuser',
    'password': '123456',
    'database': 'compus',
    'charset': 'utf8mb4'
}

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS messages (
        message_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        title VARCHAR(255) NOT NULL,
        content TEXT NOT NULL,
        message_type ENUM('system', 'claim', 'publish', 'reminder') DEFAULT 'system',
        is_read BOOLEAN DEFAULT FALSE,
        is_deleted BOOLEAN DEFAULT FALSE,
        delete_time DATETIME NULL,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    cursor.execute(create_table_sql)
    conn.commit()
    print("messages table created successfully")
    
except Exception as e:
    print("Failed to create table: %s" % str(e))
    import traceback
    traceback.print_exc()
    conn.rollback()
finally:
    cursor.close()
    conn.close()
