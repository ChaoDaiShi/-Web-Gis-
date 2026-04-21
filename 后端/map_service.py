from flask import Blueprint, jsonify, send_from_directory
import pymysql
import os

# 创建地图服务蓝图
map_bp = Blueprint('map', __name__)

# ====== 数据库配置 ======
DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",        # ← 你刚创建的用户
    "password": "123456",     # ← 你刚设置的密码
    "database": "compus",
    "charset": "utf8mb4"
}

def get_conn():
    return pymysql.connect(**DB_CONFIG)



# ====== 1. 获取默认地图 ======
@map_bp.route('/map/default', methods=['GET'])
def get_default_map():
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = "SELECT * FROM map_config ORDER BY id ASC LIMIT 1"
    cursor.execute(sql)
    data = cursor.fetchone()

    cursor.close()
    conn.close()

    if not data:
        return jsonify({"error": "没有地图数据"}), 404

    return jsonify(data)


# ====== 2. 获取地图列表（用于下拉选择） ======
@map_bp.route('/map/list', methods=['GET'])
def get_map_list():
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = "SELECT id, name FROM map_config"
    cursor.execute(sql)
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(data)


# ====== 3. 根据ID获取地图配置 ======
@map_bp.route('/map/<int:map_id>', methods=['GET'])
def get_map_by_id(map_id):
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = "SELECT * FROM map_config WHERE id=%s"
    cursor.execute(sql, (map_id,))
    data = cursor.fetchone()

    cursor.close()
    conn.close()

    if not data:
        return jsonify({"error": "地图不存在"}), 404

    return jsonify(data)


# ====== 4. 健康检查接口（可选） ======
@map_bp.route("/")
def home():
    base_dir = r"F:\工程实践2\校园失物招领与位置追踪系统\前端"
    return send_from_directory(base_dir, "主页.html")