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
    
    alter_table_sql = """
    ALTER TABLE messages MODIFY COLUMN message_type ENUM('system', 'claim', 'publish', 'reminder', 'return') DEFAULT 'system';
    """
    
    cursor.execute(alter_table_sql)
    conn.commit()
    print("messages table updated successfully - added 'return' type")
    
except Exception as e:
    print("Failed to update table: %s" % str(e))
    import traceback
    traceback.print_exc()
    conn.rollback()
finally:
    cursor.close()
    conn.close()
