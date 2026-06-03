from flask import Blueprint, jsonify
from admin.admin_common import get_conn
import pymysql

tags_bp = Blueprint('tags', __name__)

@tags_bp.route('/tags', methods=['GET'])
def get_tags():
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 从post_tag表获取所有不重复的标签
        cursor.execute("SELECT DISTINCT tag_name FROM post_tag ORDER BY tag_name")
        tag_rows = cursor.fetchall()
        
        # 构建标签列表，添加"全部"选项
        tags = [{'id': 1, 'name': '全部', 'active': True}]
        
        # 添加从数据库获取的标签
        for i, row in enumerate(tag_rows, start=2):
            tags.append({'id': i, 'name': row['tag_name'], 'active': False})
        
        # 如果数据库中没有标签，使用默认标签
        if len(tag_rows) == 0:
            default_tags = ['校园生活', '学习交流', '失物招领', '二手交易', '活动公告']
            for i, name in enumerate(default_tags, start=2):
                tags.append({'id': i, 'name': name, 'active': False})
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': tags})
        
    except Exception as e:
        print(f"获取标签列表错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500