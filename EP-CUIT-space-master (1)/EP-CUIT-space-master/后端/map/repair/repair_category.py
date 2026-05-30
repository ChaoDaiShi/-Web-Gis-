from flask import Blueprint, jsonify
from .db import get_db

repair_category_bp = Blueprint('repair_category', __name__)

@repair_category_bp.route('/repair/categories', methods=['GET'])
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
