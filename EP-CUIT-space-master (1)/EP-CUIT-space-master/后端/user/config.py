from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

class Config:
    SECRET_KEY = 'your-secret-key-here'

    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://mapuser:123456@localhost/compus'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AMAP_WEB_KEY = '49382949a3128467653e88aab0daa5c7'
    AMAP_SECURITY_JS_CODE = '13aaa6de30599d02d3b3f1c562e9bd5e'

    ADMIN_EMAIL = os.environ.get('CAMPUS_ADMIN_EMAIL', 'admin@campus.local')
    ADMIN_PASSWORD = os.environ.get('CAMPUS_ADMIN_PASSWORD', 'admin123')

db = SQLAlchemy()
