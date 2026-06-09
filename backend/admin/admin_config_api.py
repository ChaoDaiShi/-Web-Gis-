from flask import Blueprint, request, jsonify
import pymysql
import json
from admin.admin_common import get_conn, admin_required

admin_config_api_bp = Blueprint('admin_config_api', __name__)

def _table_exists(cursor, table_name):
    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = %s",
        (table_name,)
    )
    row = cursor.fetchone()
    if isinstance(row, dict):
        return row.get('cnt', 0) > 0
    return row[0] > 0

def _configs_from_map_config(cursor):
    cursor.execute(
        "SELECT id, name, center_lng, center_lat, zoom FROM map_config ORDER BY id"
    )
    configs = []
    for row in cursor.fetchall():
        configs.append({
            'config_key': f'map_config.{row["id"]}',
            'config_value': json.dumps({
                'name': row['name'],
                'center_lng': float(row['center_lng']) if row['center_lng'] is not None else None,
                'center_lat': float(row['center_lat']) if row['center_lat'] is not None else None,
                'zoom': row['zoom'],
            }, ensure_ascii=False),
            'description': f'地图配置：{row["name"]}',
            'updated_at': None
        })
    return configs

@admin_config_api_bp.route('/logs', methods=['GET'])
@admin_required
def get_logs():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        user_id = request.args.get('user_id', type=int)
        action = request.args.get('action')
        target_type = request.args.get('target_type')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        
        query = "SELECT id, user_id, action, target_type, target_id, detail, ip_address, created_at FROM system_logs WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)
        
        if action:
            query += " AND action LIKE %s"
            params.append(f'%{action}%')
        
        if target_type:
            query += " AND target_type = %s"
            params.append(target_type)
        
        if start_time:
            query += " AND created_at >= %s"
            params.append(start_time)
        
        if end_time:
            query += " AND created_at <= %s"
            params.append(end_time)
        
        count_query = query.replace("SELECT id, user_id, action, target_type, target_id, detail, ip_address, created_at", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()['COUNT(*)']
        
        offset = (page - 1) * per_page
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        logs = []
        for row in results:
            logs.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'action': row['action'],
                'target_type': row.get('target_type'),
                'target_id': row.get('target_id'),
                'detail': row.get('detail'),
                'ip_address': row['ip_address'],
                'created_at': row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row.get('created_at') else None
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'logs': logs,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_config_api_bp.route('/configs', methods=['GET'])
@admin_required
def get_configs():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        if _table_exists(cursor, 'system_configs'):
            cursor.execute("SELECT config_key, config_value, description, updated_at FROM system_configs")
            results = cursor.fetchall()
            configs = []
            for row in results:
                configs.append({
                    'config_key': row['config_key'],
                    'config_value': row['config_value'],
                    'description': row['description'],
                    'updated_at': row['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if row.get('updated_at') else None
                })
        else:
            configs = _configs_from_map_config(cursor)
        
        return jsonify({'code': 200, 'message': 'success', 'data': configs})
    except Exception as e:
        return jsonify({'code': 200, 'message': 'success', 'data': []})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_config_api_bp.route('/configs/<config_key>', methods=['PUT'])
@admin_required
def update_config(config_key):
    conn = None
    cursor = None
    try:
        data = request.get_json() or {}
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        if _table_exists(cursor, 'system_configs'):
            cursor.execute("SELECT COUNT(*) AS cnt FROM system_configs WHERE config_key = %s", (config_key,))
            count = cursor.fetchone()['cnt']
            if count > 0:
                cursor.execute(
                    "UPDATE system_configs SET config_value = %s, updated_at = NOW() WHERE config_key = %s",
                    (data.get('config_value', ''), config_key)
                )
            else:
                cursor.execute(
                    "INSERT INTO system_configs (config_key, config_value, description, updated_at) "
                    "VALUES (%s, %s, %s, NOW())",
                    (config_key, data.get('config_value', ''), data.get('description', ''))
                )
            conn.commit()
            return jsonify({'code': 200, 'message': '更新成功'})

        if config_key.startswith('map_config.'):
            map_id = config_key.split('.', 1)[1]
            try:
                payload = json.loads(data.get('config_value', '{}'))
            except json.JSONDecodeError:
                return jsonify({'code': 400, 'message': '配置值须为合法 JSON'}), 400
            cursor.execute("SELECT id FROM map_config WHERE id = %s", (map_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '地图配置不存在'}), 404
            cursor.execute(
                "UPDATE map_config SET name = %s, center_lng = %s, center_lat = %s, zoom = %s "
                "WHERE id = %s",
                (
                    payload.get('name'),
                    payload.get('center_lng'),
                    payload.get('center_lat'),
                    payload.get('zoom'),
                    map_id
                )
            )
            conn.commit()
            return jsonify({'code': 200, 'message': '更新成功'})

        return jsonify({'code': 400, 'message': '当前环境不支持修改该配置'}), 400
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
