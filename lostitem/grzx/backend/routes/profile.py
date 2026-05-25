import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from models import User, db
from utils.validators import token_required, allowed_file
from werkzeug.utils import secure_filename

# 创建个人资料相关的蓝图
profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')

@profile_bp.route('/', methods=['GET'])
@token_required
def get_profile(current_user):
    """获取个人资料接口
    
    返回:
        {"success": true, "data": {"user": {...}}}
    """
    return jsonify({
        'success': True,
        'data': current_user.to_dict()
    })

@profile_bp.route('/avatar', methods=['POST'])
@token_required
def update_avatar(current_user):
    """更新头像接口
    
    请求参数:
        avatar: 文件（图片）
    
    返回:
        成功: {"success": true, "message": "头像更新成功", "data": {"avatar": "..."}}
        失败: {"success": false, "message": "错误信息"}
    """
    if 'avatar' not in request.files:
        return jsonify({'success': False, 'message': '没有上传文件'}), 400

    file = request.files['avatar']

    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'}), 400

    if not allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
        return jsonify({'success': False, 'message': '文件类型不允许'}), 400

    # 生成唯一文件名
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    # 确保上传目录存在
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 删除旧头像
    if current_user.avatar and current_user.avatar != 'default.png' and os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.avatar)):
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.avatar))
        except:
            pass

    # 保存新头像
    file.save(filepath)
    current_user.avatar = filename
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '头像更新成功',
        'data': {
            'avatar': f'/static/avatars/{filename}'
        }
    })

@profile_bp.route('/', methods=['PUT'])
@token_required
def update_profile(current_user):
    """更新个人资料接口
    
    请求参数:
        username: 用户名
        signature: 签名
        bio: 个人介绍
    
    返回:
        成功: {"success": true, "message": "个人资料更新成功", "data": {"user": {...}}}
        失败: {"success": false, "message": "错误信息"}
    """
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '请求数据无效'}), 400

    username = data.get('username', '').strip()
    signature = data.get('signature', '').strip()
    bio = data.get('bio', '').strip()

    # 更新用户名
    if username:
        if username != current_user.username:
            existing = User.query.filter_by(username=username).first()
            if existing:
                return jsonify({'success': False, 'message': '该用户名已被使用'}), 409
        current_user.username = username

    # 更新签名
    if 'signature' in data:
        current_user.signature = signature

    # 更新个人介绍
    if 'bio' in data:
        current_user.bio = bio

    db.session.commit()

    return jsonify({
        'success': True,
        'message': '个人资料更新成功',
        'data': current_user.to_dict()
    })
