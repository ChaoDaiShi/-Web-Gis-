# 导入必要的库
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
import os
from datetime import datetime
import uuid
from PIL import Image
import base64
from io import BytesIO
import pymysql

# 创建Flask应用实例
app = Flask(__name__)

# 配置数据库连接 - MySQL
# 格式: mysql+pymysql://用户名:密码@主机:端口/数据库名
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost:3306/lostitem'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 配置图片上传目录
app.config['UPLOAD_FOLDER'] = 'uploads'

# 创建上传目录（如果不存在）
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 启用CORS（跨域资源共享）
CORS(app)

# 初始化数据库
db = SQLAlchemy(app)

# 初始化数据库迁移
migrate = Migrate(app, db)

# 数据库模型定义

class Item(db.Model):
    """失物模型"""
    # 主键，使用UUID生成唯一ID
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # 失物名称
    name = db.Column(db.String(100), nullable=False)
    # 失物类别
    category = db.Column(db.String(50), nullable=False)
    # 拾获地点
    location = db.Column(db.String(200), nullable=False)
    # 拾获时间
    found_time = db.Column(db.DateTime, nullable=False)
    # 失物特征描述
    description = db.Column(db.Text, nullable=False)
    # 失物照片路径
    image_path = db.Column(db.String(200), nullable=True)
    # 失物状态，默认为"待认领"
    status = db.Column(db.String(20), default='待认领')
    # 创建时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ClaimRequest(db.Model):
    """认领申请模型"""
    # 主键，使用UUID生成唯一ID
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # 关联的失物ID
    item_id = db.Column(db.String(36), db.ForeignKey('item.id'), nullable=False)
    # 丢失时间
    lost_time = db.Column(db.DateTime, nullable=False)
    # 丢失地点
    lost_location = db.Column(db.String(200), nullable=False)
    # 物品详细特征
    item_features = db.Column(db.Text, nullable=False)
    # 联系方式
    contact_info = db.Column(db.String(200), nullable=False)
    # 物品旧照片路径
    old_image_path = db.Column(db.String(200), nullable=True)
    # 申请状态，默认为"待处理"
    status = db.Column(db.String(20), default='待处理')
    # 创建时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 关联失物对象
    item = db.relationship('Item', backref=db.backref('claim_requests', lazy=True))

# 辅助函数

def save_image(base64_str, filename):
    """
    保存base64编码的图片
    
    Args:
        base64_str: base64编码的图片字符串
        filename: 保存的文件名
    
    Returns:
        保存成功返回图片路径，失败返回None
    """
    try:
        # 移除base64前缀（如果有）
        if base64_str.startswith('data:image/'):
            base64_str = base64_str.split(',')[1]
        
        # 解码base64字符串为二进制数据
        img_data = base64.b64decode(base64_str)
        # 打开图片
        img = Image.open(BytesIO(img_data))
        
        # 构建保存路径
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # 保存图片
        img.save(img_path)
        return img_path
    except Exception as e:
        print(f"保存图片失败: {e}")
        return None

# API接口定义

@app.route('/api/items', methods=['POST'])
def create_item():
    """
    失物发布API
    
    接收失物信息并保存到数据库
    """
    try:
        # 获取请求数据
        data = request.json
        
        # 生成唯一文件名
        image_filename = f"{uuid.uuid4()}.jpg"
        image_path = None
        
        # 如果有图片，保存图片
        if 'image' in data:
            image_path = save_image(data['image'], image_filename)
        
        # 创建失物记录
        new_item = Item(
            name=data['name'],
            category=data['category'],
            location=data['location'],
            found_time=datetime.fromisoformat(data['found_time']),
            description=data['description'],
            image_path=image_path,
            status='待认领'  # 初始状态为待认领
        )
        
        # 添加到数据库会话
        db.session.add(new_item)
        # 提交事务
        db.session.commit()
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'item': {
                'id': new_item.id,
                'name': new_item.name,
                'category': new_item.category,
                'location': new_item.location,
                'found_time': new_item.found_time.isoformat(),
                'description': new_item.description,
                'image_path': new_item.image_path,
                'status': new_item.status,
                'created_at': new_item.created_at.isoformat()
            }
        }), 201
    except Exception as e:
        # 返回错误响应
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/items', methods=['GET'])
def get_items():
    """
    失物查询和筛选API
    
    支持分类筛选和关键词搜索
    """
    try:
        # 获取查询参数
        category = request.args.get('category')
        keyword = request.args.get('keyword')
        
        # 构建查询
        query = Item.query
        
        # 分类筛选
        if category:
            query = query.filter_by(category=category)
        
        # 关键词搜索（搜索名称、描述、地点）
        if keyword:
            query = query.filter(
                (Item.name.contains(keyword)) |
                (Item.description.contains(keyword)) |
                (Item.location.contains(keyword))
            )
        
        # 只显示待认领的物品
        query = query.filter_by(status='待认领')
        
        # 执行查询
        items = query.all()
        
        # 构建响应数据
        result = []
        for item in items:
            result.append({
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'location': item.location,
                'found_time': item.found_time.isoformat(),
                'description': item.description,
                'image_path': item.image_path,
                'status': item.status,
                'created_at': item.created_at.isoformat()
            })
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'items': result
        }), 200
    except Exception as e:
        # 返回错误响应
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/items/<item_id>', methods=['GET'])
def get_item(item_id):
    """
    失物详情API
    
    根据ID获取失物详细信息
    """
    try:
        # 根据ID查询失物
        item = Item.query.get(item_id)
        if not item:
            return jsonify({'success': False, 'error': '失物不存在'}), 404
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'item': {
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'location': item.location,
                'found_time': item.found_time.isoformat(),
                'description': item.description,
                'image_path': item.image_path,
                'status': item.status,
                'created_at': item.created_at.isoformat()
            }
        }), 200
    except Exception as e:
        # 返回错误响应
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/claims', methods=['POST'])
def create_claim():
    """
    认领申请API
    
    提交认领申请信息
    """
    try:
        # 获取请求数据
        data = request.json
        
        # 检查失物是否存在
        item = Item.query.get(data['item_id'])
        if not item:
            return jsonify({'success': False, 'error': '失物不存在'}), 404
        
        # 检查失物是否已被认领
        if item.status != '待认领':
            return jsonify({'success': False, 'error': '该失物已被认领'}), 400
        
        # 生成唯一文件名
        old_image_filename = f"claim_{uuid.uuid4()}.jpg"
        old_image_path = None
        
        # 如果有旧照片，保存图片
        if 'old_image' in data:
            old_image_path = save_image(data['old_image'], old_image_filename)
        
        # 创建认领申请
        new_claim = ClaimRequest(
            item_id=data['item_id'],
            lost_time=datetime.fromisoformat(data['lost_time']),
            lost_location=data['lost_location'],
            item_features=data['item_features'],
            contact_info=data['contact_info'],
            old_image_path=old_image_path,
            status='待处理'  # 初始状态为待处理
        )
        
        # 添加到数据库会话
        db.session.add(new_claim)
        # 提交事务
        db.session.commit()
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'claim': {
                'id': new_claim.id,
                'item_id': new_claim.item_id,
                'lost_time': new_claim.lost_time.isoformat(),
                'lost_location': new_claim.lost_location,
                'item_features': new_claim.item_features,
                'contact_info': new_claim.contact_info,
                'old_image_path': new_claim.old_image_path,
                'status': new_claim.status,
                'created_at': new_claim.created_at.isoformat()
            }
        }), 201
    except Exception as e:
        # 返回错误响应
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/claims', methods=['GET'])
def get_claims():
    """
    获取认领申请列表API
    
    获取所有认领申请信息
    """
    try:
        # 查询所有认领申请
        claims = ClaimRequest.query.all()
        
        # 构建响应数据
        result = []
        for claim in claims:
            result.append({
                'id': claim.id,
                'item_id': claim.item_id,
                'item_name': claim.item.name,  # 获取关联的失物名称
                'lost_time': claim.lost_time.isoformat(),
                'lost_location': claim.lost_location,
                'item_features': claim.item_features,
                'contact_info': claim.contact_info,
                'old_image_path': claim.old_image_path,
                'status': claim.status,
                'created_at': claim.created_at.isoformat()
            })
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'claims': result
        }), 200
    except Exception as e:
        # 返回错误响应
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/claims/<claim_id>', methods=['PUT'])
def process_claim(claim_id):
    """
    处理认领申请API
    
    更新认领申请状态，同意认领时更新失物状态
    """
    try:
        # 获取请求数据
        data = request.json
        # 根据ID查询认领申请
        claim = ClaimRequest.query.get(claim_id)
        
        if not claim:
            return jsonify({'success': False, 'error': '认领申请不存在'}), 404
        
        # 更新认领申请状态
        claim.status = data['status']
        
        # 如果同意认领，更新失物状态为已认领
        if data['status'] == '已同意':
            item = Item.query.get(claim.item_id)
            if item:
                item.status = '已认领'
        
        # 提交事务
        db.session.commit()
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'claim': {
                'id': claim.id,
                'status': claim.status
            }
        }), 200
    except Exception as e:
        # 返回错误响应
        return jsonify({'success': False, 'error': str(e)}), 400

# 初始化数据库
with app.app_context():
    db.create_all()

# 主函数
if __name__ == '__main__':
    # 启动Flask应用
    # debug=True 启用调试模式
    # host='0.0.0.0' 允许所有IP访问
    # port=5000 指定端口为5000
    app.run(debug=True, host='0.0.0.0', port=5000)
