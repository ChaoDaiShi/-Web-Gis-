import pymysql

conn = pymysql.connect(host='localhost', user='mapuser', password='123456', database='compus')
cursor = conn.cursor(pymysql.cursors.DictCursor)

cursor.execute('SELECT item_id, title, type, status FROM lost_item ORDER BY create_time DESC')
print('物品列表:')
for item in cursor.fetchall():
    type_text = '丢失' if item['type'] == 0 else '拾到'
    print(f"ID:{item['item_id']}, 标题:{item['title']}, 类型:{type_text}({item['type']}), 状态:{item['status']}")

conn.close()