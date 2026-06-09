from flask import Blueprint, jsonify, request
import pymysql
import json
from .. import get_conn
from utils.cos_utils import cos_client

lost_item_list_bp = Blueprint('lost_item_list', __name__)


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


@lost_item_list_bp.route('/lost-items/<int:item_id>', methods=['GET'])
def get_lost_item(item_id):
    viewer_id = request.args.get('viewer_id')
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        base_sql = """
            SELECT
                li.item_id,
                li.title,
                li.description,
                li.type,
                li.category_id,
                li.status,
                li.audit_status,
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
        """
        
        if viewer_id:
            try:
                viewer_id_int = int(viewer_id)
                sql = base_sql + " AND (li.audit_status = 'approved' OR (li.audit_status = 'pending' AND li.publisher_id = %s))"
                params = (item_id, viewer_id_int)
            except (ValueError, TypeError):
                sql = base_sql + " AND li.audit_status = 'approved'"
                params = (item_id,)
        else:
            sql = base_sql + " AND li.audit_status = 'approved'"
            params = (item_id,)

        cursor.execute(sql, params)
        row = cursor.fetchone()

        if not row:
            return jsonify({"success": False, "message": "物品不存在"}), 404

        image_urls = []
        if row.get("image_urls"):
            try:
                image_keys = json.loads(row["image_urls"])
                image_urls = [get_signed_url(key) for key in image_keys if key]
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
            "audit_status": row.get("audit_status") or "pending",
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
    
    campus_id = request.args.get('campus_id', None)
    viewer_id = request.args.get('viewer_id')
    
    base_sql = """
        SELECT DISTINCT
            li.item_id,
            li.title,
            li.description,
            li.type,
            li.category_id,
            li.status,
            li.audit_status,
            li.image_urls,
            li.publisher_id,
            li.location_id,
            li.create_time,
            li.update_time,
            ic.campus_id,
            l.location_id AS loc_id,
            l.name AS location_name,
            l.longitude,
            l.latitude,
            l.detail AS location_detail
        FROM lost_item li
        LEFT JOIN item_campus ic ON li.item_id = ic.item_id
        LEFT JOIN location l ON li.location_id = l.location_id
        WHERE
    """
    
    params = []
    conditions = []
    
    if campus_id:
        conditions.append("ic.campus_id = %s")
        params.append(campus_id)
        base_sql = base_sql.replace("LEFT JOIN item_campus", "INNER JOIN item_campus")
    
    try:
        viewer_id_int = int(viewer_id) if viewer_id else None
    except (ValueError, TypeError):
        viewer_id_int = None
    
    if viewer_id_int:
        conditions.append("(li.audit_status = 'approved' OR (li.audit_status = 'pending' AND li.publisher_id = %s))")
        params.append(viewer_id_int)
    else:
        conditions.append("li.audit_status = 'approved'")
    
    sql = base_sql + " AND ".join(conditions) + " ORDER BY li.create_time DESC"
    
    try:
        print(f"[get_markers] 查询条件: campus_id={campus_id}, viewer_id={viewer_id}")
        cursor.execute(sql, tuple(params))
        data = cursor.fetchall()
        
        print(f"[get_markers] 查询结果: 共 {len(data)} 条记录")
        if data:
            print(f"[get_markers] 示例数据: item_id={data[0]['item_id']}, title={data[0]['title']}, audit_status={data[0].get('audit_status')}, publisher_id={data[0]['publisher_id']}")

        result = []
        for row in data:
            image_urls = []
            if row.get("image_urls"):
                try:
                    image_keys = json.loads(row["image_urls"])
                    image_urls = [get_signed_url(key) for key in image_keys if key]
                except:
                    image_urls = []

            lng = float(row["longitude"]) if row["longitude"] else None
            lat = float(row["latitude"]) if row["latitude"] else None
            
            result.append({
                "item_id": row["item_id"],
                "title": row["title"] or "未命名物品",
                "description": row["description"] or "",
                "type": row["type"] or 0,
                "category_id": row["category_id"],
                "status": row["status"] or 0,
                "audit_status": row.get("audit_status") or "pending",
                "image_urls": image_urls,
                "publisher_id": row["publisher_id"],
                "location_id": row["location_id"],
                "campus_id": row.get("campus_id"),
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
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT id, name FROM category ORDER BY id")
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
