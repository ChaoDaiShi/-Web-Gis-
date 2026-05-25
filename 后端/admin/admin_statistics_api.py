from flask import Blueprint, request, jsonify
import pymysql
from admin.admin_common import get_conn, admin_required

admin_statistics_api_bp = Blueprint('admin_statistics_api', __name__)

@admin_statistics_api_bp.route('/statistics/overview', methods=['GET'])
@admin_required
def get_statistics_overview():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM lost_item")
        total_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM lost_item WHERE audit_status = 'pending'")
        pending_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM lost_item WHERE audit_status = 'approved'")
        approved_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM lost_item WHERE status = 'claimed'")
        claimed_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM claim_form")
        total_claims = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM claim_form WHERE status = 'pending'")
        pending_claims = cursor.fetchone()[0]
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total_users': total_users,
                'total_items': total_items,
                'pending_items': pending_items,
                'approved_items': approved_items,
                'claimed_items': claimed_items,
                'total_claims': total_claims,
                'pending_claims': pending_claims
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_statistics_api_bp.route('/statistics/items-by-category', methods=['GET'])
@admin_required
def get_items_by_category():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT c.name, COUNT(l.item_id) as count
            FROM category c
            LEFT JOIN lost_item l ON c.id = l.category_id
            GROUP BY c.id
            ORDER BY c.id
        """)
        
        data = cursor.fetchall()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_statistics_api_bp.route('/statistics/items-by-status', methods=['GET'])
@admin_required
def get_items_by_status():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT status, COUNT(item_id) as count
            FROM lost_item
            GROUP BY status
        """)
        
        status_map = {
            'pending': '待认领',
            'claimed': '已认领',
            'closed': '已关闭',
            '0': '未找到',
            '1': '已找到'
        }
        
        results = cursor.fetchall()
        data = [{'status': status_map.get(row['status'], row['status']), 'count': row['count']} for row in results]
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_statistics_api_bp.route('/locations', methods=['GET'])
def get_locations():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM location")
        locations = cursor.fetchall()
        
        return jsonify(locations)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()