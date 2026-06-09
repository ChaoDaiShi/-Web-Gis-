import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

def create_appointment_table():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointment (
                appointment_id INT AUTO_INCREMENT PRIMARY KEY,
                item_id INT NOT NULL,
                user_id INT NOT NULL,
                appointment_time DATETIME NOT NULL,
                location VARCHAR(255) NOT NULL,
                longitude DECIMAL(10,7),
                latitude DECIMAL(10,7),
                contact_name VARCHAR(100) NOT NULL,
                contact_phone VARCHAR(20) NOT NULL,
                note TEXT,
                status ENUM('pending', 'approved', 'rejected', 'completed', 'cancelled') DEFAULT 'pending',
                reviewer_id INT,
                review_time DATETIME,
                review_note TEXT,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES lost_item(item_id),
                FOREIGN KEY (user_id) REFERENCES user(user_id),
                FOREIGN KEY (reviewer_id) REFERENCES admin(admin_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        conn.commit()
        print("✅ 预约表创建成功")
        
    except Exception as e:
        print(f"❌ 创建预约表失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_appointment_table()