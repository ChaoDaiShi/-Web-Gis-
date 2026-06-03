from flask import Blueprint, jsonify, request
import pymysql
import os
import json
import uuid
from .. import get_conn, BACKEND_ROOT

lost_item_publish_bp = Blueprint('lost_item_publish', __name__)

IMAGE_UPLOAD_FOLDER = os.path.join(BACKEND_ROOT, "..", "images", "lost_items")
os.makedirs(IMAGE_UPLOAD_FOLDER, exist_ok=True)

@lost_item_publish_bp.route('/map/publish', methods=['POST'])
def publish_marker():
    conn = None
    cursor = None
    try:
        title = request.form.get("title", "").strip()
        detail = request.form.get("detail", "").strip()
        phone = request.form.get("phone", "").strip()
        user_id = request.form.get("user_id")
        lng = request.form.get("lng")
        lat = request.form.get("lat")
        status = int(request.form.get("status", 0))
        category_id = int(request.form.get("category_id", 1))
        campus_id = request.form.get("campus_id")

        if not title or not detail:
            return jsonify({"success": False, "message": "标题和描述不能为空"}), 400

        if not user_id:
            return jsonify({"success": False, "message": "用户ID不能为空"}), 400

        image_urls = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename:
                    ext = os.path.splitext(file.filename)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                        filename = f"{uuid.uuid4().hex}{ext}"
                        filepath = os.path.join(IMAGE_UPLOAD_FOLDER, filename)
                        file.save(filepath)
                        image_urls.append(f"/images/lost_items/{filename}")

        conn = get_conn()
        cursor = conn.cursor()

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

        type_value = int(request.form.get("type", 0))

        cursor.execute("""
            INSERT INTO lost_item (title, description, type, category_id, status,
                                  image_urls, publisher_id, location_id, audit_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
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
        
        item_id = cursor.lastrowid
        
        # 如果提供了校区ID，创建物品-校区关联
        if campus_id:
            try:
                campus_id = int(campus_id)
                cursor.execute("""
                    INSERT INTO item_campus (item_id, campus_id)
                    VALUES (%s, %s)
                """, (item_id, campus_id))
            except Exception as campus_err:
                print(f"校区关联设置失败: {campus_err}")

        conn.commit()

        return jsonify({
            "success": True,
            "message": "发布成功，等待管理员审核",
            "data": {
                "item_id": item_id,
                "location_id": location_id,
                "campus_id": campus_id
            }
        })

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"发布失败: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
