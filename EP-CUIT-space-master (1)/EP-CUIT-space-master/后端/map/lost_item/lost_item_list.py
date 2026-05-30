from flask import Blueprint, jsonify, request
import pymysql
import json
from .. import get_conn

lost_item_list_bp = Blueprint('lost_item_list', __name__)

@lost_item_list_bp.route('/lost-items/<int:item_id>', methods=['GET'])
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

        lng = float(row["longitude"]) if row["longitude"] else None
        lat = float(row["latitude"]) if row["latitude"] else None
        
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
            "lng": lng,
            "lat": lat,
            "location_detail": row["location_detail"] or ""
        }

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({"success": False, "message": "获取物品信息失败"}), 500
    finally:
        cursor.close()
        conn.close()


@lost_item_list_bp.route('/map/markers', methods=['GET'])
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

            lng = float(row["longitude"]) if row["longitude"] else None
            lat = float(row["latitude"]) if row["latitude"] else None
            
            if lng is None or lat is None:
                continue
            
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
                "lng": lng,
                "lat": lat,
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


@lost_item_list_bp.route('/map/categories', methods=['GET'])
def get_categories():
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(
            host="localhost",
            user="mapuser",
            password="123456",
            database="compus",
            charset="utf8mb4"
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT category_id as id, name FROM category ORDER BY category_id")
        categories = cursor.fetchall()
        
        return jsonify({
            "success": True,
            "data": categories
        })
    except pymysql.Error as e:
        error_msg = f"数据库错误: {e.args[0]} - {e.args[1]}"
        return jsonify({"success": False, "message": error_msg}), 500
    except Exception as e:
        error_msg = f"服务器错误: {str(e)}"
        return jsonify({"success": False, "message": error_msg}), 500
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass
