import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from common.db_config import get_conn

def check_user_avatar():
    from common.db_config import DB_CONFIG
    print("DB_CONFIG:", DB_CONFIG)
