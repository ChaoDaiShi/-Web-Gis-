import pymysql
import os

DB_CONFIG = {
    'host': 'localhost',
    'user': 'mapuser',
    'password': '123456',
    'database': 'compus',
    'charset': 'utf8mb4'
}

def connect_db():
    return pymysql.connect(**DB_CONFIG)

def execute_sql(cursor, sql, params=None):
    try:
        cursor.execute(sql, params)
        return True, None
    except Exception as e:
        return False, str(e)

def table_exists(cursor, table_name):
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    return cursor.fetchone() is not None

def main():
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        print("=== 开始修复数据库表结构 ===\n")
        
        # 特殊处理：lost_item 有外键指向不存在的 category 表
        if table_exists(cursor, 'lost_item') and not table_exists(cursor, 'category'):
            print("检测到 lost_item 表有外键约束指向不存在的 category 表")
            # 删除这个外键约束
            try:
                cursor.execute("ALTER TABLE lost_item DROP FOREIGN KEY fk_item_category")
                print("已移除 lost_item 表的 fk_item_category 外键约束")
            except Exception as e:
                print(f"删除外键约束失败: {e}")
        
        # 创建 category 表（如果不存在）
        if not table_exists(cursor, 'category'):
            category_table = """
            CREATE TABLE category (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                description VARCHAR(200),
                sort_order INT DEFAULT 0,
                is_active TINYINT(1) DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            success, error = execute_sql(cursor, category_table)
            if success:
                print("创建表 category 成功")
                
                # 添加默认分类数据
                categories = [
                    ('证件', '身份证、学生证、校园卡等证件类', 1, 1),
                    ('电子产品', '手机、耳机、充电宝等电子产品', 2, 1),
                    ('包类', '书包、钱包、手提包等', 3, 1),
                    ('衣物', '衣服、鞋子、帽子等', 4, 1),
                    ('书籍', '课本、笔记本、资料等', 5, 1),
                    ('钥匙', '钥匙、门禁卡等', 6, 1),
                    ('饰品', '手表、眼镜、首饰等', 7, 1),
                    ('其他', '其他物品', 8, 1)
                ]
                cursor.executemany("INSERT INTO category (name, description, sort_order, is_active) VALUES (%s, %s, %s, %s)", categories)
                print("添加默认物品分类")
            else:
                print(f"创建表 category 失败: {error}")
        else:
            print("表 category 已存在，跳过创建")
        
        # 如果 lost_item 表存在且 category_id 是 NOT NULL，修改为允许 NULL
        if table_exists(cursor, 'lost_item'):
            cursor.execute("DESCRIBE lost_item category_id")
            result = cursor.fetchone()
            if result and 'NO' in result[2]:  # 第三个字段是 Null 约束
                try:
                    cursor.execute("ALTER TABLE lost_item MODIFY COLUMN category_id INT NULL")
                    print("已修改 lost_item.category_id 允许为 NULL")
                except Exception as e:
                    print(f"修改 category_id 字段失败: {e}")
        
        # 如果 lost_item 表存在且没有 category 外键，添加外键
        if table_exists(cursor, 'lost_item') and table_exists(cursor, 'category'):
            cursor.execute("SHOW CREATE TABLE lost_item")
            create_sql = cursor.fetchone()[1]
            # 检查是否已经有指向 category(id) 的外键
            if 'category(id)' not in create_sql:
                try:
                    cursor.execute("ALTER TABLE lost_item ADD CONSTRAINT fk_item_category FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE SET NULL")
                    print("已为 lost_item 表添加 category 外键约束")
                except Exception as e:
                    print(f"添加外键约束失败（可能已存在）: {e}")
        
        # 检查并添加其他缺失的表
        missing_tables = [
            ('user_verify', """
            CREATE TABLE user_verify (
                verify_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                identity VARCHAR(50) NOT NULL,
                real_name VARCHAR(100) NOT NULL,
                id_card VARCHAR(18) NOT NULL,
                student_id VARCHAR(50),
                school VARCHAR(200),
                phone VARCHAR(20),
                email VARCHAR(100),
                id_card_front LONGTEXT NOT NULL,
                id_card_back LONGTEXT NOT NULL,
                status TINYINT DEFAULT 0,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
                INDEX idx_verify_user (user_id),
                INDEX idx_verify_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """),
            ('repair_campus', """
            CREATE TABLE repair_campus (
                id INT AUTO_INCREMENT PRIMARY KEY,
                repair_id INT NOT NULL,
                campus_id INT NOT NULL,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (repair_id) REFERENCES repair(repair_id) ON DELETE CASCADE,
                FOREIGN KEY (campus_id) REFERENCES map_config(id) ON DELETE CASCADE,
                UNIQUE KEY unique_repair_campus (repair_id, campus_id),
                INDEX idx_repaircampus_repair (repair_id),
                INDEX idx_repaircampus_campus (campus_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """),
            ('item_campus', """
            CREATE TABLE item_campus (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_id INT NOT NULL,
                campus_id INT NOT NULL,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES lost_item(item_id) ON DELETE CASCADE,
                FOREIGN KEY (campus_id) REFERENCES map_config(id) ON DELETE CASCADE,
                UNIQUE KEY unique_item_campus (item_id, campus_id),
                INDEX idx_itemcampus_item (item_id),
                INDEX idx_itemcampus_campus (campus_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """),
        ]
        
        for table_name, create_sql in missing_tables:
            if not table_exists(cursor, table_name):
                success, error = execute_sql(cursor, create_sql)
                if success:
                    print(f"创建表 {table_name} 成功")
                else:
                    print(f"创建表 {table_name} 失败: {error}")
            else:
                print(f"表 {table_name} 已存在，跳过创建")
        
        # 检查并添加默认管理员
        cursor.execute("SELECT COUNT(*) FROM admin WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            from werkzeug.security import generate_password_hash
            hashed = generate_password_hash('admin')
            cursor.execute("INSERT INTO admin (username, password_hash) VALUES (%s, %s)", ('admin', hashed))
            print("添加默认管理员账号 (admin/admin)")
        
        # 检查并添加默认报修分类
        cursor.execute("SELECT COUNT(*) FROM repair_category")
        if cursor.fetchone()[0] == 0:
            repair_categories = [
                ('教室设备', 'classroom', '教室多媒体、桌椅等设施故障'),
                ('宿舍设施', 'dormitory', '宿舍水电、家具等故障'),
                ('公共区域', 'public', '楼道、走廊等公共设施故障'),
                ('绿化环境', 'garden', '花草树木、环境卫生问题'),
                ('网络通信', 'network', '网络、WiFi故障'),
                ('水电设施', 'water', '水龙头、电灯等故障'),
                ('安全隐患', 'safety', '安全相关问题'),
                ('其他', 'other', '其他类型报修')
            ]
            cursor.executemany("INSERT INTO repair_category (name, icon, description) VALUES (%s, %s, %s)", repair_categories)
            print("添加默认报修分类")
        
        # 检查并添加校区配置
        cursor.execute("SELECT COUNT(*) FROM map_config")
        if cursor.fetchone()[0] == 0:
            campuses = [
                ('成都信息工程大学（航空港校区）', 103.9885, 30.5815, 103.98, 30.575, 103.997, 30.588, 19),
                ('成都信息工程大学（龙泉校区）', 104.305407, 30.606347, 104.295, 30.599, 104.315, 30.613, 19)
            ]
            cursor.executemany("INSERT INTO map_config (name, center_lng, center_lat, sw_lng, sw_lat, ne_lng, ne_lat, zoom) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", campuses)
            print("添加校区配置")
        
        conn.commit()
        print("\n=== 数据库修复完成 ===")
        
    except Exception as e:
        print(f"\n数据库修复失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
