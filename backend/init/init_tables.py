# -*- coding: utf-8 -*-
"""
创建所有数据表的脚本
"""

import pymysql
from config import DB_CONFIG

def create_table(cursor, conn, table_name, create_sql):
    """创建数据表"""
    try:
        cursor.execute(create_sql)
        conn.commit()
        print(f"✓ {table_name} 表创建成功")
        return True
    except Exception as e:
        print(f"✗ {table_name} 表创建失败: {e}")
        conn.rollback()
        return False

def create_user_table(cursor, conn):
    """创建用户表"""
    create_sql = """
    CREATE TABLE IF NOT EXISTS user (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        avatar_url VARCHAR(255),
        phone VARCHAR(20),
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME NULL,
        is_active BOOLEAN DEFAULT TRUE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    return create_table(cursor, conn, 'user', create_sql)

def create_admin_table(cursor, conn):
    """创建管理员表"""
    create_sql = """
    CREATE TABLE IF NOT EXISTS admin (
        admin_id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    return create_table(cursor, conn, 'admin', create_sql)

def create_category_table(cursor, conn):
    """创建分类表"""
    create_sql = """
    CREATE TABLE IF NOT EXISTS category (
        category_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(50) NOT NULL UNIQUE,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    return create_table(cursor, conn, 'category', create_sql)

def create_lost_item_table(cursor, conn):
    """创建失物招领表"""
    create_sql = """
    CREATE TABLE IF NOT EXISTS lost_item (
        item_id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(100) NOT NULL,
        description TEXT,
        type INT DEFAULT 0,
        category_id INT,
        publisher_id INT NOT NULL,
        longitude DECIMAL(12,8),
        latitude DECIMAL(12,8),
        location VARCHAR(255),
        images TEXT,
        status INT DEFAULT 0,
        claimer_id INT NULL,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        update_time DATETIME NULL,
        FOREIGN KEY (category_id) REFERENCES category(category_id),
        FOREIGN KEY (publisher_id) REFERENCES user(user_id),
        FOREIGN KEY (claimer_id) REFERENCES user(user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    return create_table(cursor, conn, 'lost_item', create_sql)

def create_audit_table(cursor, conn):
    """创建统一审核表"""
    create_sql = """
    CREATE TABLE IF NOT EXISTS audit (
        audit_id INT AUTO_INCREMENT PRIMARY KEY,
        target_type VARCHAR(50) NOT NULL COMMENT '审核目标类型: lost_item, claim, claim_form, return_form, user_verify, appointment, privilege_request',
        target_id INT NOT NULL COMMENT '关联目标ID',
        requester_id INT COMMENT '申请人ID',
        status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '审核状态: pending, approved, rejected',
        audit_by INT COMMENT '审核人ID(管理员)',
        audit_time DATETIME COMMENT '审核时间',
        audit_remark VARCHAR(500) COMMENT '审核备注',
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        INDEX idx_target_type (target_type),
        INDEX idx_target_id (target_id),
        INDEX idx_status (status),
        INDEX idx_requester (requester_id),
        INDEX idx_audit_by (audit_by)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='统一审核表';
    """
    return create_table(cursor, conn, 'audit', create_sql)

def create_claim_form_table(cursor, conn):
    """创建认领申请表单"""
    create_sql = """
    CREATE TABLE IF NOT EXISTS claim_form (
        claim_id INT AUTO_INCREMENT PRIMARY KEY,
        item_id INT,
        applicant_name VARCHAR(50),
        applicant_phone VARCHAR(50) NOT NULL,
        applicant_email VARCHAR(100),
        claim_reason TEXT NOT NULL,
        item_description TEXT NOT NULL,
        user_id INT,
        proof_images TEXT,
        status INT DEFAULT 0,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES lost_item(item_id),
        FOREIGN KEY (user_id) REFERENCES user(user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    return create_table(cursor, conn, 'claim_form', create_sql)

def create_return_form_table(cursor, conn):
    """创建归还申请表单"""
    create_sql = """
    CREATE TABLE IF NOT EXISTS return_form (
        return_id INT AUTO_INCREMENT PRIMARY KEY,
        item_id INT,
        returner_name VARCHAR(100) NOT NULL,
        returner_phone VARCHAR(20) NOT NULL,
        returner_email VARCHAR(100),
        return_reason TEXT NOT NULL,
        return_location VARCHAR(500),
        user_id INT,
        proof_images TEXT,
        status SMALLINT DEFAULT 0,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES lost_item(item_id),
        FOREIGN KEY (user_id) REFERENCES user(user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    return create_table(cursor, conn, 'return_form', create_sql)

def create_messages_table(cursor, conn):
    """创建消息表"""
    create_sql = """
    CREATE TABLE IF NOT EXISTS messages (
        message_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        title VARCHAR(255) NOT NULL,
        content TEXT NOT NULL,
        message_type ENUM('system', 'claim', 'publish', 'reminder', 'return') DEFAULT 'system',
        is_read BOOLEAN DEFAULT FALSE,
        is_deleted BOOLEAN DEFAULT FALSE,
        delete_time DATETIME NULL,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    return create_table(cursor, conn, 'messages', create_sql)

def create_map_config_table(cursor, conn):
    """创建地图配置表"""
    create_sql = """
    CREATE TABLE IF NOT EXISTS map_config (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        center_lng DECIMAL(12,8) NOT NULL,
        center_lat DECIMAL(12,8) NOT NULL,
        sw_lng DECIMAL(12,8) NOT NULL,
        sw_lat DECIMAL(12,8) NOT NULL,
        ne_lng DECIMAL(12,8) NOT NULL,
        ne_lat DECIMAL(12,8) NOT NULL,
        zoom INT DEFAULT 17,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        update_time DATETIME NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    return create_table(cursor, conn, 'map_config', create_sql)

def create_repair_table(cursor, conn):
    """创建报修表"""
    create_sql = """
    CREATE TABLE IF NOT EXISTS repair (
        repair_id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(100) NOT NULL,
        description TEXT NOT NULL,
        priority INT DEFAULT 1,
        longitude DECIMAL(12,8) NOT NULL,
        latitude DECIMAL(12,8) NOT NULL,
        location VARCHAR(255),
        status INT DEFAULT 0,
        reporter_id INT NOT NULL,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        update_time DATETIME NULL,
        FOREIGN KEY (reporter_id) REFERENCES user(user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    return create_table(cursor, conn, 'repair', create_sql)

def main():
    """主函数"""
    print("开始创建数据表...")
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 创建所有表
        tables = [
            create_user_table,
            create_admin_table,
            create_category_table,
            create_lost_item_table,
            create_claim_form_table,
            create_return_form_table,
            create_messages_table,
            create_map_config_table,
            create_repair_table,
            create_audit_table
        ]
        
        for table_func in tables:
            table_func(cursor, conn)
        
        cursor.close()
        conn.close()
        
        print("\n✓ 所有数据表创建完成")
        
    except Exception as e:
        print(f"\n✗ 创建数据表失败: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()

if __name__ == '__main__':
    main()
