from flask import Blueprint, jsonify, request
import pymysql
from datetime import datetime

map_bp = Blueprint('map', __name__)

# ================== 数据库配置 ==================
DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}


def get_conn():
    return pymysql.connect(**DB_CONFIG)


# ================== 0. 地图默认配置 ==================
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


# ================== 1. 获取地图标记（location表） ==================
@map_bp.route('/map/markers', methods=['GET'])
def get_markers():
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        cursor.execute("""
            SELECT
                location_id,
                name,
                longitude AS lng,
                latitude AS lat
            FROM location
            ORDER BY location_id DESC
        """)
        data = cursor.fetchall()

        for row in data:
            row["title"] = row.get("name") or "未命名标记"
            row["description"] = ""
            row["status"] = 0
            row["create_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ================== 2. 发布标记（写入location表） ==================
@map_bp.route('/map/publish', methods=['POST'])
def publish_marker():
    data = request.get_json() or {}

    title = data.get("title", "").strip()
    lat = data.get("lat")
    lng = data.get("lng")

    if not all([title, lat, lng]):
        return jsonify({"success": False, "message": "参数缺失"}), 400

    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO location (name, longitude, latitude)
            VALUES (%s, %s, %s)
        """, (title, lng, lat))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "发布成功"
        })

    except Exception as e:
        conn.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        cursor.close()
        conn.close()
