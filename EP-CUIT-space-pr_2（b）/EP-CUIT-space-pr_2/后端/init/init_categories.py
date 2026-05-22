import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'mapuser',
    'password': '123456',
    'database': 'compus',
    'charset': 'utf8mb4'
}

def init_categories():
    connection = None
    cursor = None
    
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM category")
        result = cursor.fetchone()
        count = result[0]
        
        if count > 0:
            print(f"分类表已有 {count} 条记录，跳过初始化")
            return
        
        categories = [
            ('校园卡',),
            ('钥匙',),
            ('书包',),
            ('手机',),
            ('钱包',),
            ('证件',),
            ('文具',),
            ('其他',)
        ]
        
        insert_sql = "INSERT INTO category (name) VALUES (%s)"
        
        cursor.executemany(insert_sql, categories)
        connection.commit()
        
        print("分类数据初始化成功！")
        print("已添加以下分类：")
        for cat in categories:
            print(f"  - {cat[0]}")
        
    except pymysql.Error as e:
        print(f"数据库操作失败: {e}")
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == '__main__':
    init_categories()