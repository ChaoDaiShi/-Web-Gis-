from flask import Blueprint, request, jsonify
import os
import uuid
from user.models import User
from user.config import db
from utils.cos_utils import cos_client

profile_bp = Blueprint('profile', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_role_display(role):
    role_map = {
        'student': '学生',
        'teacher': '教师',
        'admin': '管理员',
        'staff': '教职工',
        'maintainer': '维修工'
    }
    return role_map.get(role, role) if role else '学生'


def get_signed_url(url_or_key):
    if not url_or_key:
        return None
    key = cos_client.normalize_key(url_or_key)
    if not key:
        return None
    try:
        return cos_client.get_presigned_url(key, expires=3600)
    except Exception as e:
        print(f"生成签名URL失败: {e}")
        return None


@profile_bp.route('/api/profile', methods=['GET'])
def get_profile():
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
            'avatar': get_signed_url(user.avatar_url) if user.avatar_url else '/images/avatars/default.png',
            'bg_image': get_signed_url(user.bg_image) if user.bg_image else '',
            'signature': getattr(user, 'signature', '') or '',
            'bio': getattr(user, 'bio', '') or '',
            'create_time': user.create_time.strftime('%Y-%m-%d') if user.create_time else '',
            'identity': get_role_display(getattr(user, 'role', '')),
            'role': getattr(user, 'role', '') or ''
        }
    })


@profile_bp.route('/api/profile/avatar', methods=['POST'])
def update_avatar():
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

    ext = file.filename.split('.')[-1].lower()
    content_type = f'image/{ext}' if ext in ['jpg', 'jpeg', 'png', 'gif'] else 'image/jpeg'
    
    try:
        result = cos_client.upload_bytes(
            content=file.read(),
            key=f"avatars/{uuid.uuid4().hex}.{ext}",
            content_type=content_type
        )
        user.avatar_url = result['key']
        db.session.commit()

        return jsonify({
            'success': True,
            'avatar': get_signed_url(user.avatar_url)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'上传失败: {str(e)}'}), 500


@profile_bp.route('/api/profile/bg-image', methods=['POST'])
def update_bg_image():
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

    ext = file.filename.split('.')[-1].lower()
    content_type = f'image/{ext}' if ext in ['jpg', 'jpeg', 'png', 'gif'] else 'image/jpeg'
    
    try:
        result = cos_client.upload_bytes(
            content=file.read(),
            key=f"bg_images/{uuid.uuid4().hex}.{ext}",
            content_type=content_type
        )
        user.bg_image = result['key']
        db.session.commit()

        return jsonify({
            'success': True,
            'bg_image': get_signed_url(user.bg_image)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'上传失败: {str(e)}'}), 500


@profile_bp.route('/api/profile', methods=['PUT'])
def update_profile():
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
            'avatar': get_signed_url(user.avatar_url) if user.avatar_url else '/images/avatars/default.png',
            'bg_image': get_signed_url(user.bg_image) if user.bg_image else '',
            'signature': user.signature or '',
            'bio': user.bio or '',
            'create_time': user.create_time.strftime('%Y-%m-%d') if user.create_time else '',
            'identity': get_role_display(getattr(user, 'role', ''))
        }
    })


@profile_bp.route('/api/my/publish', methods=['GET'])
def my_publish():
    from common.db_config import get_conn

    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT li.item_id, li.title, li.description, li.create_time, li.status, li.type, li.image_urls, li.publisher_id,
                   li.audit_status, l.longitude, l.latitude
            FROM lost_item li
            LEFT JOIN location l ON li.location_id = l.location_id
            WHERE li.publisher_id = %s
            ORDER BY li.create_time DESC
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
                "publisher_id": item['publisher_id'],
                "audit_status": item.get('audit_status') or 'pending',
                "lat": item['latitude'],
                "lng": item['longitude'],
                "latitude": item['latitude'],
                "longitude": item['longitude']
            })

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": result})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
