"""检查和修复认领数据"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.db_config import get_conn

def check_data():
    """检查数据库中的认领数据"""
    conn = get_conn()
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("数据库数据检查")
    print("="*60)
    
    # 1. 查看所有物品
    print("\n【所有物品】")
    cursor.execute("""
        SELECT item_id, title, publisher_id, status, audit_status 
        FROM lost_item 
        ORDER BY item_id DESC 
        LIMIT 20
    """)
    items = cursor.fetchall()
    for item in items:
        print(f"  ID={item[0]}, 标题={item[1]}, 发布者ID={item[2]}, 状态={item[3]}, 审核状态={item[4]}")
    
    # 2. 查看所有认领申请
    print("\n【所有认领申请】")
    cursor.execute("""
        SELECT claim_id, item_id, user_id, applicant_name, status 
        FROM claim_form 
        ORDER BY claim_id DESC 
        LIMIT 20
    """)
    claims = cursor.fetchall()
    for claim in claims:
        print(f"  认领ID={claim[0]}, 物品ID={claim[1]}, 用户ID={claim[2]}, 申请人={claim[3]}, 状态={claim[4]}")
    
    # 2.5 查看可预约归还的物品（用户ID=6）
    print("\n【用户ID=6 可预约归还的物品】")
    cursor.execute("""
        SELECT 
            li.item_id, li.title, li.status, li.publisher_id,
            cf.claim_id, cf.user_id as owner_id, cf.status as claim_status
        FROM lost_item li
        INNER JOIN claim_form cf ON li.item_id = cf.item_id AND cf.status = 1
        WHERE li.publisher_id = 6 AND li.status = 1
    """)
    available = cursor.fetchall()
    for item in available:
        print(f"  物品ID={item[0]}, 标题={item[1]}, 物品状态={item[2]}, 发布者ID={item[3]}, 认领ID={item[4]}, 失主ID={item[5]}, 认领状态={item[6]}")
    
    # 2.6 检查数据不一致的物品（状态=1但无认领记录）
    print("\n【数据不一致的物品（状态=1但无认领记录）】")
    cursor.execute("""
        SELECT li.item_id, li.title, li.publisher_id, li.status
        FROM lost_item li
        LEFT JOIN claim_form cf ON li.item_id = cf.item_id AND cf.status = 1
        WHERE li.status = 1 AND cf.claim_id IS NULL
    """)
    inconsistent = cursor.fetchall()
    for item in inconsistent:
        print(f"  ⚠️ 物品ID={item[0]}, 标题={item[1]}, 发布者ID={item[2]}, 状态={item[3]} (无认领记录)")
    
    # 3. 查看物品状态说明
    print("\n【状态说明】")
    print("  lost_item.status: 0=未认领, 1=已认领")
    print("  claim_form.status: 0=待审核, 1=审核通过, 2=审核拒绝")
    
    cursor.close()
    conn.close()

def fix_claim_status(item_id, claim_user_id):
    """修复认领状态"""
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # 更新物品状态为已认领
        cursor.execute("UPDATE lost_item SET status = 1 WHERE item_id = %s", (item_id,))
        
        # 更新认领申请状态为通过
        cursor.execute("""
            UPDATE claim_form SET status = 1 
            WHERE item_id = %s AND user_id = %s
        """, (item_id, claim_user_id))
        
        conn.commit()
        print(f"\n✅ 已修复: 物品ID={item_id}, 认领者ID={claim_user_id}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 修复失败: {e}")
    finally:
        cursor.close()
        conn.close()

def create_claim_record(item_id, owner_user_id):
    """为物品创建认领记录"""
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # 检查是否已有认领记录
        cursor.execute("SELECT claim_id FROM claim_form WHERE item_id = %s", (item_id,))
        if cursor.fetchone():
            print(f"\n⚠️ 物品ID={item_id}已有认领记录")
            return
        
        # 创建认领记录
        cursor.execute("""
            INSERT INTO claim_form (item_id, user_id, applicant_name, applicant_phone, 
                                   claim_reason, item_description, status, create_time)
            VALUES (%s, %s, '失主', '13800138000', '这是我的物品', '物品描述', 1, NOW())
        """, (item_id, owner_user_id))
        
        conn.commit()
        print(f"\n✅ 已为物品ID={item_id}创建认领记录，失主ID={owner_user_id}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 创建失败: {e}")
    finally:
        cursor.close()
        conn.close()

def fix_inconsistent_items():
    """修复数据不一致的物品（状态=1但无认领记录）"""
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # 查找数据不一致的物品
        cursor.execute("""
            SELECT li.item_id, li.title, li.publisher_id
            FROM lost_item li
            LEFT JOIN claim_form cf ON li.item_id = cf.item_id AND cf.status = 1
            WHERE li.status = 1 AND cf.claim_id IS NULL
        """)
        inconsistent = cursor.fetchall()
        
        if not inconsistent:
            print("\n✅ 没有数据不一致的物品")
            return
        
        print(f"\n发现 {len(inconsistent)} 个数据不一致的物品：")
        for item in inconsistent:
            print(f"  物品ID={item[0]}, 标题={item[1]}, 发布者ID={item[2]}")
        
        confirm = input("\n是否为这些物品创建认领记录？(y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            return
        
        # 为每个物品创建认领记录
        for item in inconsistent:
            item_id = item[0]
            publisher_id = item[2]
            
            # 找一个不同的用户作为失主
            cursor.execute("SELECT user_id FROM user WHERE user_id != %s LIMIT 1", (publisher_id,))
            owner = cursor.fetchone()
            if not owner:
                print(f"  ❌ 物品ID={item_id} 找不到失主用户")
                continue
            
            owner_id = owner[0]
            
            # 创建认领记录
            cursor.execute("""
                INSERT INTO claim_form (item_id, user_id, applicant_name, applicant_phone, 
                                       claim_reason, item_description, status, create_time)
                VALUES (%s, %s, '失主', '13800138000', '这是我的物品', '物品描述', 1, NOW())
            """, (item_id, owner_id))
            
            print(f"  ✅ 物品ID={item_id} 已创建认领记录，失主ID={owner_id}")
        
        conn.commit()
        print("\n✅ 修复完成")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 修复失败: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("\n1. 检查数据")
    print("2. 修复认领状态")
    print("3. 为物品创建认领记录")
    print("4. 修复数据不一致的物品")
    
    choice = input("\n请选择 (1/2/3/4): ").strip()
    
    if choice == "1":
        check_data()
    elif choice == "2":
        item_id = input("请输入物品ID: ").strip()
        user_id = input("请输入认领者用户ID: ").strip()
        fix_claim_status(int(item_id), int(user_id))
        print("\n修复后的数据:")
        check_data()
    elif choice == "3":
        item_id = input("请输入物品ID: ").strip()
        user_id = input("请输入失主用户ID: ").strip()
        create_claim_record(int(item_id), int(user_id))
        print("\n创建后的数据:")
        check_data()
    elif choice == "4":
        fix_inconsistent_items()
        print("\n修复后的数据:")
        check_data()
    else:
        print("无效选择")
