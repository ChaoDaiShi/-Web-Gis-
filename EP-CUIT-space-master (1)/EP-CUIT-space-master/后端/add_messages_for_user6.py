import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

def add_messages_for_user6():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        test_user_id = 6
        
        # Sample test messages
        test_messages = [
            {
                "title": "欢迎使用失物招领系统",
                "content": "您好！欢迎使用校园失物招领系统。您可以发布失物信息，也可以浏览他人发布的失物信息。",
                "message_type": "system"
            },
            {
                "title": "您的认证申请已提交",
                "content": "您的身份认证申请已成功提交，请等待管理员审核。审核通过后，您将获得更多功能权限。",
                "message_type": "system"
            },
            {
                "title": "新物品发布提醒",
                "content": "有人在图书馆附近发布了一条新的失物信息：黑色校园卡，有时间可以去看看是否是您丢失的！",
                "message_type": "publish"
            }
        ]
        
        # Insert test messages
        print("Adding test messages for user 6...")
        for msg in test_messages:
            cursor.execute("""
                INSERT INTO messages (user_id, title, content, message_type, is_read)
                VALUES (%s, %s, %s, %s, 0)
            """, (test_user_id, msg['title'], msg['content'], msg['message_type']))
            print(f"  Added: {msg['title']}")
        
        conn.commit()
        print(f"\n[OK] Successfully added {len(test_messages)} test messages for user 6")
        
        # Verify
        cursor.execute("""
            SELECT message_id, user_id, title, message_type, is_read 
            FROM messages 
            WHERE user_id = %s 
            ORDER BY create_time DESC
        """, (test_user_id,))
        messages = cursor.fetchall()
        
        print(f"\n[OK] Now user 6 has {len(messages)} messages:")
        for msg in messages:
            print(f"  - [{msg['message_id']}] {msg['title']}")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_messages_for_user6()
