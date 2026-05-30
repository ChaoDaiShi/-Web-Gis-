import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

def check_messages():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Check if messages table exists
        cursor.execute("SHOW TABLES LIKE 'messages'")
        if not cursor.fetchone():
            print("[ERROR] messages table does not exist!")
            return
        
        print("[OK] messages table exists")
        
        # Show table structure
        print("\n=== Table Structure ===")
        cursor.execute("DESCRIBE messages")
        for row in cursor.fetchall():
            print(row)
        
        # Show all messages
        print("\n=== All Messages ===")
        cursor.execute("SELECT * FROM messages ORDER BY create_time DESC")
        messages = cursor.fetchall()
        
        if not messages:
            print("[ERROR] No message data!")
        else:
            print(f"[OK] Found {len(messages)} messages:")
            for msg in messages:
                print(f"  - message_id: {msg['message_id']}, user_id: {msg['user_id']}, title: {msg['title']}, is_deleted: {msg['is_deleted']}")
        
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_messages()
