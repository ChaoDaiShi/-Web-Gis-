# -*- coding: utf-8 -*-
"""
插入初始数据的脚本
"""

import pymysql
from werkzeug.security import generate_password_hash
from datetime import datetime
from config import DB_CONFIG, DEFAULT_ADMIN, INITIAL_CATEGORIES, INITIAL_CAMPUSES

def insert_admin(cursor, conn):
    """插入默认管理员"""
    try:
        cursor.execute("SELECT * FROM admin WHERE username = %s", (DEFAULT_ADMIN['username'],))
        if cursor.fetchone():
            print("✓ 管理员账号已存在，跳过")
            return True
        
        hashed_password = generate_password_hash(DEFAULT_ADMIN['password'])
        cursor.execute("""
            INSERT INTO admin (username, password_hash)
            VALUES (%s, %s)
        """, (DEFAULT_ADMIN['username'], hashed_password))
        conn.commit()
        print(f"✓ 管理员账号初始化成功 (用户名: {DEFAULT_ADMIN['username']}, 密码: {DEFAULT_ADMIN['password']})")
        return True
    except Exception as e:
        print(f"✗ 插入管理员失败: {e}")
        conn.rollback()
        return False

def insert_categories(cursor, conn):
    """插入初始分类"""
    try:
        cursor.execute("SELECT COUNT(*) FROM category")
        result = cursor.fetchone()
        if result[0] > 0:
            print(f"✓ 分类表已有 {result[0]} 条记录，跳过")
            return True
        
        categories = [(cat,) for cat in INITIAL_CATEGORIES]
        cursor.executemany("INSERT INTO category (name) VALUES (%s)", categories)
        conn.commit()
        print(f"✓ 插入 {len(INITIAL_CATEGORIES)} 个分类成功")
        for cat in INITIAL_CATEGORIES:
            print(f"  - {cat}")
        return True
    except Exception as e:
        print(f"✗ 插入分类失败: {e}")
        conn.rollback()
        return False

def insert_campuses(cursor, conn):
    """插入初始校区数据"""
    try:
        cursor.execute("SELECT COUNT(*) FROM map_config")
        result = cursor.fetchone()
        if result[0] > 0:
            print(f"✓ 校区配置表已有 {result[0]} 条记录，跳过")
            return True
        
        campuses = [
            (campus['name'], campus['center_lng'], campus['center_lat'],
             campus['sw_lng'], campus['sw_lat'], campus['ne_lng'], campus['ne_lat'], campus['zoom'])
            for campus in INITIAL_CAMPUSES
        ]
        
        cursor.executemany("""
            INSERT INTO map_config (name, center_lng, center_lat, sw_lng, sw_lat, ne_lng, ne_lat, zoom)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, campuses)
        conn.commit()
        print(f"✓ 插入 {len(INITIAL_CAMPUSES)} 个校区配置成功")
        for campus in INITIAL_CAMPUSES:
            print(f"  - {campus['name']}")
        return True
    except Exception as e:
        print(f"✗ 插入校区配置失败: {e}")
        conn.rollback()
        return False

def insert_test_user(cursor, conn):
    """插入测试用户"""
    try:
        cursor.execute("SELECT COUNT(*) FROM user")
        result = cursor.fetchone()
        if result[0] > 0:
            print(f"✓ 用户表已有 {result[0]} 条记录，跳过")
            return True
        
        test_users = [
            {
                'username': 'testuser',
                'email': 'test@example.com',
                'password': '12345678'
            },
            {
                'username': 'student',
                'email': 'student@example.com',
                'password': '12345678'
            }
        ]
        
        for user in test_users:
            hashed_password = generate_password_hash(user['password'])
            cursor.execute("""
                INSERT INTO user (username, email, password_hash)
                VALUES (%s, %s, %s)
            """, (user['username'], user['email'], hashed_password))
        
        conn.commit()
        print("✓ 插入测试用户成功")
        print("  - testuser (密码: 12345678)")
        print("  - student (密码: 12345678)")
        return True
    except Exception as e:
        print(f"✗ 插入测试用户失败: {e}")
        conn.rollback()
        return False

def insert_test_messages(cursor, conn):
    """插入测试消息"""
    try:
        cursor.execute("SELECT COUNT(*) FROM messages")
        result = cursor.fetchone()
        if result[0] > 0:
            print(f"✓ 消息表已有 {result[0]} 条记录，跳过")
            return True
        
        cursor.execute("SELECT user_id FROM user LIMIT 3")
        users = cursor.fetchall()
        if not users:
            print("✗ 没有找到用户，跳过消息插入")
            return True
        
        test_messages = [
            {'title': '系统维护通知', 'content': '系统将于今晚22:00-24:00进行维护，期间可能无法正常使用，请提前做好准备。', 'type': 'system', 'read': False},
            {'title': '新功能上线', 'content': '消息通知系统已上线，您现在可以接收系统通知和认领提醒了。', 'type': 'system', 'read': True},
            {'title': '物品认领成功', 'content': '您认领的物品已被确认，请联系失主进行交接。', 'type': 'claim', 'read': False},
            {'title': '认领请求处理中', 'content': '您提交的认领申请正在审核中，请耐心等待。', 'type': 'claim', 'read': True},
            {'title': '物品发布成功', 'content': '您发布的物品已成功发布到失物招领平台。', 'type': 'publish', 'read': False},
            {'title': '物品状态更新', 'content': '您发布的物品已被认领，感谢您的贡献。', 'type': 'publish', 'read': True},
            {'title': '认领提醒', 'content': '您有新的认领请求等待处理，请及时查看。', 'type': 'reminder', 'read': False},
            {'title': '系统提醒', 'content': '请完善您的个人资料，以便更好地使用系统功能。', 'type': 'reminder', 'read': True},
        ]
        
        inserted_count = 0
        for i, msg in enumerate(test_messages):
            user_id = users[i % len(users)][0]
            cursor.execute("""
                INSERT INTO messages (user_id, title, content, message_type, is_read)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, msg['title'], msg['content'], msg['type'], msg['read']))
            inserted_count += 1
        
        conn.commit()
        print(f"✓ 插入 {inserted_count} 条测试消息成功")
        return True
    except Exception as e:
        print(f"✗ 插入测试消息失败: {e}")
        conn.rollback()
        return False

def main():
    """主函数"""
    print("开始插入初始数据...")
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 插入初始数据
        tasks = [
            insert_admin,
            insert_categories,
            insert_campuses,
            insert_test_user,
            insert_test_messages
        ]
        
        for task in tasks:
            task(cursor, conn)
        
        cursor.close()
        conn.close()
        
        print("\n✓ 所有初始数据插入完成")
        
    except Exception as e:
        print(f"\n✗ 插入初始数据失败: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()

if __name__ == '__main__':
    main()
