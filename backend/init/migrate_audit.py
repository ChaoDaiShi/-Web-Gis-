# -*- coding: utf-8 -*-
"""
迁移现有审核数据到统一审核表的脚本
"""

import pymysql
from config import DB_CONFIG

def migrate_lost_item_audit(cursor, conn):
    """迁移失物招领的审核数据"""
    print("正在迁移失物招领审核数据...")
    try:
        cursor.execute("""
            SELECT item_id, publisher_id, audit_status, audit_time, audit_remark, audit_by, create_time
            FROM lost_item
            WHERE audit_status IS NOT NULL
        """)
        items = cursor.fetchall()
        
        for item in items:
            item_id, publisher_id, audit_status, audit_time, audit_remark, audit_by, create_time = item
            cursor.execute("""
                INSERT IGNORE INTO audit 
                (target_type, target_id, requester_id, status, audit_by, audit_time, audit_remark, create_time)
                VALUES ('lost_item', %s, %s, %s, %s, %s, %s, %s)
            """, (item_id, publisher_id, audit_status, audit_by, audit_time, audit_remark, create_time))
        
        conn.commit()
        print(f"✓ 已迁移 {len(items)} 条失物招领审核数据")
        return True
    except Exception as e:
        print(f"✗ 迁移失物招领审核数据失败: {e}")
        conn.rollback()
        return False

def migrate_claim_audit(cursor, conn):
    """迁移认领的审核数据"""
    print("正在迁移认领审核数据...")
    try:
        cursor.execute("""
            SELECT claim_id, claimer_id, status, audit_time, audit_remark, audit_by, created_at
            FROM claim
            WHERE status IS NOT NULL
        """)
        claims = cursor.fetchall()
        
        for claim in claims:
            claim_id, claimer_id, status, audit_time, audit_remark, audit_by, created_at = claim
            cursor.execute("""
                INSERT IGNORE INTO audit 
                (target_type, target_id, requester_id, status, audit_by, audit_time, audit_remark, create_time)
                VALUES ('claim', %s, %s, %s, %s, %s, %s, %s)
            """, (claim_id, claimer_id, status, audit_by, audit_time, audit_remark, created_at))
        
        conn.commit()
        print(f"✓ 已迁移 {len(claims)} 条认领审核数据")
        return True
    except Exception as e:
        print(f"✗ 迁移认领审核数据失败: {e}")
        conn.rollback()
        return False

def migrate_claim_form_audit(cursor, conn):
    """迁移认领表单的审核数据"""
    print("正在迁移认领表单审核数据...")
    try:
        status_map = {0: 'pending', 1: 'approved', 2: 'rejected'}
        cursor.execute("""
            SELECT claim_id, user_id, status, create_time
            FROM claim_form
        """)
        claim_forms = cursor.fetchall()
        
        for form in claim_forms:
            claim_id, user_id, status, create_time = form
            mapped_status = status_map.get(status, 'pending')
            cursor.execute("""
                INSERT IGNORE INTO audit 
                (target_type, target_id, requester_id, status, create_time)
                VALUES ('claim_form', %s, %s, %s, %s)
            """, (claim_id, user_id, mapped_status, create_time))
        
        conn.commit()
        print(f"✓ 已迁移 {len(claim_forms)} 条认领表单审核数据")
        return True
    except Exception as e:
        print(f"✗ 迁移认领表单审核数据失败: {e}")
        conn.rollback()
        return False

def migrate_return_form_audit(cursor, conn):
    """迁移归还表单的审核数据"""
    print("正在迁移归还表单审核数据...")
    try:
        status_map = {0: 'pending', 1: 'approved', 2: 'rejected'}
        cursor.execute("""
            SELECT return_id, user_id, status, create_time
            FROM return_form
        """)
        return_forms = cursor.fetchall()
        
        for form in return_forms:
            return_id, user_id, status, create_time = form
            mapped_status = status_map.get(status, 'pending')
            cursor.execute("""
                INSERT IGNORE INTO audit 
                (target_type, target_id, requester_id, status, create_time)
                VALUES ('return_form', %s, %s, %s, %s)
            """, (return_id, user_id, mapped_status, create_time))
        
        conn.commit()
        print(f"✓ 已迁移 {len(return_forms)} 条归还表单审核数据")
        return True
    except Exception as e:
        print(f"✗ 迁移归还表单审核数据失败: {e}")
        conn.rollback()
        return False

def migrate_user_verify_audit(cursor, conn):
    """迁移用户认证的审核数据"""
    print("正在迁移用户认证审核数据...")
    try:
        status_map = {0: 'pending', 1: 'approved', 2: 'rejected'}
        cursor.execute("""
            SELECT verify_id, user_id, status, create_time, update_time
            FROM user_verify
        """)
        user_verifies = cursor.fetchall()
        
        for verify in user_verifies:
            verify_id, user_id, status, create_time, update_time = verify
            mapped_status = status_map.get(status, 'pending')
            audit_time = update_time if status != 0 else None
            cursor.execute("""
                INSERT IGNORE INTO audit 
                (target_type, target_id, requester_id, status, audit_time, create_time)
                VALUES ('user_verify', %s, %s, %s, %s, %s)
            """, (verify_id, user_id, mapped_status, audit_time, create_time))
        
        conn.commit()
        print(f"✓ 已迁移 {len(user_verifies)} 条用户认证审核数据")
        return True
    except Exception as e:
        print(f"✗ 迁移用户认证审核数据失败: {e}")
        conn.rollback()
        return False

def migrate_appointment_audit(cursor, conn):
    """迁移预约的审核数据"""
    print("正在迁移预约审核数据...")
    try:
        cursor.execute("""
            SELECT appointment_id, user_id, status, reviewer_id, review_time, review_note, create_time
            FROM appointment
        """)
        appointments = cursor.fetchall()
        
        for appointment in appointments:
            appointment_id, user_id, status, reviewer_id, review_time, review_note, create_time = appointment
            cursor.execute("""
                INSERT IGNORE INTO audit 
                (target_type, target_id, requester_id, status, audit_by, audit_time, audit_remark, create_time)
                VALUES ('appointment', %s, %s, %s, %s, %s, %s, %s)
            """, (appointment_id, user_id, status, reviewer_id, review_time, review_note, create_time))
        
        conn.commit()
        print(f"✓ 已迁移 {len(appointments)} 条预约审核数据")
        return True
    except Exception as e:
        print(f"✗ 迁移预约审核数据失败: {e}")
        conn.rollback()
        return False

def migrate_privilege_request_audit(cursor, conn):
    """迁移权限申请的审核数据"""
    print("正在迁移权限申请审核数据...")
    try:
        cursor.execute("""
            SELECT request_id, admin_id, status, reviewer_id, review_time, review_note, create_time
            FROM privilege_request
        """)
        privilege_requests = cursor.fetchall()
        
        for req in privilege_requests:
            request_id, admin_id, status, reviewer_id, review_time, review_note, create_time = req
            cursor.execute("""
                INSERT IGNORE INTO audit 
                (target_type, target_id, requester_id, status, audit_by, audit_time, audit_remark, create_time)
                VALUES ('privilege_request', %s, %s, %s, %s, %s, %s, %s)
            """, (request_id, admin_id, status, reviewer_id, review_time, review_note, create_time))
        
        conn.commit()
        print(f"✓ 已迁移 {len(privilege_requests)} 条权限申请审核数据")
        return True
    except Exception as e:
        print(f"✗ 迁移权限申请审核数据失败: {e}")
        conn.rollback()
        return False

def main():
    """主函数"""
    print("开始迁移审核数据到统一审核表...")
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查audit表是否存在
        cursor.execute("SHOW TABLES LIKE 'audit'")
        if not cursor.fetchone():
            print("✗ audit表不存在，请先运行初始化脚本创建表")
            return
        
        # 执行所有迁移
        migrations = [
            migrate_lost_item_audit,
            migrate_claim_audit,
            migrate_claim_form_audit,
            migrate_return_form_audit,
            migrate_user_verify_audit,
            migrate_appointment_audit,
            migrate_privilege_request_audit
        ]
        
        success_count = 0
        for migration in migrations:
            if migration(cursor, conn):
                success_count += 1
        
        cursor.close()
        conn.close()
        
        print(f"\n✓ 审核数据迁移完成，成功 {success_count}/{len(migrations)} 个迁移任务")
        
    except Exception as e:
        print(f"\n✗ 审核数据迁移失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
