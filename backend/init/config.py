# -*- coding: utf-8 -*-
"""
数据库配置文件
"""
import os
from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'sh-cynosdbmysql-grp-c6mzndo0.sql.tencentcdb.com'),
    'user': os.environ.get('DB_USER', 'mapuser'),
    'password': os.environ.get('DB_PASSWORD', 'NML821512lmn'),
    'database': os.environ.get('DB_DATABASE', 'compus'),
    'charset': os.environ.get('DB_CHARSET', 'utf8mb4'),
    'port': int(os.environ.get('DB_PORT', 28233))
}

# 默认管理员账号
DEFAULT_ADMIN = {
    'username': 'admin',
    'password': 'admin'
}

# 初始分类数据
INITIAL_CATEGORIES = [
    '校园卡',
    '钥匙',
    '书包',
    '手机',
    '钱包',
    '证件',
    '文具',
    '其他'
]

# 初始校区数据
INITIAL_CAMPUSES = [
    {
        'name': '成都信息工程大学航空港校区',
        'center_lng': 103.9694,
        'center_lat': 30.5728,
        'sw_lng': 103.9600,
        'sw_lat': 30.5650,
        'ne_lng': 103.9800,
        'ne_lat': 30.5800,
        'zoom': 17
    },
    {
        'name': '成都信息工程大学龙泉校区',
        'center_lng': 104.2282,
        'center_lat': 30.5858,
        'sw_lng': 104.2180,
        'sw_lat': 30.5780,
        'ne_lng': 104.2380,
        'ne_lat': 30.5930,
        'zoom': 17
    }
]