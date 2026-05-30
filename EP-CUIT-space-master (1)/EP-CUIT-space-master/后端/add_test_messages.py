import pymysql
from datetime import datetime

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

def add_test_messages():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # First, check what users exist
        print("Checking existing users...")
        cursor.execute("SELECT user_id, username FROM user LIMIT 10")
        users = cursor.fetchall()
        
        if not users:
            print("[ERROR] No users found! Please register a user first.")
            return
        
        print(f"[OK] Found {len(users)} users:")
        for user in users:
            print(f"  - user_id: {user['user_id']}, username: {user['username']}")
        
        # Use the first user for test messages
        test_user_id = users[0]['user_id']
        print(f"\nUsing user_id {test_user_id} for test messages")
        
        # Sample test messages
        test_messages = [
            {
                "title": "欢迎使用失物招领系统",
                "content": "您好！欢迎使用校园失物招领系统。您可以发布失物信息，也可以浏览他人发布的失物信息。",
                "message_type": "system"
            },
            {
                "title": "新物品发布通知",
                "content": "有人发布了新的失物信息！物品ID：1，标题：黑色钱包，地点：图书馆。",
                "message_type": "publish"
            },
            {
                "title": "认领申请提醒",
                "content": "您的物品收到了新的认领申请！物品ID：1，请及时处理。",
                "message_type": "claim"
            },
            {
                "title": "物品归还通知",
                "content": "您认领的物品已被标记为归还！物品ID：1。",
                "message_type": "return"
            },
            {
                "title": "系统维护通知",
                "content": "系统将于今晚22:00-24:00进行维护，请提前保存好您的数据。",
                "message_type": "reminder"
            }
        ]
        
        # Insert test messages
        print("\nAdding test messages...")
        for msg in test_messages:
            cursor.execute("""
                INSERT INTO messages (user_id, title, content, message_type, is_read)
                VALUES (%s, %s, %s, %s, 0)
            """, (test_user_id, msg['title'], msg['content'], msg['message_type']))
            print(f"  Added: {msg['title']}")
        
        conn.commit()
        print(f"\n[OK] Successfully added {len(test_messages)} test messages for user {test_user_id}")
        
        # Verify the messages were added
        print("\nVerifying messages...")
        cursor.execute("""
            SELECT message_id, user_id, title, message_type, is_read, create_time 
            FROM messages 
            WHERE user_id = %s 
            ORDER BY create_time DESC
        """, (test_user_id,))
        messages = cursor.fetchall()
        
        print(f"[OK] Found {len(messages)} messages for user {test_user_id}:")
        for msg in messages:
            print(f"  - [{msg['message_id']}] {msg['title']} ({msg['message_type']}, read: {msg['is_read']})")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_test_messages()
