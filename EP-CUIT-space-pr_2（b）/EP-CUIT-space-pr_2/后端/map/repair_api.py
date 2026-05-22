from flask import Blueprint, request, jsonify
import pymysql
import json
from datetime import datetime
import os
import uuid

repair_bp = Blueprint('repair', __name__)

# 计算文件上传路径
BACKEND_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(BACKEND_ROOT)
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    return pymysql.connect(
        host='localhost',
        user='mapuser',
        password='123456',
        database='compus',
        charset='utf8mb4'
    )

@repair_bp.route('/repair/categories', methods=['GET'])
def get_categories():
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM repair_category ORDER BY repair_category_id")
        categories = cursor.fetchall()
        print(f"[DEBUG] Found {len(categories)} repair categories")
        return jsonify({'success': True, 'data': categories})
    except Exception as e:
        print(f"[ERROR] Failed to get repair categories: {e}")
        # 如果表不存在，返回默认分类
        default_categories = [
            {"repair_category_id": 1, "name": "基础设施", "icon": "🏗️", "description": "建筑设施维修"},
            {"repair_category_id": 2, "name": "电气设备", "icon": "🔌", "description": "电器设备维修"},
            {"repair_category_id": 3, "name": "环境卫生", "icon": "🧹", "description": "环境卫生问题"},
            {"repair_category_id": 4, "name": "其他", "icon": "📋", "description": "其他问题"}
        ]
        return jsonify({'success': True, 'data': default_categories})
    finally:
        cursor.close()
        db.close()

@repair_bp.route('/repair', methods=['POST'])
def create_repair():
    db = None
    cursor = None
    try:
        print(f"\n=== NEW REPAIR REQUEST ===")
        print(f"Content-Type: {request.content_type}")
        
        # 获取表单参数（优先从 form 获取）
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        repair_category_id = request.form.get("repair_category_id", "").strip()
        reporter_id = request.form.get("reporter_id", "").strip()
        priority = request.form.get("priority", "1")
        lng = request.form.get("lng", "").strip()
        lat = request.form.get("lat", "").strip()
        
        # 如果 form 中没有数据，尝试从 JSON body 获取
        if not title and request.data:
            try:
                data = json.loads(request.data.decode('utf-8'))
                title = str(data.get('title', '')).strip()
                description = str(data.get('description', '')).strip()
                repair_category_id = str(data.get('repair_category_id', '')).strip()
                reporter_id = str(data.get('reporter_id', '')).strip()
                priority = str(data.get('priority', '1'))
                lng = str(data.get('lng', '')).strip()
                lat = str(data.get('lat', '')).strip()
                print("Data loaded from JSON body")
            except Exception as e:
                print(f"Failed to parse JSON: {e}")
        
        print(f"Parsed values:")
        print(f"  title: '{title}'")
        print(f"  description: '{description}'")
        print(f"  repair_category_id: '{repair_category_id}'")
        print(f"  reporter_id: '{reporter_id}'")
        print(f"  priority: '{priority}'")
        print(f"  lng: '{lng}'")
        print(f"  lat: '{lat}'")
        
        # 参数校验
        if not title:
            return jsonify({'success': False, 'message': '缺少必要参数: title'}), 400
        if not description:
            return jsonify({'success': False, 'message': '缺少必要参数: description'}), 400
        if not repair_category_id:
            return jsonify({'success': False, 'message': '缺少必要参数: repair_category_id'}), 400
        if not reporter_id:
            return jsonify({'success': False, 'message': '缺少必要参数: reporter_id'}), 400

        # 连接数据库
        db = get_db()
        cursor = db.cursor()

        # 处理位置信息（参考 map_service.py 的实现）
        location_id = None
        if lng and lat:
            try:
                # 转换为 float 类型
                lng_float = float(lng)
                lat_float = float(lat)
                
                # 验证坐标范围（经度 -180 到 180，纬度 -90 到 90）
                if not (-180 <= lng_float <= 180) or not (-90 <= lat_float <= 90):
                    print(f"Invalid coordinates: lng={lng_float}, lat={lat_float}")
                else:
                    # 先查询是否已存在相同坐标
                    cursor.execute(
                        "SELECT location_id FROM location WHERE longitude = %s AND latitude = %s LIMIT 1", 
                        (lng_float, lat_float)
                    )
                    result = cursor.fetchone()
                    if result:
                        location_id = result[0]
                        print(f"Found existing location_id: {location_id}")
                    else:
                        # 插入新位置记录
                        cursor.execute(
                            "INSERT INTO location (name, longitude, latitude, detail) VALUES (%s, %s, %s, %s)", 
                            (title, lng_float, lat_float, description)
                        )
                        db.commit()
                        location_id = cursor.lastrowid
                        print(f"Created new location with location_id: {location_id}")
            except ValueError as e:
                print(f"Invalid coordinate format: {e}")
            except Exception as e:
                print(f"Location error: {e}")

        # 处理图片上传
        images_json = None
        if 'images' in request.files:
            uploaded_files = request.files.getlist('images')
            if uploaded_files:
                image_paths = []
                for file in uploaded_files:
                    if file and file.filename:
                        ext = os.path.splitext(file.filename)[1].lower()
                        if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                            # 使用 UUID 生成唯一文件名
                            filename = f"repair_{uuid.uuid4().hex}{ext}"
                            filepath = os.path.join(UPLOAD_FOLDER, filename)
                            file.save(filepath)
                            image_paths.append(f"/uploads/{filename}")
                if image_paths:
                    images_json = json.dumps(image_paths)

        # 插入报修记录
        sql = """
        INSERT INTO repair (title, description, repair_category_id, location_id, reporter_id, 
                           priority, images, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
        """
        cursor.execute(sql, (
            title,
            description,
            repair_category_id,
            location_id,
            reporter_id,
            priority,
            images_json
        ))
        db.commit()
        repair_id = cursor.lastrowid
        
        print(f"Repair created successfully: repair_id={repair_id}, location_id={location_id}")
        return jsonify({
            'success': True, 
            'repair_id': repair_id,
            'location_id': location_id
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        if db:
            db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@repair_bp.route('/repair', methods=['GET'])
def get_repairs():
    """
    获取所有报修标记列表
    
    查询数据库中所有报修记录，包含关联的位置信息，用于在地图上显示标记
    
    返回:
        JSON: 包含所有报修标记的列表，每个标记包含位置坐标
    """
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    
    try:
        print("[DEBUG] Starting get_repairs query...")
        # 查询所有报修信息及关联位置
        cursor.execute("""
            SELECT
                r.repair_id,
                r.title,
                r.description,
                r.repair_category_id,
                r.location_id,
                r.reporter_id,
                r.priority,
                r.images,
                r.status,
                r.create_time,
                r.update_time,
                rc.name AS category_name,
                l.longitude,
                l.latitude,
                l.name AS location_name,
                l.detail AS location_detail
            FROM repair r
            LEFT JOIN repair_category rc ON r.repair_category_id = rc.repair_category_id
            LEFT JOIN location l ON r.location_id = l.location_id
            ORDER BY r.create_time DESC
        """)
        data = cursor.fetchall()
        print(f"[DEBUG] Query returned {len(data)} records")

        # 处理每条记录（参考 map_service.py 的实现）
        result = []
        for idx, row in enumerate(data):
            print(f"[DEBUG] Processing row {idx}: repair_id={row.get('repair_id')}, title={row.get('title')}")
            print(f"[DEBUG] Location: longitude={row.get('longitude')}, latitude={row.get('latitude')}, location_id={row.get('location_id')}")
            
            # 解析图片URL列表
            image_urls = []
            if row.get("images"):
                try:
                    image_urls = json.loads(row["images"])
                except Exception as e:
                    print(f"[DEBUG] Failed to parse images: {e}")
                    image_urls = []

            # 组装单条记录（确保坐标为 float 类型）
            lng = float(row["longitude"]) if row["longitude"] else None
            lat = float(row["latitude"]) if row["latitude"] else None
            
            print(f"[DEBUG] Converted coordinates: lng={lng}, lat={lat}")
            
            result.append({
                "repair_id": row["repair_id"],
                "title": row["title"] or "未命名报修",
                "description": row["description"] or "",
                "repair_category_id": row["repair_category_id"],
                "category_name": row["category_name"],
                "location_id": row["location_id"],
                "reporter_id": row["reporter_id"],
                "priority": row["priority"] or 1,
                "images": image_urls,
                "status": row["status"] or 0,
                "create_time": row["create_time"].strftime("%Y-%m-%d %H:%M:%S") if row["create_time"] else "",
                "update_time": row["update_time"].strftime("%Y-%m-%d %H:%M:%S") if row["update_time"] else "",
                "lng": lng,
                "lat": lat,
                "location_name": row["location_name"],
                "location_detail": row["location_detail"] or ""
            })

        print(f"[DEBUG] Final result count: {len(result)}")
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        print(f"Error getting repairs: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        db.close()

@repair_bp.route('/repair/<int:repair_id>', methods=['GET'])
def get_repair(repair_id):
    """
    获取单个报修信息
    
    根据报修ID查询报修详情，包括关联的位置信息
    
    参数:
        repair_id (int): 报修ID
        
    返回:
        JSON: 包含报修详细信息和位置坐标
    """
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT
                r.repair_id,
                r.title,
                r.description,
                r.repair_category_id,
                r.location_id,
                r.reporter_id,
                r.priority,
                r.images,
                r.status,
                r.create_time,
                r.update_time,
                rc.name AS category_name,
                l.longitude,
                l.latitude,
                l.name AS location_name,
                l.detail AS location_detail
            FROM repair r
            LEFT JOIN repair_category rc ON r.repair_category_id = rc.repair_category_id
            LEFT JOIN location l ON r.location_id = l.location_id
            WHERE r.repair_id = %s
        """, (repair_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"success": False, "message": "报修记录不存在"}), 404

        # 解析图片URL列表
        image_urls = []
        if row.get("images"):
            try:
                image_urls = json.loads(row["images"])
            except:
                image_urls = []

        # 组装返回结果（确保坐标为 float 类型）
        result = {
            "repair_id": row["repair_id"],
            "title": row["title"] or "未命名报修",
            "description": row["description"] or "",
            "repair_category_id": row["repair_category_id"],
            "category_name": row["category_name"],
            "location_id": row["location_id"],
            "reporter_id": row["reporter_id"],
            "priority": row["priority"] or 1,
            "images": image_urls,
            "status": row["status"] or 0,
            "create_time": row["create_time"].strftime("%Y-%m-%d %H:%M:%S") if row["create_time"] else "",
            "update_time": row["update_time"].strftime("%Y-%m-%d %H:%M:%S") if row["update_time"] else "",
            "lng": float(row["longitude"]) if row["longitude"] else None,
            "lat": float(row["latitude"]) if row["latitude"] else None,
            "location_name": row["location_name"],
            "location_detail": row["location_detail"] or ""
        }

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        db.close()

@repair_bp.route('/repair/<int:repair_id>', methods=['PUT'])
def update_repair(repair_id):
    db = get_db()
    cursor = db.cursor()
    try:
        data = request.get_json()
        
        status = data.get('status')
        process_note = data.get('process_note')
        assignee_id = data.get('assignee_id')
        
        sql = "UPDATE repair SET "
        params = []
        
        if status is not None:
            sql += "status = %s, "
            params.append(status)
        if process_note is not None:
            sql += "process_note = %s, "
            params.append(process_note)
        if assignee_id is not None:
            sql += "assignee_id = %s, "
            params.append(assignee_id)
        
        sql = sql.rstrip(', ')
        sql += " WHERE repair_id = %s"
        params.append(repair_id)
        
        cursor.execute(sql, params)
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@repair_bp.route('/repair/<int:repair_id>', methods=['DELETE'])
def delete_repair(repair_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM repair WHERE repair_id = %s", (repair_id,))
        db.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': '报修记录不存在'}), 404
        
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()