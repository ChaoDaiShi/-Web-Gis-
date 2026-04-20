from app import create_app
from app.models.database import db, User

def seed_data():
    """
    数据库初始化脚本
    创建测试用户数据用于开发和测试
    """
    app = create_app()
    with app.app_context():
        db.create_all()

        if User.query.count() == 0:
            users = [
                User(username='张三', email='zhangsan@example.com', phone='13800138001'),
                User(username='李四', email='lisi@example.com', phone='13800138002'),
                User(username='王五', email='wangwu@example.com', phone='13800138003'),
            ]

            for user in users:
                db.session.add(user)

            db.session.commit()
            print('测试用户数据已创建')

            for user in users:
                print(f'用户ID: {user.id}, 用户名: {user.username}')
        else:
            print('数据库中已有数据，跳过初始化')

if __name__ == '__main__':
    seed_data()