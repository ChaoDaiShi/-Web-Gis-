import pymysql
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from admin.admin_common import send_verify_notification, get_conn

def test_verify_notification():
    print("Testing verify notification...")
    
    test_cases = [
        {
            "user_id": 6,
            "is_approved": True,
            "real_name": "测试用户",
            "identity": "student",
            "description": "Test: User verification approved"
        },
        {
            "user_id": 6,
            "is_approved": False,
            "real_name": "测试用户",
            "identity": "teacher",
            "description": "Test: User verification rejected"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[Test {i}] {test_case['description']}")
        print(f"  User ID: {test_case['user_id']}")
        print(f"  Real Name: {test_case['real_name']}")
        print(f"  Identity: {test_case['identity']}")
        print(f"  Approved: {test_case['is_approved']}")
        
        try:
            send_verify_notification(
                test_case['user_id'],
                test_case['is_approved'],
                test_case['real_name'],
                test_case['identity']
            )
            print(f"  [OK] Notification sent successfully")
        except Exception as e:
            print(f"  [ERROR] Failed to send notification: {e}")
    
    print("\n" + "="*60)
    print("Verifying messages in database...")
    
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT message_id, user_id, title, content, message_type, is_read
            FROM messages
            WHERE user_id = 6 AND message_type = 'system'
            ORDER BY create_time DESC
            LIMIT 10
        """)
        
        messages = cursor.fetchall()
        
        print(f"\nFound {len(messages)} system messages for user 6:")
        for msg in messages:
            print(f"\n[Message ID: {msg['message_id']}]")
            print(f"  Title: {msg['title']}")
            print(f"  Content: {msg['content']}")
            print(f"  Type: {msg['message_type']}")
            print(f"  Read: {msg['is_read']}")
        
    except Exception as e:
        print(f"[ERROR] Failed to query messages: {e}")
    finally:
        cursor.close()
        conn.close()
    
    print("\n" + "="*60)
    print("Test completed!")

if __name__ == "__main__":
    test_verify_notification()
