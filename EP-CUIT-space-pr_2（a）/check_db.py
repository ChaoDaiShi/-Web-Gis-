import pymysql

conn = pymysql.connect(host='localhost', user='mapuser', password='123456', database='compus', charset='utf8mb4')
cursor = conn.cursor(pymysql.cursors.DictCursor)

cursor.execute('SELECT * FROM claim_form ORDER BY create_time DESC LIMIT 5')
rows = cursor.fetchall()
print("=== 认领表单 ===")
for row in rows:
    print(f"claim_id: {row['claim_id']}")
    print(f"proof_images: {row['proof_images']}")
    print("---")

cursor.execute('SELECT * FROM return_form ORDER BY create_time DESC LIMIT 5')
rows = cursor.fetchall()
print("\n=== 归还表单 ===")
for row in rows:
    print(f"return_id: {row['return_id']}")
    print(f"proof_images: {row['proof_images']}")
    print("---")

cursor.close()
conn.close()