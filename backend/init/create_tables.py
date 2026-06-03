import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'mapuser',
    'password': '123456',
    'database': 'compus',
    'charset': 'utf8mb4',
    'port': 3306
}

def create_tables():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    tables = [
        """
        CREATE TABLE IF NOT EXISTS user (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20),
            avatar_url VARCHAR(500),
            signature VARCHAR(255),
            bio TEXT,
            bg_image VARCHAR(500),
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            role VARCHAR(20) DEFAULT 'student',
            status VARCHAR(20) DEFAULT 'normal',
            temp_role VARCHAR(20),
            temp_role_expire DATETIME
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS admin (
            admin_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS temp_admin_requests (
            id VARCHAR(20) PRIMARY KEY,
            user_id VARCHAR(20) NOT NULL,
            reason TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            request_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            audit_by VARCHAR(20),
            audit_time DATETIME,
            audit_remark VARCHAR(200),
            expire_time DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS category (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description VARCHAR(200),
            sort_order INT DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS lost_item (
            item_id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            category_id INT,
            item_type VARCHAR(20) DEFAULT 'lost',
            status VARCHAR(20) DEFAULT 'pending',
            location_name VARCHAR(100),
            longitude FLOAT,
            latitude FLOAT,
            contact_info VARCHAR(100),
            image_url VARCHAR(255),
            publisher_id INT NOT NULL,
            publish_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            found_time DATETIME,
            audit_status VARCHAR(20) DEFAULT 'pending',
            audit_by INT,
            audit_time DATETIME,
            audit_remark VARCHAR(200),
            view_count INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS claim (
            claim_id INT AUTO_INCREMENT PRIMARY KEY,
            item_id INT NOT NULL,
            claimer_id INT NOT NULL,
            claim_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            claim_reason TEXT,
            proof_info VARCHAR(255),
            status VARCHAR(20) DEFAULT 'pending',
            audit_by INT,
            audit_time DATETIME,
            audit_remark VARCHAR(200),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS return_form (
            return_id INT AUTO_INCREMENT PRIMARY KEY,
            item_id INT,
            returner_name VARCHAR(100) NOT NULL,
            returner_phone VARCHAR(20) NOT NULL,
            returner_email VARCHAR(100),
            return_reason TEXT NOT NULL,
            return_location VARCHAR(500),
            user_id INT,
            proof_images TEXT,
            status SMALLINT DEFAULT 0,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS messages (
            message_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            message_type ENUM('system', 'claim', 'publish', 'reminder', 'return') DEFAULT 'system',
            is_read BOOLEAN DEFAULT FALSE,
            is_deleted BOOLEAN DEFAULT FALSE,
            delete_time DATETIME NULL,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS map_config (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            center_lng DECIMAL(12,8) NOT NULL,
            center_lat DECIMAL(12,8) NOT NULL,
            sw_lng DECIMAL(12,8) NOT NULL,
            sw_lat DECIMAL(12,8) NOT NULL,
            ne_lng DECIMAL(12,8) NOT NULL,
            ne_lat DECIMAL(12,8) NOT NULL,
            zoom INT DEFAULT 17,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS repair (
            repair_id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            priority INT DEFAULT 1,
            longitude DECIMAL(12,8) NOT NULL,
            latitude DECIMAL(12,8) NOT NULL,
            location VARCHAR(255),
            status INT DEFAULT 0,
            reporter_id INT NOT NULL,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS system_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            action VARCHAR(50) NOT NULL,
            target_type VARCHAR(50),
            target_id VARCHAR(20),
            detail TEXT,
            ip_address VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS system_configs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            config_key VARCHAR(50) NOT NULL UNIQUE,
            config_value TEXT,
            description VARCHAR(200),
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    ]
    
    for i, sql in enumerate(tables):
        try:
            cursor.execute(sql)
            conn.commit()
            print(f"表 {i+1} 创建成功")
        except Exception as e:
            print(f"表 {i+1} 创建失败: {e}")
            conn.rollback()
    
    cursor.close()
    conn.close()
    print("所有表创建完成")

if __name__ == "__main__":
    create_tables()