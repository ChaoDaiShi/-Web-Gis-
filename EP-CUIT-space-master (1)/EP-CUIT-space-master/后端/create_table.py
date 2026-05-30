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
    CREATE TABLE IF NOT EXISTS user_verify (
        verify_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        identity VARCHAR(50) NOT NULL,
        real_name VARCHAR(100) NOT NULL,
        id_card VARCHAR(18) NOT NULL,
        student_id VARCHAR(50),
        school VARCHAR(200),
        phone VARCHAR(20),
        email VARCHAR(100),
        id_card_front TEXT NOT NULL,
        id_card_back TEXT NOT NULL,
        status TINYINT DEFAULT 0 COMMENT '0=待审核, 1=已通过',
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_user_id (user_id),
        INDEX idx_status (status),
        INDEX idx_create_time (create_time)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户认证申请表';
    """
    
    cursor.execute(create_table_sql)
    conn.commit()
    print("表 user_verify 创建成功！")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"创建表失败: {e}")