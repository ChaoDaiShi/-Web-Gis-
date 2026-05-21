import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'mapuser',
    'password': '123456',
    'database': 'compus',
    'charset': 'utf8mb4'
}

def init_claim_table():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS claim (
                claim_id INT AUTO_INCREMENT PRIMARY KEY,
                item_id INT NOT NULL,
                claimer_id INT NOT NULL,
                create_time DATETIME NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                FOREIGN KEY (item_id) REFERENCES lost_item(item_id),
                FOREIGN KEY (claimer_id) REFERENCES user(user_id),
                UNIQUE KEY unique_claim (item_id, claimer_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        conn.commit()
        print("claim 表初始化成功")

    except Exception as e:
        print(f"claim 表初始化失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    init_claim_table()
