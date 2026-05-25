import pymysql
import os

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

BACKEND_ROOT = os.path.dirname(__file__)

def get_conn():
    return pymysql.connect(**DB_CONFIG)
