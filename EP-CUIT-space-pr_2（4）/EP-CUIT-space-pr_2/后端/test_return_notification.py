import pymysql
from datetime import datetime

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

def test_send_notification():
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        test_user_id = 1
        item_id = 26
        item_title = "测试物品"
        
        title = f"{item_title}归还申请通过"
        content = f"您的「物品ID：{item_id}，物品名：{item_title}」归还申请已通过，请联系失主进行物品交接。"
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"准备插入消息: user_id={test_user_id}, title={title}")
        
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type, create_time)
            VALUES (%s, %s, %s, 'return', %s)
        """, (test_user_id, title, content, local_time))
        
        conn.commit()
        print("✓ 消息插入成功！")
        
        cursor.execute("SELECT COUNT(*) FROM messages WHERE user_id = %s AND message_type = 'return'", (test_user_id,))
        count = cursor.fetchone()[0]
        print(f"用户 {test_user_id} 的归还通知数量: {count}")
        
    except Exception as e:
        print(f"✗ 发送通知失败: {e}")
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
