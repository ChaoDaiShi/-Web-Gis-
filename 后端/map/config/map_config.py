from flask import Blueprint, jsonify
from .. import get_conn
import pymysql

map_config_bp = Blueprint('map_config', __name__)

@map_config_bp.route('/map/campuses', methods=['GET'])
def get_campuses():
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT
                id, name, center_lng, center_lat,
                sw_lng, sw_lat, ne_lng, ne_lat, zoom
            FROM map_config
            ORDER BY id ASC
        """)
        rows = cursor.fetchall()
        campuses = []
        for row in rows:
            campuses.append({
                'id': f'campus_{row["id"]}',
                'name': row['name'],
                'center': [row['center_lng'], row['center_lat']],
                'bounds': {
                    'sw': [row['sw_lng'], row['sw_lat']],
                    'ne': [row['ne_lng'], row['ne_lat']]
                },
                'zoom': row['zoom']
            })
        return jsonify({
            'success': True,
            'data': campuses
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })
    finally:
        cursor.close()
        conn.close()

@map_config_bp.route('/map/default', methods=['GET'])
def get_default_map():
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT
                name, center_lng, center_lat,
                sw_lng, sw_lat, ne_lng, ne_lat, zoom
            FROM map_config
            ORDER BY name ASC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            return jsonify(row)
    except Exception:
        pass
    finally:
        cursor.close()
        conn.close()

    return jsonify({
        "name": "default",
        "center_lng": 121.4737,
        "center_lat": 31.2304,
        "sw_lng": 121.4637,
        "sw_lat": 31.2204,
        "ne_lng": 121.4837,
        "ne_lat": 31.2404,
        "zoom": 18
    })
