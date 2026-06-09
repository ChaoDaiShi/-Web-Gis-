from common.db_config import get_conn as get_db

def get_all_nodes(campus_id='campus_1'):
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM nav_nodes WHERE campus_id = %s", (campus_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()

def get_all_edges(campus_id='campus_1'):
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM nav_edges WHERE campus_id = %s", (campus_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()

def get_node_by_id(node_id):
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM nav_nodes WHERE node_id = %s", (node_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        db.close()

def add_node(name, lng, lat, node_type='intersection', campus_id='campus_1'):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO nav_nodes (name, lng, lat, type, campus_id) VALUES (%s, %s, %s, %s, %s)",
            (name, lng, lat, node_type, campus_id)
        )
        db.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        db.close()

def add_edge(from_node_id, to_node_id, length, name=None, is_bidirectional=True, campus_id='campus_1'):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO nav_edges (from_node_id, to_node_id, length, name, is_bidirectional, campus_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (from_node_id, to_node_id, length, name, is_bidirectional, campus_id)
        )
        db.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        db.close()

def find_nearest_node(lng, lat, campus_id='campus_1'):
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT *, 
                   (6371000 * ACOS(COS(RADIANS(%s)) * COS(RADIANS(lat)) * COS(RADIANS(lng) - RADIANS(%s)) + SIN(RADIANS(%s)) * SIN(RADIANS(lat)))) AS distance
            FROM nav_nodes 
            WHERE campus_id = %s
            ORDER BY distance ASC
            LIMIT 1
        """, (lat, lng, lat, campus_id))
        return cursor.fetchone()
    finally:
        cursor.close()
        db.close()