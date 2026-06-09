import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.db_config import get_conn

conn = get_conn()
cursor = conn.cursor()

try:
    print('=== 检查 user 表缺失字段 ===')
    
    cursor.execute("DESCRIBE user")
    columns = cursor.fetchall()
    column_names = [col[0] for col in columns]
    
    print(f"当前 user 表字段: {column_names}")
    
    # 检查并添加缺失字段
    if 'role' not in column_names:
        print("添加缺失字段: role")
        cursor.execute("ALTER TABLE user ADD COLUMN role VARCHAR(20) DEFAULT 'student'")
    
    if 'status' not in column_names:
        print("添加缺失字段: status")
        cursor.execute("ALTER TABLE user ADD COLUMN status VARCHAR(20) DEFAULT 'normal'")
    
    conn.commit()
    
    # 验证修复结果
    print('\n=== 修复后的 user 表结构 ===')
    cursor.execute("DESCRIBE user")
    columns = cursor.fetchall()
    for col in columns:
        print(f"{col[0]}: {col[1]} - Null: {col[2]}, Default: {col[4]}")
        
except Exception as e:
    print(f"修复失败: {e}")
    conn.rollback()
finally:
    conn.close()

print('\n=== user 表修复完成 ===')
