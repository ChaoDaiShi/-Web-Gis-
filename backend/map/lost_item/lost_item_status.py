from flask import Blueprint, jsonify, request
from datetime import datetime
from .. import get_conn

lost_item_status_bp = Blueprint('lost_item_status', __name__)

@lost_item_status_bp.route('/map/update-status/<item_id>', methods=['POST'])
def update_item_status(item_id):
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
