import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import request, jsonify
from datetime import datetime
import pymysql
from common.db_config import get_conn

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

def get_admin_permissions(admin_id):
    """获取管理员的权限列表"""
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor())
        
        # 获取管理员角色
        cursor.execute('SELECT role, permissions FROM admin WHERE admin_id = %s', (admin_id,))
        admin = cursor.fetchone()
        
        if not admin:
            return []
        
        # 超级管理员拥有所有权限
        if admin['role'] == 'super_admin':
            cursor.execute('SELECT permission_key FROM permission_definition')
            all_permissions = cursor.fetchall()
            return [p['permission_key'] for p in all_permissions]
        
        # 二级管理员从permissions字段获取权限
        if admin['permissions']:
            try:
                import json
                return json.loads(admin['permissions'])
            except:
                return []
        
        return []
    except Exception as e:
        print(f"获取管理员权限失败: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def super_admin_required(fn):
    """超级管理员专用装饰器"""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # 简化处理：如果有admin_token就允许访问
        auth = request.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未授权'}), 401
        
        token = auth[7:]
        if token != 'admin_token':
            return jsonify({'code': 403, 'message': '需要管理员权限'}), 403
        
        # admin_token 直接代表超级管理员
        return fn(*args, **kwargs)
    return wrapper

def permission_required(permission_key):
    """权限验证装饰器"""
    from functools import wraps
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth = request.headers.get('Authorization')
            if not auth or not auth.startswith('Bearer '):
                return jsonify({'code': 401, 'message': '未授权'}), 401
            
            token = auth[7:]
            if token != 'admin_token':
                return jsonify({'code': 403, 'message': '需要管理员权限'}), 403
            
            # 获取管理员ID
            admin_id = request.args.get('admin_id') or request.form.get('admin_id')
            if not admin_id:
                return jsonify({'code': 403, 'message': '需要管理员权限'}), 403
            
            permissions = get_admin_permissions(admin_id)
            
            if permission_key not in permissions:
                return jsonify({'code': 403, 'message': '权限不足'}), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator

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
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        name = real_name or '用户'
        role = identity or '身份'
        if is_approved:
            title = '实名认证已通过'
            content = f'您的「{role}」实名认证（{name}）已通过审核。'
        else:
            title = '实名认证未通过'
            content = f'您的「{role}」实名认证（{name}）未通过审核，请核对信息后重新提交。'
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type, create_time, is_read, is_deleted)
            VALUES (%s, %s, %s, 'system', %s, FALSE, FALSE)
        """, (user_id, title, content, local_time))
        conn.commit()
    except Exception as e:
        print(f"发送认证通知失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def create_audit_record(target_type, target_id, requester_id=None):
    """创建统一审核记录"""
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO audit (target_type, target_id, requester_id, status, create_time, update_time)
            VALUES (%s, %s, %s, 'pending', %s, %s)
        """, (target_type, target_id, requester_id, datetime.now(), datetime.now()))
        
        audit_id = cursor.lastrowid
        conn.commit()
        
        return audit_id
    except Exception as e:
        print(f"创建审核记录失败: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def send_audit_notification(user_id, is_approved, item_id=None, item_title=None, remark=''):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        item_name = item_title or '未知物品'
        
        if is_approved:
            title = f"{item_name}发布审核通过"
            content = f"您发布的「物品ID：{item_id}，物品名：{item_name}」已通过审核，现在其他用户可以在地图上看到该物品了。"
            if remark:
                content += f" 审核备注：{remark}"
        else:
            title = f"{item_name}发布审核未通过"
            content = f"您发布的「物品ID：{item_id}，物品名：{item_name}」未通过审核，请检查物品信息是否完整或重新提交。"
            if remark:
                content += f" 拒绝原因：{remark}"
        
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type, create_time, is_read, is_deleted)
            VALUES (%s, %s, %s, 'audit', %s, FALSE, FALSE)
        """, (user_id, title, content, local_time))
        
        conn.commit()
        print(f"[DEBUG] 审核通知已发送给用户 {user_id}")
    except Exception as e:
        print(f"发送审核通知失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()