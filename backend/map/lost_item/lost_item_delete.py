from flask import Blueprint, jsonify
from .. import get_conn

lost_item_delete_bp = Blueprint('lost_item_delete', __name__)

@lost_item_delete_bp.route('/map/delete-marker/<int:item_id>', methods=['DELETE'])
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
        return jsonify({"success": False, "message": "删除失败"}), 500
    finally:
        cursor.close()
        conn.close()
