"""
创建好友关系表和聊天消息表
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from common.db_config import DB_CONFIG

def create_friend_tables():
    """创建好友相关表"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 好友关系表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_friend (
                friendship_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                friend_id INT NOT NULL,
                status ENUM('pending', 'accepted', 'rejected', 'blocked') DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_friendship (user_id, friend_id),
                INDEX idx_user_id (user_id),
                INDEX idx_friend_id (friend_id),
                INDEX idx_status (status),
                FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
                FOREIGN KEY (friend_id) REFERENCES user(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ 好友关系表 user_friend 创建成功")
        
        # 聊天消息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_message (
                message_id INT AUTO_INCREMENT PRIMARY KEY,
                sender_id INT NOT NULL,
                receiver_id INT NOT NULL,
                content TEXT NOT NULL,
                message_type ENUM('text', 'image', 'system') DEFAULT 'text',
                is_read TINYINT DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_sender (sender_id),
                INDEX idx_receiver (receiver_id),
                INDEX idx_created (created_at),
                INDEX idx_conversation (sender_id, receiver_id),
                FOREIGN KEY (sender_id) REFERENCES user(user_id) ON DELETE CASCADE,
                FOREIGN KEY (receiver_id) REFERENCES user(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ 聊天消息表 chat_message 创建成功")
        
        # 聊天会话表（用于快速查询会话列表）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_conversation (
                conversation_id INT AUTO_INCREMENT PRIMARY KEY,
                user1_id INT NOT NULL,
                user2_id INT NOT NULL,
                last_message_id INT,
                last_message_time DATETIME,
                unread_count_user1 INT DEFAULT 0,
                unread_count_user2 INT DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_conversation (user1_id, user2_id),
                INDEX idx_user1 (user1_id),
                INDEX idx_user2 (user2_id),
                INDEX idx_last_message (last_message_time),
                FOREIGN KEY (user1_id) REFERENCES user(user_id) ON DELETE CASCADE,
                FOREIGN KEY (user2_id) REFERENCES user(user_id) ON DELETE CASCADE,
                FOREIGN KEY (last_message_id) REFERENCES chat_message(message_id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ 聊天会话表 chat_conversation 创建成功")
        
        conn.commit()
        print("\n🎉 所有好友和聊天相关表创建完成！")
        
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    create_friend_tables()
