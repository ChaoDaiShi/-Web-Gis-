import pymysql

def get_db():
    return pymysql.connect(
        host='localhost',
        user='mapuser',
        password='123456',
        database='compus',
        charset='utf8mb4'
    )

__all__ = ['get_db', 'pymysql']
