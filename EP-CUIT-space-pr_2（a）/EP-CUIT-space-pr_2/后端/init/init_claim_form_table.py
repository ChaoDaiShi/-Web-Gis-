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
    CREATE TABLE IF NOT EXISTS claim_form (
        claim_id INT AUTO_INCREMENT PRIMARY KEY,
        item_id INT,
        applicant_name VARCHAR(50),
        applicant_phone VARCHAR(50) NOT NULL,
        applicant_email VARCHAR(100),
        claim_reason TEXT NOT NULL,
        item_description TEXT NOT NULL,
        user_id INT,
        proof_images TEXT,
        status INT DEFAULT 0,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    cursor.execute(create_table_sql)
    conn.commit()
    print("claim_form 表创建成功")
    
except Exception as e:
    print(f"创建表失败: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
