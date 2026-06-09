# -*- coding: utf-8 -*-
"""为 user_verify 表添加缺失的 update_time 字段"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.db_config import get_conn

conn = get_conn()
cur = conn.cursor()

try:
    cur.execute("""
        ALTER TABLE user_verify 
        ADD COLUMN update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    """)
    conn.commit()
    print('[OK] user_verify.update_time 字段已添加')
except Exception as e:
    if 'Duplicate column' in str(e):
        print('[SKIP] update_time 字段已存在')
    else:
        print(f'[ERROR] {e}')
finally:
    cur.close()
    conn.close()
