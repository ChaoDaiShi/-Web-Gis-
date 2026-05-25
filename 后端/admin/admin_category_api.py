from flask import Blueprint, request, jsonify
import pymysql
from admin.admin_common import get_conn, admin_required

admin_category_api_bp = Blueprint('admin_category_api', __name__)

@admin_category_api_bp.route('/categories', methods=['GET'])
@admin_required
def get_categories():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT category_id as id, name FROM category ORDER BY category_id")
        categories = cursor.fetchall()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': categories
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_category_api_bp.route('/categories', methods=['POST'])
@admin_required
def create_category():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'code': 400, 'message': '分类名称不能为空'}), 400
        
        cursor.execute("SELECT * FROM category WHERE name = %s", (data['name'],))
        existing = cursor.fetchone()
        if existing:
            return jsonify({'code': 400, 'message': '分类名称已存在'}), 400
        
        cursor.execute("INSERT INTO category (name) VALUES (%s)", (data['name'],))
        
        conn.commit()
        
        return jsonify({
            'code': 201,
            'message': '创建成功'
        }), 201
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_category_api_bp.route('/categories/<category_id>', methods=['PUT'])
@admin_required
def update_category(category_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM category WHERE category_id = %s", (category_id,))
        category = cursor.fetchone()
        
        if not category:
            return jsonify({'code': 404, 'message': '分类不存在'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            cursor.execute("SELECT * FROM category WHERE name = %s AND category_id != %s", (data['name'], category_id))
            existing = cursor.fetchone()
            if existing:
                return jsonify({'code': 400, 'message': '分类名称已存在'}), 400
            
            cursor.execute("UPDATE category SET name = %s WHERE category_id = %s", (data['name'], category_id))
        
        conn.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功'
        })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_category_api_bp.route('/categories/<category_id>', methods=['DELETE'])
@admin_required
def delete_category(category_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM category WHERE category_id = %s", (category_id,))
        category = cursor.fetchone()
        
        if not category:
            return jsonify({'code': 404, 'message': '分类不存在'}), 404
        
        cursor.execute("SELECT COUNT(*) FROM lost_item WHERE category_id = %s", (category_id,))
        items_count = cursor.fetchone()[0]
        
        if items_count > 0:
            return jsonify({'code': 400, 'message': f'该分类下有{items_count}个物品，无法删除'}), 400
        
        cursor.execute("DELETE FROM category WHERE category_id = %s", (category_id,))
        conn.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功'
        })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()