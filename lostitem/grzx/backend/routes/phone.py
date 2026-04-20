from flask import Blueprint, request, jsonify
from models import User, db
from utils.validators import token_required, create_verification, verify_code

# 创建手机号相关的蓝图
phone_bp = Blueprint('phone', __name__, url_prefix='/api/phone')

@phone_bp.route('/send-code', methods=['POST'])
@token_required
def send_verification_code(current_user):
    """发送手机验证码接口
    
    请求参数:
        phone: 手机号
    
    返回:
        成功: {"success": true, "message": "验证码已发送", "data": {"expires_in": 600}}
        失败: {"success": false, "message": "错误信息"}
    """
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '请求数据无效'}), 400

    phone = data.get('phone', '').strip()

    if not phone:
        return jsonify({'success': False, 'message': '手机号不能为空'}), 400

    if not phone.startswith('1') or len(phone) != 11:
        return jsonify({'success': False, 'message': '手机号格式不正确'}), 400

    # 检查手机号是否已被其他用户绑定
    existing = User.query.filter_by(phone=phone).first()
    if existing and existing.id != current_user.id:
        return jsonify({'success': False, 'message': '该手机号已被其他账号绑定'}), 409

    # 生成验证码
    code = create_verification(phone=phone, code_type='phone_bind')

    # 实际项目中应该发送短信，这里仅打印验证码
    print(f"Phone binding verification code for {phone}: {code}")

    return jsonify({
        'success': True,
        'message': '验证码已发送',
        'data': {
            'expires_in': 600  # 10分钟过期
        }
    })

@phone_bp.route('/bind', methods=['POST'])
@token_required
def bind_phone(current_user):
    """绑定手机号接口
    
    请求参数:
        phone: 手机号
        code: 验证码
    
    返回:
        成功: {"success": true, "message": "手机号绑定成功", "data": {"phone": "..."}}
        失败: {"success": false, "message": "错误信息"}
    """
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '请求数据无效'}), 400

    phone = data.get('phone', '').strip()
    code = data.get('code', '')

    if not phone or not code:
        return jsonify({'success': False, 'message': '手机号和验证码都不能为空'}), 400

    if not phone.startswith('1') or len(phone) != 11:
        return jsonify({'success': False, 'message': '手机号格式不正确'}), 400

    # 检查手机号是否已被其他用户绑定
    existing = User.query.filter_by(phone=phone).first()
    if existing and existing.id != current_user.id:
        return jsonify({'success': False, 'message': '该手机号已被其他账号绑定'}), 409

    # 验证验证码
    valid, message = verify_code(phone=phone, code=code, code_type='phone_bind')
    if not valid:
        return jsonify({'success': False, 'message': message}), 400

    # 绑定手机号
    current_user.phone = phone
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '手机号绑定成功',
        'data': {
            'phone': phone
        }
    })

@phone_bp.route('/unbind', methods=['POST'])
@token_required
def unbind_phone(current_user):
    """解绑手机号接口
    
    请求参数:
        code: 验证码
    
    返回:
        成功: {"success": true, "message": "手机号解绑成功"}
        失败: {"success": false, "message": "错误信息"}
    """
    if not current_user.phone:
        return jsonify({'success': False, 'message': '当前账号未绑定手机号'}), 400

    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '请求数据无效'}), 400

    code = data.get('code', '')

    if not code:
        return jsonify({'success': False, 'message': '验证码不能为空'}), 400

    # 验证验证码
    valid, message = verify_code(phone=current_user.phone, code=code, code_type='phone_unbind')
    if not valid:
        return jsonify({'success': False, 'message': message}), 400

    # 解绑手机号
    current_user.phone = None
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '手机号解绑成功'
    })
