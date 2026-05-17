import pymysql
from werkzeug.security import generate_password_hash

DB_CONFIG = {
    'host': 'localhost',
    'user': 'mapuser',
    'password': '123456',
    'database': 'compus',
    'charset': 'utf8mb4'
}

def init_admin():
    connection = None
    cursor = None
    
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        cursor.execute("SELECT * FROM admin WHERE username = %s", ('admin',))
        result = cursor.fetchone()
        
        if result:
            print("管理员账号已存在，跳过初始化")
            return
        
        hashed_password = generate_password_hash('admin')
        
        insert_sql = """
            INSERT INTO admin (username, password_hash)
            VALUES (%s, %s)
        """
        
        cursor.execute(insert_sql, ('admin', hashed_password))
        connection.commit()
        
        print("管理员账号初始化成功！")
        print(f"用户名: admin")
        print(f"密码: admin")
        
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
    init_admin()