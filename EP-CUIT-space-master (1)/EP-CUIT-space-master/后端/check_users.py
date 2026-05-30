import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

def check_users():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Check all users
        print("=== All Users ===")
        cursor.execute("SELECT user_id, username, email, phone FROM user")
        users = cursor.fetchall()
        
        for user in users:
            print(f"user_id: {user['user_id']}, username: {user['username']}, email: {user['email']}, phone: {user['phone']}")
            
            # Check messages for this user
            cursor.execute("SELECT COUNT(*) FROM messages WHERE user_id = %s AND is_deleted = 0", (user['user_id'],))
            msg_count = cursor.fetchone()
            print(f"  Messages: {list(msg_count.values())[0]}")
        
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_users()
