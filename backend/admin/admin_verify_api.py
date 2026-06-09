
from flask import Blueprint, request, jsonify
from datetime import datetime
import pymysql
from admin.admin_common import get_conn, send_verify_notification

admin_verify_bp = Blueprint('admin_verify', __name__)

@admin_verify_bp.route('/user-verify', methods=['GET'])
def get_user_verify_list():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM user_verify ORDER BY create_time DESC")
        verify_list = cursor.fetchall()
        
        status_labels = ['待审核', '已通过', '已拒绝']
        result = []
        for item in verify_list:
            st = item['status'] if item['status'] is not None else 0
            # 通过 user_id 从 user 表获取联系方式
            user_phone = None
            user_email = None
            if item.get('user_id'):
                cursor.execute("SELECT phone, email FROM user WHERE user_id = %s", (item['user_id'],))
                user_info = cursor.fetchone()
                if user_info:
                    user_phone = user_info.get('phone')
                    user_email = user_info.get('email')
            result.append({
                'verify_id': item['verify_id'],
                'user_id': item['user_id'],
                'identity': item['identity'],
                'real_name': item['real_name'],
                'id_card': item.get('id_card'),
                'student_id': item.get('student_id'),
                'school': item.get('school'),
                'phone': user_phone,
                'email': user_email,
                'id_card_front': item.get('id_card_front'),
                'id_card_back': item.get('id_card_back'),
                'status': st,
                'status_label': status_labels[st] if 0 <= st < len(status_labels) else '未知',
                'create_time': item['create_time'].strftime('%Y-%m-%d %H:%M:%S') if item.get('create_time') else ''
            })
        
        return jsonify({'code': 200, 'message': 'success', 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_verify_bp.route('/user-verify', methods=['POST'])
def add_user_verify():
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        identity = data.get('identity')
        real_name = data.get('real_name')
        student_id = data.get('student_id')
        school = data.get('school')
        phone = data.get('phone')
        email = data.get('email')
        id_card_front = data.get('id_card_front')
        id_card_back = data.get('id_card_back')
        
        if not user_id or not identity or not real_name:
            return jsonify({'success': False, 'message': '用户ID、身份类型和真实姓名不能为空'})
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_verify 
            (user_id, identity, real_name, student_id, school, id_card_front, id_card_back, status, create_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            int(user_id),
            identity,
            real_name,
            student_id,
            school,
            id_card_front,
            id_card_back,
            0,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        verify_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({'success': True, 'message': '提交成功', 'verify_id': verify_id})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_verify_bp.route('/user-verify/<int:verify_id>', methods=['DELETE'])
def delete_user_verify(verify_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM user_verify WHERE verify_id = %s", (verify_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return jsonify({'success': True, 'message': '删除成功'})
        else:
            return jsonify({'success': False, 'message': '未找到该认证记录'})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_verify_bp.route('/user-verify/<int:verify_id>/approve', methods=['POST'])
def approve_user_verify(verify_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id, real_name, identity FROM user_verify WHERE verify_id = %s", (verify_id,))
        verify = cursor.fetchone()
        
        if not verify:
            return jsonify({'code': 404, 'message': '认证记录不存在'}), 404
        
        user_id = verify[0]
        real_name = verify[1]
        identity = verify[2]
        
        # 更新认证状态
        cursor.execute("UPDATE user_verify SET status = 1, update_time = %s WHERE verify_id = %s", 
                      (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), verify_id))
        
        # 身份映射：处理前端可能提交的不同身份值
        identity_map = {
            'student': 'student',
            'teacher': 'teacher',
            'staff': 'staff',
            'admin': 'admin',
            'maintainer': 'maintainer',
            'maintenance': 'maintainer',
            '维修工': 'maintainer',
            '教师': 'teacher',
            '学生': 'student',
            '教职工': 'staff'
        }
        role_value = identity_map.get(identity, identity)
        
        # 同步更新用户表的 role 字段
        cursor.execute("UPDATE user SET role = %s WHERE user_id = %s", (role_value, user_id))
        
        send_verify_notification(user_id, True, real_name, identity)
        
        conn.commit()
        
        return jsonify({'code': 200, 'message': '通过成功', 'success': True})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_verify_bp.route('/user-verify/<int:verify_id>/reject', methods=['POST'])
def reject_user_verify(verify_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id, real_name, identity FROM user_verify WHERE verify_id = %s", (verify_id,))
        verify = cursor.fetchone()
        
        if not verify:
            return jsonify({'code': 404, 'message': '认证记录不存在'}), 404
        
        user_id = verify[0]
        real_name = verify[1]
        identity = verify[2]
        
        cursor.execute(
            "UPDATE user_verify SET status = 2, update_time = %s WHERE verify_id = %s",
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), verify_id)
        )
        
        send_verify_notification(user_id, False, real_name, identity)
        
        conn.commit()
        
        return jsonify({'code': 200, 'message': '拒绝成功', 'success': True})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
