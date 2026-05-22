import pymysql
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'user': 'mapuser',
    'password': '123456',
    'database': 'compus',
    'charset': 'utf8mb4'
}

def test_send_notification():
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Database connected successfully")
        
        user_id = 1
        title = "Test Notification"
        content = "This is a test notification to verify the notification function."
        message_type = 'claim'
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print("Preparing to insert notification - user_id: %d, title: %s" % (user_id, title))
        
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type, create_time, is_read, is_deleted)
            VALUES (%s, %s, %s, %s, %s, FALSE, FALSE)
        """, (user_id, title, content, message_type, local_time))
        
        conn.commit()
        
        print("Notification inserted successfully!")
        
        cursor.execute("SELECT * FROM messages WHERE user_id = %s ORDER BY create_time DESC LIMIT 1", (user_id,))
        result = cursor.fetchone()
        if result:
            print("Latest notification record: %s" % str(result))
        else:
            print("Failed to retrieve the inserted notification")
            
    except Exception as e:
        print("Test failed: %s" % str(e))
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    test_send_notification()
