import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import request, jsonify
from datetime import datetime
import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'mapuser',
    'password': '123456',
    'database': 'compus',
    'charset': 'utf8mb4'
}

def get_conn():
    return pymysql.connect(**DB_CONFIG)

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未授权'}), 401
        
        token = auth[7:]
        if token != 'admin_token':
            return jsonify({'code': 403, 'message': '需要管理员权限'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

def send_claim_notification(user_id, is_approved, item_id=None):
    item_title = None
    
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        if item_id:
            cursor.execute("SELECT title FROM lost_item WHERE item_id = %s", (item_id,))
            result = cursor.fetchone()
            if result:
                item_title = result[0]
        
        item_name = item_title or '未知物品'
        
        if is_approved:
            title = f"{item_name}认领申请通过"
            content = f"您的「物品ID：{item_id}，物品名：{item_name}」认领申请已通过，请联系拾物者进行物品交接。"
        else:
            title = f"{item_name}认领申请未通过"
            content = f"您的「物品ID：{item_id}，物品名：{item_name}」认领申请未通过，请检查填写信息是否正确或重新提交申请。"
        
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type, create_time, is_read, is_deleted)
            VALUES (%s, %s, %s, 'claim', %s, FALSE, FALSE)
        """, (user_id, title, content, local_time))
        
        conn.commit()
    except Exception as e:
        print(f"发送认领通知失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def send_return_notification(user_id, is_approved, item_id=None):
    item_title = None
    
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        if item_id:
            cursor.execute("SELECT title FROM lost_item WHERE item_id = %s", (item_id,))
            result = cursor.fetchone()
            if result:
                item_title = result[0]
        
        item_name = item_title or '未知物品'
        
        if is_approved:
            title = f"{item_name}归还申请通过"
            content = f"您的「物品ID：{item_id}，物品名：{item_name}」归还申请已通过，请联系失主进行物品交接。"
        else:
            title = f"{item_name}归还申请未通过"
            content = f"您的「物品ID：{item_id}，物品名：{item_name}」归还申请未通过，请检查填写信息是否正确或重新提交申请。"
        
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type, create_time, is_read, is_deleted)
            VALUES (%s, %s, %s, 'return', %s, FALSE, FALSE)
        """, (user_id, title, content, local_time))
        
        conn.commit()
    except Exception as e:
        print(f"发送归还通知失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def send_verify_notification(user_id, is_approved, real_name=None, identity=None):
    realname = real_name or '未知姓名'
    identity_text = identity or '未知身份'
    
    identity_map = {
        'student': '学生',
        'teacher': '教师',
        'maintenance': '维修工',
        'staff': '教职工'
    }
    identity_display = identity_map.get(identity, identity_text)
    
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        if is_approved:
            title = "身份认证申请通过"
            content = f"您的身份认证申请（姓名：{realname}，身份类型：{identity_display}）已通过审核，恭喜您已获得完整功能权限。"
        else:
            title = "身份认证申请未通过"
            content = f"您的身份认证申请（姓名：{realname}，身份类型：{identity_display}）未通过审核，请检查填写信息是否正确或重新提交认证申请。"
        
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type, create_time, is_read, is_deleted)
            VALUES (%s, %s, %s, 'system', %s, FALSE, FALSE)
        """, (user_id, title, content, local_time))
        
        conn.commit()
    except Exception as e:
        print(f"发送认证审核通知失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
