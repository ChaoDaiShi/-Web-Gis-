#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息通知系统初始化脚本
用于创建消息表并插入测试数据
"""

import pymysql
from datetime import datetime, timedelta

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

def get_conn():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def create_message_table():
    """创建消息表"""
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # 检查用户表是否存在
        cursor.execute("SHOW TABLES LIKE 'user'")
        if not cursor.fetchone():
            print("✗ 用户表不存在，请先确保用户表已创建")
            return False
        
        # 创建消息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                message_type ENUM('system', 'claim', 'publish', 'reminder') DEFAULT 'system',
                is_read BOOLEAN DEFAULT FALSE,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        conn.commit()
        print("✓ 消息表创建成功")
        return True
        
    except Exception as e:
        print(f"✗ 创建消息表失败: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def insert_test_messages():
    """插入测试消息数据"""
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # 获取用户ID列表
        cursor.execute("SELECT user_id FROM user LIMIT 3")
        users = cursor.fetchall()
        
        if not users:
            print("✗ 没有找到用户，请先创建用户数据")
            return False
        
        # 测试消息数据
        test_messages = [
            # 系统通知
            {
                "title": "系统维护通知",
                "content": "系统将于今晚22:00-24:00进行维护，期间可能无法正常使用，请提前做好准备。",
                "type": "system",
                "read": False
            },
            {
                "title": "新功能上线",
                "content": "消息通知系统已上线，您现在可以接收系统通知和认领提醒了。",
                "type": "system", 
                "read": True
            },
            
            # 认领通知
            {
                "title": "物品认领成功",
                "content": "您认领的'黑色钱包'已被确认，请联系失主进行交接。",
                "type": "claim",
                "read": False
            },
            {
                "title": "认领请求处理中",
                "content": "您提交的'笔记本电脑'认领申请正在审核中，请耐心等待。",
                "type": "claim",
                "read": True
            },
            
            # 发布通知
            {
                "title": "物品发布成功",
                "content": "您的'红色水杯'已成功发布到失物招领平台。",
                "type": "publish",
                "read": False
            },
            {
                "title": "物品状态更新",
                "content": "您发布的'蓝色书包'已被认领，感谢您的贡献。",
                "type": "publish",
                "read": True
            },
            
            # 提醒通知
            {
                "title": "认领提醒",
                "content": "您有新的认领请求等待处理，请及时查看。",
                "type": "reminder",
                "read": False
            },
            {
                "title": "系统提醒",
                "content": "请完善您的个人资料，以便更好地使用系统功能。",
                "type": "reminder",
                "read": True
            }
        ]
        
        # 插入测试数据
        inserted_count = 0
        for i, message in enumerate(test_messages):
            user_id = users[i % len(users)][0]  # 轮询分配用户
            
            # 设置不同的创建时间，使数据更真实
            create_time = datetime.now() - timedelta(days=i, hours=i)
            
            cursor.execute("""
                INSERT INTO messages (user_id, title, content, message_type, is_read, create_time)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, message["title"], message["content"], message["type"], message["read"], create_time))
            
            inserted_count += 1
        
        conn.commit()
        print(f"✓ 插入 {inserted_count} 条测试消息成功")
        return True
        
    except Exception as e:
        print(f"✗ 插入测试数据失败: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """主函数"""
    print("=" * 50)
    print("消息通知系统初始化")
    print("=" * 50)
    
    # 检查数据库连接
    try:
        conn = get_conn()
        conn.close()
        print("✓ 数据库连接正常")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return
    
    # 创建消息表
    if not create_message_table():
        return
    
    # 插入测试数据
    if not insert_test_messages():
        return
    
    print("\n" + "=" * 50)
    print("初始化完成")
    print("=" * 50)
    print("\n使用方法:")
    print("1. 启动后端服务: python Start.py")
    print("2. 访问个人中心: http://127.0.0.1:5000/profile")
    print("3. 点击'消息通知'按钮查看消息")
    print("4. 或直接访问消息中心: http://127.0.0.1:5000/messages")

if __name__ == "__main__":
    main()