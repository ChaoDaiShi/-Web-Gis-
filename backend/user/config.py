from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'sh-cynosdbmysql-grp-c6mzndo0.sql.tencentcdb.com'),
    'port': int(os.environ.get('DB_PORT', 28233)),
    'user': os.environ.get('DB_USER', 'mapuser'),
    'password': os.environ.get('DB_PASSWORD', 'NML821512lmn'),
    'database': os.environ.get('DB_DATABASE', 'compus'),
    'charset': os.environ.get('DB_CHARSET', 'utf8mb4')
}

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AMAP_WEB_KEY = os.environ.get('GAODE_API_KEY', '')
    AMAP_SECURITY_JS_CODE = os.environ.get('GAODE_SECURITY_JS_CODE', '')

    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@campus.local')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

db = SQLAlchemy()