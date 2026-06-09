from flask import Blueprint, jsonify, request
import pymysql
import json
from .db import get_db
from utils.cos_utils import cos_client

repair_list_bp = Blueprint('repair_list', __name__)


def get_signed_url(url_or_key):
    if not url_or_key:
        return None
    key = cos_client.normalize_key(url_or_key)
    if not key:
        return None
    try:
        return cos_client.get_presigned_url(key, expires=3600)
    except Exception as e:
        print(f"生成签名URL失败: {e}")
        return None


@repair_list_bp.route('/repair', methods=['GET'])
def get_repairs():
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    
    try:
        campus_id = request.args.get('campus_id')
        if campus_id:
            try:
                campus_id = int(campus_id)
            except ValueError:
                campus_id = None
        
        query = """
            SELECT DISTINCT
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
                l.detail AS location_detail,
                rc2.campus_id
            FROM repair r
            LEFT JOIN repair_category rc ON r.repair_category_id = rc.repair_category_id
            LEFT JOIN location l ON r.location_id = l.location_id
            JOIN repair_campus rc2 ON r.repair_id = rc2.repair_id
            WHERE r.status != 2
        """
        
        params = []
        if campus_id:
            query += " AND rc2.campus_id = %s"
            params.append(campus_id)
        
        query += " ORDER BY r.create_time DESC"
        
        cursor.execute(query, params)
        data = cursor.fetchall()

        result = []
        for row in data:
            image_urls = []
            if row.get("images"):
                try:
                    image_keys = json.loads(row["images"])
                    image_urls = [get_signed_url(key) for key in image_keys if key]
                except:
                    image_urls = []

            lng = float(row["longitude"]) if row["longitude"] else None
            lat = float(row["latitude"]) if row["latitude"] else None
            
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
                "location_detail": row["location_detail"] or "",
                "campus_id": row["campus_id"]
            })
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


@repair_list_bp.route('/repair/<int:repair_id>', methods=['GET'])
def get_repair(repair_id):
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

        image_urls = []
        if row.get("images"):
            try:
                image_keys = json.loads(row["images"])
                image_urls = [get_signed_url(key) for key in image_keys if key]
            except:
                image_urls = []

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
