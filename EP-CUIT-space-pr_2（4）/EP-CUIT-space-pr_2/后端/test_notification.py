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
    
    # 检查消息表是否存在
    cursor.execute("SHOW TABLES LIKE 'messages'")
    result = cursor.fetchone()
    print(f"消息表存在: {result is not None}")
    
    # 检查claim_form表
    cursor.execute("SELECT COUNT(*) FROM claim_form")
    count = cursor.fetchone()[0]
    print(f"认领表单数量: {count}")
    
    # 查看claim_form的结构
    cursor.execute("DESCRIBE claim_form")
    print("\nclaim_form表结构:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # 查看是否有user_id字段
    cursor.execute("SELECT user_id FROM claim_form LIMIT 5")
    user_ids = cursor.fetchall()
    print(f"\nuser_id示例: {user_ids}")
    
    # 查看messages表结构
    cursor.execute("DESCRIBE messages")
    print("\nmessages表结构:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # 测试插入消息
    if user_ids:
        test_user_id = user_ids[0][0]
        print(f"\n测试向用户 {test_user_id} 发送消息...")
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type)
            VALUES (%s, %s, %s, 'claim')
        """, (test_user_id, "测试通知", "这是一条测试消息",))
        conn.commit()
        print("消息插入成功!")
        
        # 验证插入
        cursor.execute("SELECT COUNT(*) FROM messages WHERE user_id = %s", (test_user_id,))
        msg_count = cursor.fetchone()[0]
        print(f"用户 {test_user_id} 的消息数量: {msg_count}")
    
    conn.close()
    print("\n测试完成!")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()