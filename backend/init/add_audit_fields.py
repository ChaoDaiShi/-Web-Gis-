
# -*- coding: utf-8 -*-
"""
为 lost_item 表添加审核相关字段的脚本
"""

import pymysql
from config import DB_CONFIG

def add_audit_fields(cursor, conn):
    """添加审核相关字段"""
    try:
        # 检查 audit_status 字段是否存在
        cursor.execute("SHOW COLUMNS FROM lost_item LIKE 'audit_status'")
        if not cursor.fetchone():
            # 添加 audit_status 字段
            cursor.execute("""
                ALTER TABLE lost_item 
                ADD COLUMN audit_status VARCHAR(20) DEFAULT 'pending' 
                COMMENT '审核状态: pending待审核, approved已通过, rejected已拒绝'
            """)
            print("✓ audit_status 字段添加成功")
        else:
            print("✓ audit_status 字段已存在")
        
        # 检查 audit_time 字段是否存在
        cursor.execute("SHOW COLUMNS FROM lost_item LIKE 'audit_time'")
        if not cursor.fetchone():
            # 添加 audit_time 字段
            cursor.execute("""
                ALTER TABLE lost_item 
                ADD COLUMN audit_time DATETIME NULL 
                COMMENT '审核时间'
            """)
            print("✓ audit_time 字段添加成功")
        else:
            print("✓ audit_time 字段已存在")
        
        # 检查 audit_remark 字段是否存在
        cursor.execute("SHOW COLUMNS FROM lost_item LIKE 'audit_remark'")
        if not cursor.fetchone():
            # 添加 audit_remark 字段
            cursor.execute("""
                ALTER TABLE lost_item 
                ADD COLUMN audit_remark VARCHAR(200) NULL 
                COMMENT '审核备注'
            """)
            print("✓ audit_remark 字段添加成功")
        else:
            print("✓ audit_remark 字段已存在")
        
        # 检查 audit_by 字段是否存在
        cursor.execute("SHOW COLUMNS FROM lost_item LIKE 'audit_by'")
        if not cursor.fetchone():
            # 添加 audit_by 字段
            cursor.execute("""
                ALTER TABLE lost_item 
                ADD COLUMN audit_by INT NULL 
                COMMENT '审核人ID'
            """)
            print("✓ audit_by 字段添加成功")
        else:
            print("✓ audit_by 字段已存在")
        
        # 将现有数据的 audit_status 设置为 approved
        cursor.execute("UPDATE lost_item SET audit_status = 'approved' WHERE audit_status IS NULL OR audit_status = ''")
        
        conn.commit()
        print("✓ 数据迁移完成")
        return True
        
    except Exception as e:
        print(f"✗ 添加审核字段失败: {e}")
        conn.rollback()
        return False

def main():
    """主函数"""
    print("开始为 lost_item 表添加审核字段...")
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        add_audit_fields(cursor, conn)
        
        cursor.close()
        conn.close()
        
        print("\n✓ 审核字段添加完成")
        
    except Exception as e:
        print(f"\n✗ 添加审核字段失败: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()

if __name__ == '__main__':
    main()
