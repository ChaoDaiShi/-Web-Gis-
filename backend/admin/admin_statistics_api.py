from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
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
        
        cursor.execute("SELECT COUNT(*) FROM user")
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

@admin_statistics_api_bp.route('/statistics/items-trend', methods=['GET'])
@admin_required
def get_items_trend():
    conn = None
    cursor = None
    try:
        days = request.args.get('days', 7, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT DATE(create_time) as date, COUNT(item_id) as count
            FROM lost_item
            WHERE create_time >= %s
            GROUP BY DATE(create_time)
            ORDER BY DATE(create_time)
        """, (start_date,))
        
        results = cursor.fetchall()
        data = [{'date': str(row['date']), 'count': row['count']} for row in results]
        
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

@admin_statistics_api_bp.route('/statistics/user-activity', methods=['GET'])
@admin_required
def get_user_activity():
    conn = None
    cursor = None
    try:
        days = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', 10, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT u.user_id, u.username, COUNT(l.item_id) as action_count
            FROM user u
            JOIN lost_item l ON u.user_id = l.publisher_id
            WHERE l.create_time >= %s
            GROUP BY u.user_id, u.username
            ORDER BY COUNT(l.item_id) DESC
            LIMIT %s
        """, (start_date, limit))
        
        results = cursor.fetchall()
        data = [{'user_id': row['user_id'], 'username': row['username'], 'action_count': row['action_count']} for row in results]
        
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