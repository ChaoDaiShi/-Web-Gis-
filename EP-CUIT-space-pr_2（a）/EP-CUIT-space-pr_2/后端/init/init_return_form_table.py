import pymysql

def init_return_form_table():
    connection = None
    cursor = None
    
    try:
        connection = pymysql.connect(
            host='localhost',
            user='mapuser',
            password='123456',
            database='compus',
            port=3306
        )
        cursor = connection.cursor()
        
        create_table_sql = """
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
        """
        
        cursor.execute(create_table_sql)
        connection.commit()
        
        print("return_form 表创建成功！")
        
    except pymysql.Error as e:
        print(f"创建表失败: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == '__main__':
    init_return_form_table()
