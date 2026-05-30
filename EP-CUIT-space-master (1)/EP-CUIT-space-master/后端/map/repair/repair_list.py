from flask import Blueprint, jsonify
import pymysql
import json
from .db import get_db

repair_list_bp = Blueprint('repair_list', __name__)

@repair_list_bp.route('/repair', methods=['GET'])
def get_repairs():
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    
    try:
        print("[DEBUG] Starting get_repairs query...")
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

        result = []
        for idx, row in enumerate(data):
            print(f"[DEBUG] Processing row {idx}: repair_id={row.get('repair_id')}, title={row.get('title')}")
            print(f"[DEBUG] Location: longitude={row.get('longitude')}, latitude={row.get('latitude')}, location_id={row.get('location_id')}")
            
            image_urls = []
            if row.get("images"):
                try:
                    image_urls = json.loads(row["images"])
                except Exception as e:
                    print(f"[DEBUG] Failed to parse images: {e}")
                    image_urls = []

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
                image_urls = json.loads(row["images"])
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
