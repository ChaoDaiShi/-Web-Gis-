from flask import Blueprint, request, jsonify, current_app
from models import User, db
from utils.validators import token_required, create_verification, verify_code

# 创建密码相关的蓝图
password_bp = Blueprint('password', __name__, url_prefix='/api/password')

@password_bp.route('/send-code', methods=['POST'])
@token_required
def send_verification_code(current_user):
    """发送密码修改验证码接口
    
    请求参数:
        email: 邮箱（必须与当前账号匹配）
    
    返回:
        成功: {"success": true, "message": "验证码已发送到您的邮箱", "data": {"expires_in": 600}}
        失败: {"success": false, "message": "错误信息"}
    """
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '请求数据无效'}), 400

    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'success': False, 'message': '邮箱不能为空'}), 400

    if email != current_user.email:
        return jsonify({'success': False, 'message': '邮箱与当前账号不匹配'}), 400

    # 生成验证码
    code = create_verification(email=email, code_type='password_change')

    # 实际项目中应该发送邮件，这里仅打印验证码
    print(f"Password change verification code for {email}: {code}")

    return jsonify({
        'success': True,
        'message': '验证码已发送到您的邮箱',
        'data': {
            'expires_in': 600  # 10分钟过期
        }
    })

@password_bp.route('/reset', methods=['POST'])
@token_required
def reset_password(current_user):
    """重置密码接口
    
    请求参数:
        email: 邮箱（必须与当前账号匹配）
        new_password: 新密码
        confirm_password: 确认新密码
        code: 验证码
    
    返回:
        成功: {"success": true, "message": "密码修改成功"}
        失败: {"success": false, "message": "错误信息"}
    """
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '请求数据无效'}), 400

    email = data.get('email', '').strip().lower()
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    code = data.get('code', '')

    if not all([email, new_password, confirm_password, code]):
        return jsonify({'success': False, 'message': '所有字段都不能为空'}), 400

    if email != current_user.email:
        return jsonify({'success': False, 'message': '邮箱与当前账号不匹配'}), 400

    if new_password != confirm_password:
        return jsonify({'success': False, 'message': '两次输入的新密码不一致'}), 400

    if len(new_password) < 6:
        return jsonify({'success': False, 'message': '密码长度不能少于6位'}), 400

    # 验证验证码
    valid, message = verify_code(email=email, code=code, code_type='password_change')
    if not valid:
        return jsonify({'success': False, 'message': message}), 400

    # 更新密码
    current_user.set_password(new_password)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '密码修改成功'
    })
