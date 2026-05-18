"""
地图服务模块 - 失物招领系统地图相关API

该模块提供地图配置、失物标记的增删查等功能，包括：
- 获取默认地图配置
- 查询单个失物信息
- 查询所有失物标记列表
- 删除失物标记
- 发布新的失物标记

数据库表关联关系：
- lost_item（失物表）通过 location_id 关联 location（位置表）
- 失物标记包含经纬度信息，用于在地图上显示
"""

from flask import Blueprint, jsonify, request
import pymysql
import os
import json
import uuid
from datetime import datetime

# 创建蓝图对象，用于注册路由
map_bp = Blueprint('map', __name__)

# 数据库连接配置
DB_CONFIG = {
    "host": "localhost",      # 数据库主机地址
    "user": "mapuser",        # 数据库用户名
    "password": "123456",     # 数据库密码
    "database": "compus",     # 数据库名称
    "charset": "utf8mb4"      # 字符编码（支持中文）
}

# 计算文件上传路径
BACKEND_ROOT = os.path.dirname(__file__)           # 后端代码目录
PROJECT_ROOT = os.path.dirname(BACKEND_ROOT)       # 项目根目录
IMAGE_UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads")  # 图片上传目录
os.makedirs(IMAGE_UPLOAD_FOLDER, exist_ok=True)    # 确保目录存在


def get_conn():
    """
    获取数据库连接
    
    返回:
        pymysql.connect: 数据库连接对象
    """
    return pymysql.connect(**DB_CONFIG)


@map_bp.route('/map/default', methods=['GET'])
def get_default_map():
    """
    获取默认地图配置
    
    从数据库查询地图配置，如果查询失败则返回默认配置
    
    返回:
        JSON: 包含地图中心点、边界和缩放级别的配置信息
    """
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # 查询地图配置表中的第一条记录
        cursor.execute("""
            SELECT
                name, center_lng, center_lat,
                sw_lng, sw_lat, ne_lng, ne_lat, zoom
            FROM map_config
            ORDER BY name ASC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            return jsonify(row)
    except Exception:
        pass
    finally:
        cursor.close()
        conn.close()

    # 返回默认配置（上海地区坐标）
    return jsonify({
        "name": "default",
        "center_lng": 121.4737,
        "center_lat": 31.2304,
        "sw_lng": 121.4637,
        "sw_lat": 31.2204,
        "ne_lng": 121.4837,
        "ne_lat": 31.2404,
        "zoom": 18
    })


@map_bp.route('/lost-items/<int:item_id>', methods=['GET'])
def get_lost_item(item_id):
    """
    获取单个失物信息
    
    根据物品ID查询失物详情，包括关联的位置信息
    
    参数:
        item_id (int): 物品ID
        
    返回:
        JSON: 包含物品详细信息和位置坐标
    """
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # 查询失物信息及关联的位置信息
        cursor.execute("""
            SELECT
                li.item_id,
                li.title,
                li.description,
                li.type,
                li.category_id,
                li.status,
                li.image_urls,
                li.publisher_id,
                li.location_id,
                li.create_time,
                li.update_time,
                l.location_id AS loc_id,
                l.name AS location_name,
                l.longitude,
                l.latitude,
                l.detail AS location_detail
            FROM lost_item li
            LEFT JOIN location l ON li.location_id = l.location_id
            WHERE li.item_id = %s
        """, (item_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"success": False, "message": "物品不存在"}), 404

        # 解析图片URL列表
        image_urls = []
        if row.get("image_urls"):
            try:
                image_urls = json.loads(row["image_urls"])
            except:
                image_urls = []

        # 组装返回结果
        result = {
            "item_id": row["item_id"],
            "title": row["title"] or "未命名物品",
            "description": row["description"] or "",
            "type": row["type"] or 0,
            "category_id": row["category_id"],
            "status": row["status"] or 0,
            "image_urls": image_urls,
            "publisher_id": row["publisher_id"],
            "location_id": row["location_id"],
            "create_time": row["create_time"].strftime("%Y-%m-%d %H:%M:%S") if row["create_time"] else "",
            "update_time": row["update_time"].strftime("%Y-%m-%d %H:%M:%S") if row["update_time"] else "",
            "location_name": row["location_name"],
            "lng": row["longitude"],
            "lat": row["latitude"],
            "location_detail": row["location_detail"] or ""
        }

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"获取物品信息失败: {e}")
        return jsonify({"success": False, "message": "获取物品信息失败"}), 500
    finally:
        cursor.close()
        conn.close()


@map_bp.route('/map/markers', methods=['GET'])
def get_markers():
    """
    获取所有失物标记列表
    
    查询数据库中所有失物记录，包含关联的位置信息，用于在地图上显示标记
    
    返回:
        JSON: 包含所有失物标记的列表，每个标记包含位置坐标
    """
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # 查询所有失物信息及关联位置
        cursor.execute("""
            SELECT
                li.item_id,
                li.title,
                li.description,
                li.type,
                li.category_id,
                li.status,
                li.image_urls,
                li.publisher_id,
                li.location_id,
                li.create_time,
                li.update_time,
                l.location_id AS loc_id,
                l.name AS location_name,
                l.longitude,
                l.latitude,
                l.detail AS location_detail
            FROM lost_item li
            LEFT JOIN location l ON li.location_id = l.location_id
            ORDER BY li.create_time DESC
        """)
        data = cursor.fetchall()

        # 处理每条记录
        result = []
        for row in data:
            # 解析图片URL列表
            image_urls = []
            if row.get("image_urls"):
                try:
                    image_urls = json.loads(row["image_urls"])
                except:
                    image_urls = []

            # 组装单条记录
            result.append({
                "item_id": row["item_id"],
                "title": row["title"] or "未命名物品",
                "description": row["description"] or "",
                "type": row["type"] or 0,
                "category_id": row["category_id"],
                "status": row["status"] or 0,
                "image_urls": image_urls,
                "publisher_id": row["publisher_id"],
                "location_id": row["location_id"],
                "create_time": row["create_time"].strftime("%Y-%m-%d %H:%M:%S") if row["create_time"] else "",
                "update_time": row["update_time"].strftime("%Y-%m-%d %H:%M:%S") if row["update_time"] else "",
                "location_name": row["location_name"],
                "lng": row["longitude"],
                "lat": row["latitude"],
                "location_detail": row["location_detail"] or ""
            })

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@map_bp.route('/map/delete-marker/<int:item_id>', methods=['DELETE'])
def delete_marker(item_id):
    """
    删除失物标记
    
    根据物品ID删除对应的失物记录
    
    参数:
        item_id (int): 物品ID
        
    返回:
        JSON: 删除结果状态
    """
    conn = get_conn()
    cursor = conn.cursor()

    try:
        # 执行删除操作
        cursor.execute("DELETE FROM lost_item WHERE item_id = %s", (item_id,))
        conn.commit()

        # 根据受影响行数判断是否删除成功
        if cursor.rowcount > 0:
            return jsonify({"success": True, "message": "删除成功"})
        else:
            return jsonify({"success": False, "message": "物品不存在"}), 404
    except Exception as e:
        logger.error(f"删除物品失败: {e}")
        return jsonify({"success": False, "message": "删除失败"}), 500
    finally:
        cursor.close()
        conn.close()


@map_bp.route('/map/publish', methods=['POST'])
def publish_marker():
    """
    发布新的失物标记
    
    处理用户提交的失物招领信息，包括图片上传和位置信息存储
    
    请求参数（FormData格式）:
        title: 物品标题
        detail: 物品描述
        phone: 联系电话
        user_id: 用户ID
        lng: 经度
        lat: 纬度
        status: 状态（0=失物，1=拾物）
        category_id: 分类ID
        images: 图片文件列表（可选）
    
    返回:
        JSON: 发布结果，包含新建物品的ID和位置ID
    """
    conn = None
    cursor = None
    try:
        # 获取表单参数
        title = request.form.get("title", "").strip()
        detail = request.form.get("detail", "").strip()
        phone = request.form.get("phone", "").strip()
        user_id = request.form.get("user_id")
        lng = request.form.get("lng")
        lat = request.form.get("lat")
        status = int(request.form.get("status", 0))
        category_id = int(request.form.get("category_id", 1))

        # 参数校验
        if not title or not detail:
            return jsonify({"success": False, "message": "标题和描述不能为空"}), 400

        if not user_id:
            return jsonify({"success": False, "message": "用户ID不能为空"}), 400

        # 处理图片上传
        image_urls = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename:
                    # 验证文件扩展名
                    ext = os.path.splitext(file.filename)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                        # 生成唯一文件名并保存
                        filename = f"{uuid.uuid4().hex}{ext}"
                        filepath = os.path.join(IMAGE_UPLOAD_FOLDER, filename)
                        file.save(filepath)
                        image_urls.append(f"/uploads/{filename}")

        # 连接数据库
        conn = get_conn()
        cursor = conn.cursor()

        # 插入位置信息（如果有经纬度）
        location_id = None
        if lng and lat:
            try:
                lng = float(lng)
                lat = float(lat)
                cursor.execute("""
                    INSERT INTO location (name, longitude, latitude, detail)
                    VALUES (%s, %s, %s, %s)
                """, (title, lng, lat, detail))
                location_id = cursor.lastrowid
            except Exception as loc_err:
                print(f"位置插入失败: {loc_err}")
                location_id = None

        # 根据状态确定类型（0=失物，1=拾物）
        type_value = 1 if status == 1 else 0

        # 插入失物记录
        cursor.execute("""
            INSERT INTO lost_item (title, description, type, category_id, status,
                                  image_urls, publisher_id, location_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            title,
            detail,
            type_value,
            category_id,
            status,
            json.dumps(image_urls),
            user_id,
            location_id
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "发布成功",
            "data": {
                "item_id": cursor.lastrowid,
                "location_id": location_id
            }
        })

    except Exception as e:
        # 发生异常时回滚事务
        if conn:
            conn.rollback()
        print(f"发布失败: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        # 确保资源释放
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@map_bp.route('/map/update-status/<item_id>', methods=['POST'])
def update_item_status(item_id):
    """
    更新物品状态
    
    根据物品ID更新失物状态（已找到/已归还）
    
    参数:
        item_id (int): 物品ID
        
    请求体（JSON格式）:
        status: 新状态（0=未找到/未被认领，1=已找到/已被认领）
        user_id: 用户ID
        
    返回:
        JSON: 更新结果状态
    """
    conn = None
    cursor = None
    try:
        status = int(request.json.get("status", 1))
        user_id = request.json.get("user_id")

        if not user_id:
            return jsonify({"success": False, "message": "用户ID不能为空"}), 400

        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT type FROM lost_item 
            WHERE item_id = %s AND publisher_id = %s
        """, (item_id, user_id))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({"success": False, "message": "物品不存在或无权限操作"}), 403

        cursor.execute("""
            UPDATE lost_item 
            SET status = %s, update_time = %s
            WHERE item_id = %s
        """, (status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), item_id))
        
        conn.commit()
        
        return jsonify({"success": True, "message": "状态更新成功"})
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"更新状态失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()