
import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'mapuser',
    'password': '123456',
    'database': 'compus',
    'charset': 'utf8mb4'
}

def connect_db():
    return pymysql.connect(**DB_CONFIG)

def get_table_columns(cursor, table_name):
    cursor.execute(f"DESCRIBE " + table_name)
    return {row[0] for row in cursor.fetchall()}

def main():
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        print("=== 数据库表结构验证 ===\n")
        
        # 根据数据库文档定义的正确字段
        doc_tables = {
            'user': ['user_id', 'username', 'password_hash', 'email', 'phone', 'avatar_url', 'create_time', 'signature', 'bio', 'bg_image', 'role', 'status'],
            'admin': ['admin_id', 'username', 'password_hash', 'email', 'phone', 'create_time', 'last_login'],
            'user_verify': ['verify_id', 'user_id', 'identity', 'real_name', 'id_card', 'student_id', 'school', 'phone', 'email', 'id_card_front', 'id_card_back', 'status', 'create_time', 'update_time'],
            'category': ['id', 'name', 'description', 'sort_order', 'is_active', 'created_at'],
            'location': ['location_id', 'name', 'latitude', 'longitude', 'detail'],
            'map_config': ['id', 'name', 'center_lng', 'center_lat', 'sw_lng', 'sw_lat', 'ne_lng', 'ne_lat', 'zoom'],
            'lost_item': ['item_id', 'title', 'description', 'type', 'category_id', 'status', 'image_urls', 'publisher_id', 'location_id', 'create_time', 'update_time', 'audit_status', 'audit_time', 'audit_remark', 'audit_by'],
            'item_campus': ['id', 'item_id', 'campus_id', 'create_time'],
            'claim': ['claim_id', 'item_id', 'claimer_id', 'message', 'status', 'create_time'],
            'claim_form': ['claim_id', 'item_id', 'username', 'applicant_name', 'applicant_phone', 'claim_reason', 'item_description', 'user_id', 'proof_images', 'status', 'create_time', 'applicant_email'],
            'return_form': ['return_id', 'item_id', 'username', 'applicant_name', 'applicant_phone', 'return_reason', 'item_description', 'user_id', 'proof_images', 'status', 'create_time'],
            'messages': ['message_id', 'user_id', 'title', 'content', 'message_type', 'is_read', 'create_time', 'item_id', 'is_deleted', 'delete_time'],
            'repair_category': ['repair_category_id', 'name', 'icon', 'description'],
            'repair': ['repair_id', 'title', 'description', 'repair_category_id', 'location_id', 'reporter_id', 'images', 'status', 'priority', 'assignee_id', 'process_note', 'create_time', 'update_time'],
            'repair_campus': ['id', 'repair_id', 'campus_id', 'create_time'],
            'nav_nodes': ['node_id', 'name', 'lng', 'lat', 'type', 'campus_id', 'created_at', 'updated_at'],
            'community_posts': ['post_id', 'user_id', 'title', 'content', 'images', 'is_public', 'is_commentable', 'created_at', 'updated_at'],
            'community_comments': ['comment_id', 'post_id', 'user_id', 'parent_id', 'content', 'created_at'],
            'post_likes': ['like_id', 'post_id', 'user_id', 'created_at'],
            'comment_likes': ['like_id', 'comment_id', 'user_id', 'created_at'],
            'notifications': ['notification_id', 'user_id', 'type', 'post_id', 'comment_id', 'content', 'is_read', 'created_at']
        }
        
        all_correct = True
        
        for table_name, expected_columns in sorted(doc_tables.items()):
            cursor.execute("SHOW TABLES LIKE %s", (table_name,))
            if not cursor.fetchone():
                print(f"❌ 表 {table_name} 不存在")
                all_correct = False
                continue
            
            actual_columns = get_table_columns(cursor, table_name)
            expected_set = set(expected_columns)
            
            missing = sorted(expected_set - actual_columns)
            extra = sorted(actual_columns - expected_set)
            
            if missing or extra:
                print(f"❌ 表 {table_name}:")
                if missing:
                    print(f"  缺失字段: {', '.join(missing)}")
                if extra:
                    print(f"  多余字段: {', '.join(extra)}")
                all_correct = False
            else:
                print(f"✅ 表 {table_name}")
        
        if all_correct:
            print("\n🎉 所有表结构均与数据库文档一致！\n")
        else:
            print("\n⚠️  部分表结构不一致，请检查上面的输出！\n")
        
    except Exception as e:
        print(f"验证失败: {e}")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
