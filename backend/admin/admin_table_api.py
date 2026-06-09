from flask import Blueprint, request, jsonify
from user.models import User
from user.config import db
import pymysql
from common.db_config import get_conn

table_bp = Blueprint('table', __name__)

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

@table_bp.route('/api/admin/tables', methods=['GET'])
@admin_required
def get_all_tables():
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': tables
        })
    finally:
        cursor.close()
        conn.close()

@table_bp.route('/api/admin/tables/<table_name>/structure', methods=['GET'])
@admin_required
def get_table_structure(table_name):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(f"DESCRIBE {table_name}")
        structure = []
        for col in cursor.fetchall():
            structure.append({
                'field': col[0],
                'type': col[1],
                'null': 'YES' if col[2] == 'YES' else 'NO',
                'key': col[3],
                'default': col[4],
                'extra': col[5]
            })
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': structure
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@table_bp.route('/api/admin/tables/<table_name>/data', methods=['GET'])
@admin_required
def get_table_data(table_name):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search_field = request.args.get('search_field')
    search_value = request.args.get('search_value')
    
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        offset = (page - 1) * per_page
        
        if search_field and search_value:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {search_field} LIKE %s", (f'%{search_value}%',))
            total = cursor.fetchone()['COUNT(*)']
            cursor.execute(f"SELECT * FROM {table_name} WHERE {search_field} LIKE %s LIMIT %s OFFSET %s", 
                        (f'%{search_value}%', per_page, offset))
        else:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total = cursor.fetchone()['COUNT(*)']
            cursor.execute(f"SELECT * FROM {table_name} LIMIT %s OFFSET %s", (per_page, offset))
        
        data = cursor.fetchall()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'items': data
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@table_bp.route('/api/admin/tables/<table_name>/data', methods=['POST'])
@admin_required
def insert_table_data(table_name):
    data = request.get_json()
    
    conn = get_conn()
    cursor = conn.cursor()
    try:
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = list(data.values())
        
        cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
        conn.commit()
        
        return jsonify({
            'code': 200,
            'message': '插入成功',
            'data': {'insert_id': cursor.lastrowid}
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@table_bp.route('/api/admin/tables/<table_name>/data/<primary_key>', methods=['PUT'])
@admin_required
def update_table_data(table_name, primary_key):
    data = request.get_json()
    
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(f"DESCRIBE {table_name}")
        cols = cursor.fetchall()
        pk_field = cols[0][0]
        
        set_clause = ', '.join([f'{k}=%s' for k in data.keys()])
        values = list(data.values()) + [primary_key]
        
        cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE {pk_field}=%s", values)
        conn.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': {'affected_rows': cursor.rowcount}
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@table_bp.route('/api/admin/tables/<table_name>/data/<primary_key>', methods=['DELETE'])
@admin_required
def delete_table_data(table_name, primary_key):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(f"DESCRIBE {table_name}")
        cols = cursor.fetchall()
        pk_field = cols[0][0]
        
        cursor.execute(f"DELETE FROM {table_name} WHERE {pk_field}=%s", (primary_key,))
        conn.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功',
            'data': {'affected_rows': cursor.rowcount}
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
