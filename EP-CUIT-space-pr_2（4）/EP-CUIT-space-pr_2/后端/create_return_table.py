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
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS return_form (
        return_id INT AUTO_INCREMENT PRIMARY KEY,
        item_id INT,
        username VARCHAR(50),
        applicant_name VARCHAR(100),
        applicant_phone VARCHAR(50) NOT NULL,
        return_reason TEXT NOT NULL,
        item_description TEXT NOT NULL,
        user_id INT,
        proof_images TEXT,
        status SMALLINT DEFAULT 0,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    cursor.execute(create_table_sql)
    conn.commit()
    print("表 return_form 创建成功！")
    
except Exception as e:
    print(f"创建表失败: {e}")
    if conn:
        conn.rollback()
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
