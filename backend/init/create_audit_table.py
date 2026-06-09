# 创建 audit 统一审核表
import pymysql
from config import DB_CONFIG

sql = """
CREATE TABLE IF NOT EXISTS audit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    target_type VARCHAR(50) NOT NULL COMMENT '审核目标类型: lost_item, claim_form, return_form, user_verify, appointment, privilege_request',
    target_id INT NOT NULL,
    requester_id INT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    audit_by INT COMMENT '审核人ID(管理员)',
    audit_time DATETIME COMMENT '审核时间',
    audit_remark VARCHAR(500) COMMENT '审核备注',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_target (target_type, target_id),
    INDEX idx_status (status),
    INDEX idx_audit_by (audit_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='统一审核表';
"""

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()
cursor.execute(sql)
conn.commit()
print("audit 统一审核表创建成功")

# 检查已存在的 lost_item 数据，创建对应的 audit 记录
cursor.execute("SHOW COLUMNS FROM lost_item LIKE 'audit_status'")
if cursor.fetchone():
    cursor.execute("""
        SELECT li.item_id, li.publisher_id, li.audit_status, li.create_time
        FROM lost_item li
        LEFT JOIN audit a ON a.target_type = 'lost_item' AND a.target_id = li.item_id
        WHERE a.audit_id IS NULL
    """)
    missing = cursor.fetchall()
    if missing:
        for row in missing:
            cursor.execute("""
                INSERT INTO audit (target_type, target_id, requester_id, status, create_time)
                VALUES ('lost_item', %s, %s, %s, %s)
            """, (row[0], row[1], row[2] or 'pending', row[3]))
        conn.commit()
        print(f"已同步 {len(missing)} 条 lost_item 审核记录到 audit 表")
    else:
        print("lost_item 审核数据无需同步")

cursor.close()
conn.close()
print("完成！")
