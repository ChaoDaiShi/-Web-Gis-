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
    
    alter_table_sql = """
    ALTER TABLE user_verify 
    MODIFY COLUMN id_card_front LONGTEXT NOT NULL,
    MODIFY COLUMN id_card_back LONGTEXT NOT NULL;
    """
    
    cursor.execute(alter_table_sql)
    conn.commit()
    print("表 user_verify 字段类型修改成功！")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"修改表失败: {e}")