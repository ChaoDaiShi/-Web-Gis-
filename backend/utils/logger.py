import pymysql
from datetime import datetime
from flask import request, session, has_request_context
from common.db_config import get_conn as _get_conn

def get_conn():
    try:
        conn = _get_conn()
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def get_current_user_id():
    """从session中获取当前用户ID"""
    if has_request_context():
        return session.get('user_id') or session.get('user') or session.get('admin_id')
    return None

def log_action(user_id, action, target_type=None, target_id=None, detail=None, ip_address=None):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO system_logs (user_id, action, target_type, target_id, detail, ip_address, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, action, target_type, target_id, detail, ip_address, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"日志记录失败: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def auto_log(action, target_type=None, target_id=None, detail=None):
    """自动从Flask请求上下文中提取用户信息并记录日志"""
    if not has_request_context():
        return False
    user_id = get_current_user_id()
    ip_address = request.remote_addr if request else None
    return log_action(user_id, action, target_type, target_id, detail, ip_address)

def get_logs(page=1, per_page=20, user_id=None, action=None, target_type=None, start_time=None, end_time=None):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        if not conn:
            return {'code': 500, 'message': '数据库连接失败'}
        
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = "SELECT * FROM system_logs WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)
        
        if action:
            query += " AND action LIKE %s"
            params.append(f'%{action}%')
        
        if target_type:
            query += " AND target_type = %s"
            params.append(target_type)
        
        if start_time:
            query += " AND created_at >= %s"
            params.append(start_time)
        
        if end_time:
            query += " AND created_at <= %s"
            params.append(end_time)
        
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()['COUNT(*)']
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        
        for log in logs:
            if log.get('created_at'):
                log['created_at'] = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'code': 200,
            'message': 'success',
            'data': {
                'logs': logs,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
        }
    except Exception as e:
        return {'code': 500, 'message': str(e)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()