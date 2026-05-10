from flask import Blueprint, jsonify, request
import pymysql
import os
import json
import uuid
from datetime import datetime

map_bp = Blueprint('map', __name__)

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

BACKEND_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(BACKEND_ROOT)
IMAGE_UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads")
os.makedirs(IMAGE_UPLOAD_FOLDER, exist_ok=True)

def get_conn():
    return pymysql.connect(**DB_CONFIG)


@map_bp.route('/map/default', methods=['GET'])
def get_default_map():
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
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
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
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

        image_urls = []
        if row.get("image_urls"):
            try:
                image_urls = json.loads(row["image_urls"])
            except:
                image_urls = []

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
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
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

        result = []
        for row in data:
            image_urls = []
            if row.get("image_urls"):
                try:
                    image_urls = json.loads(row["image_urls"])
                except:
                    image_urls = []

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
    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM lost_item WHERE item_id = %s", (item_id,))
        conn.commit()

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
                        image_urls.append(f"/uploads/{filename}")

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

        type_value = 1 if status == 1 else 0

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