from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
from datetime import datetime

profile_bp = Blueprint('profile', __name__)

BACKEND_ROOT = os.path.dirname(__file__)
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

    db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'phone': user.phone or '',
            'avatar': user.avatar_url if user.avatar_url else '/static/avatars/default.png',
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
            SELECT c.claim_id, l.title, c.create_time, c.status
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
                "create_time": str(item['create_time']) if item['create_time'] else '',
                "status": item['status']
            })

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": result})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500