import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'mapuser',
    'password': '123456',
    'database': 'compus',
    'charset': 'utf8mb4'
}

def init_nav_data():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM nav_nodes")
        if cursor.fetchone()[0] > 0:
            print("导航节点数据已存在，跳过初始化")
            return
        
        nodes = [
            # 主教学楼区域
            ('正大门', 103.9855, 30.5835, 'entrance'),
            ('图书馆', 103.9865, 30.5825, 'building'),
            ('教学楼A', 103.9875, 30.5820, 'building'),
            ('教学楼B', 103.9885, 30.5815, 'building'),
            ('操场', 103.9895, 30.5805, 'landmark'),
            ('食堂', 103.9845, 30.5810, 'building'),
            ('宿舍区', 103.9835, 30.5800, 'building'),
            ('体育馆', 103.9905, 30.5825, 'building'),
            ('行政楼', 103.9860, 30.5830, 'building'),
            ('实验楼', 103.9880, 30.5835, 'building'),
            
            # 道路交叉口节点
            ('交叉口1', 103.9850, 30.5820, 'intersection'),
            ('交叉口2', 103.9870, 30.5815, 'intersection'),
            ('交叉口3', 103.9890, 30.5810, 'intersection'),
            ('交叉口4', 103.9860, 30.5815, 'intersection'),
            ('交叉口5', 103.9840, 30.5815, 'intersection'),
        ]
        
        cursor.executemany(
            "INSERT INTO nav_nodes (name, lng, lat, type, campus_id) VALUES (%s, %s, %s, %s, 'campus_1')",
            nodes
        )
        conn.commit()
        print("导航节点初始化成功")
        
        # 获取节点ID映射
        cursor.execute("SELECT name, node_id FROM nav_nodes")
        node_map = {row[0]: row[1] for row in cursor.fetchall()}
        
        edges = [
            # 主路
            (node_map['正大门'], node_map['交叉口1'], 150, '正门大道'),
            (node_map['交叉口1'], node_map['交叉口4'], 200, '中央大道'),
            (node_map['交叉口4'], node_map['交叉口2'], 180, '中央大道'),
            (node_map['交叉口2'], node_map['交叉口3'], 220, '中央大道'),
            (node_map['交叉口3'], node_map['操场'], 100, '操场路'),
            
            # 支路
            (node_map['交叉口1'], node_map['食堂'], 120, '食堂路'),
            (node_map['交叉口4'], node_map['图书馆'], 80, '图书馆路'),
            (node_map['交叉口4'], node_map['行政楼'], 60, '行政路'),
            (node_map['交叉口2'], node_map['教学楼A'], 50, '教学路A'),
            (node_map['交叉口2'], node_map['教学楼B'], 80, '教学路B'),
            (node_map['交叉口2'], node_map['实验楼'], 100, '实验路'),
            (node_map['交叉口3'], node_map['体育馆'], 150, '体育馆路'),
            (node_map['食堂'], node_map['宿舍区'], 180, '宿舍路'),
            (node_map['交叉口1'], node_map['宿舍区'], 250, '外环南路'),
            (node_map['图书馆'], node_map['行政楼'], 60, '图书馆后街'),
            (node_map['教学楼A'], node_map['教学楼B'], 100, '教学中路'),
        ]
        
        cursor.executemany(
            "INSERT INTO nav_edges (from_node_id, to_node_id, length, name, is_bidirectional, campus_id) VALUES (%s, %s, %s, %s, 1, 'campus_1')",
            edges
        )
        conn.commit()
        print("导航路段初始化成功")
        
    except Exception as e:
        print(f"导航数据初始化失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_nav_data()