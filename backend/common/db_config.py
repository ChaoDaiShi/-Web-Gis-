# -*- coding: utf-8 -*-
"""
统一数据库配置模块
所有数据库连接统一从此模块获取，修改数据库配置只需改 .env 文件
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'sh-cynosdbmysql-grp-c6mzndo0.sql.tencentcdb.com'),
    'port': int(os.environ.get('DB_PORT', 28233)),
    'user': os.environ.get('DB_USER', 'mapuser'),
    'password': os.environ.get('DB_PASSWORD', 'NML821512lmn'),
    'database': os.environ.get('DB_DATABASE', 'compus'),
    'charset': os.environ.get('DB_CHARSET', 'utf8mb4'),
    'connect_timeout': int(os.environ.get('DB_TIMEOUT', 10)),
    'read_timeout': int(os.environ.get('DB_TIMEOUT', 10)),
    'write_timeout': int(os.environ.get('DB_TIMEOUT', 10))
}


def get_conn():
    """获取数据库连接（统一入口）"""
    return pymysql.connect(**DB_CONFIG)
