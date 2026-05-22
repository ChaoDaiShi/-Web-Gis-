from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
from datetime import datetime

profile_bp = Blueprint('profile', __name__)

BACKEND_ROOT = os.path.dirname(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BACKEND_ROOT, 'static', 'avatars')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@profile_bp.route('/api/profile', methods=['GET'])
def get_profile():
    from user.DenluZhuChe import User, db

    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})

    return jsonify({
        'success': True,
        'data': {
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'avatar': user.avatar_url if user.avatar_url else '/static/avatars/default.png',
            'bg_image': user.bg_image if user.bg_image else '',
            'signature': getattr(user, 'signature', '') or '',
            'bio': getattr(user, 'bio', '') or '',
            'create_time': user.create_time.strftime('%Y-%m-%d') if user.create_time else ''
        }
    })


@profile_bp.route('/api/profile/avatar', methods=['POST'])
def update_avatar():
    from user.DenluZhuChe import User, db

    user_id = request.form.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})

    file = request.files.get('avatar')

    if not file or file.filename == '':
        return jsonify({'success': False, 'message': '请选择文件'})

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': '格式错误'})

    ext = file.filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)
                      
    user.avatar_url = f'/static/avatars/{filename}'
    db.session.commit()

    return jsonify({
        'success': True,
        'avatar': user.avatar_url
    })


@profile_bp.route('/api/profile/bg-image', methods=['POST'])
def update_bg_image():
    from user.DenluZhuChe import User, db

    user_id = request.form.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})

    file = request.files.get('bg_image')

    if not file or file.filename == '':
        return jsonify({'success': False, 'message': '请选择文件'})

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': '格式错误'})

    ext = file.filename.split('.')[-1]
    filename = f"bg_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)
                      
    user.bg_image = f'/static/avatars/{filename}'
    db.session.commit()

    return jsonify({
        'success': True,
        'bg_image': user.bg_image
    })


@profile_bp.route('/api/profile', methods=['PUT'])
def update_profile():
    from user.DenluZhuChe import User, db

    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})

    user.username = data.get('username', user.username)
    user.bio = data.get('bio', user.bio or '')
    user.signature = data.get('signature', user.signature or '')
    user.phone = data.get('phone', user.phone or '')
    
    if data.get('remove_bg'):
        user.bg_image = None

    db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'phone': user.phone or '',
            'avatar': user.avatar_url if user.avatar_url else '/static/avatars/default.png',
            'bg_image': user.bg_image if user.bg_image else '',
            'signature': user.signature or '',
            'bio': user.bio or '',
            'create_time': user.create_time.strftime('%Y-%m-%d') if user.create_time else ''
        }
    })


@profile_bp.route('/api/my/publish', methods=['GET'])
def my_publish():
    import pymysql

    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

    DB_CONFIG = {
        "host": "localhost",
        "user": "mapuser",
        "password": "123456",
        "database": "compus",
        "charset": "utf8mb4"
    }

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT item_id, title, description, create_time, status, type, image_urls, publisher_id
            FROM lost_item
            WHERE publisher_id = %s
            ORDER BY create_time DESC
        """, (int(user_id),))

        items = cursor.fetchall()

        result = []
        for item in items:
            result.append({
                "item_id": item['item_id'],
                "title": item['title'],
                "description": item['description'] or '',
                "create_time": str(item['create_time']) if item['create_time'] else '',
                "status": item['status'],
                "type": item['type'] or 0,
                "image_urls": item['image_urls'] or '',
                "publisher_id": item['publisher_id']
            })

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": result})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@profile_bp.route('/api/my/claim', methods=['GET'])
def my_claim():
    import pymysql

    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

    DB_CONFIG = {
        "host": "localhost",
        "user": "mapuser",
        "password": "123456",
        "database": "compus",
        "charset": "utf8mb4"
    }

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT c.claim_id, l.title, l.type, c.create_time, c.status, l.item_id
            FROM claim c
            JOIN lost_item l ON c.item_id = l.item_id
            WHERE c.claimer_id = %s
            ORDER BY c.create_time DESC
        """, (int(user_id),))

        items = cursor.fetchall()

        result = []
        for item in items:
            result.append({
                "claim_id": item['claim_id'],
                "title": item['title'],
                "type": item['type'],
                "create_time": str(item['create_time']) if item['create_time'] else '',
                "status": item['status'],
                "item_id": item['item_id']
            })

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": result})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@profile_bp.route('/api/my/claim', methods=['POST'])
def add_my_claim():
    import pymysql
    from datetime import datetime

    data = request.get_json()
    user_id = data.get('user_id')
    item_id = data.get('item_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

    if not item_id:
        return jsonify({'success': False, 'message': '物品ID不能为空'}), 400

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

        cursor.execute("""
            INSERT INTO claim (item_id, claimer_id, create_time, status)
            VALUES (%s, %s, %s, %s)
        """, (int(item_id), int(user_id), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "认领记录创建成功"})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@profile_bp.route('/api/my/claim/by-item/<int:item_id>', methods=['DELETE'])
def delete_claim_by_item(item_id):
    import pymysql

    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

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

        cursor.execute("DELETE FROM claim WHERE item_id = %s AND claimer_id = %s", (item_id, int(user_id)))
        
        if cursor.rowcount > 0:
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"success": True, "message": "删除认领记录成功"})
        else:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "未找到该认领记录"}), 404
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@profile_bp.route('/api/my/claim/<int:claim_id>/cancel', methods=['POST'])
def cancel_my_claim(claim_id):
    import pymysql
    from datetime import datetime

    data = request.get_json()
    user_id = data.get('user_id')
    item_id = data.get('item_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

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

        cursor.execute("DELETE FROM claim WHERE claim_id = %s AND claimer_id = %s", (claim_id, int(user_id)))
        
        if cursor.rowcount > 0:
            if item_id:
                cursor.execute("""
                    UPDATE lost_item 
                    SET status = %s 
                    WHERE item_id = %s
                """, (0, int(item_id)))
            
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"success": True, "message": "取消认领成功"})
        else:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "未找到该认领记录"}), 404
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500