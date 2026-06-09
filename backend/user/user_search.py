"""用户搜索API"""
from flask import Blueprint, jsonify, request
from common.db_config import get_conn
import logging

logger = logging.getLogger(__name__)

user_search_bp = Blueprint('user_search', __name__)

@user_search_bp.route('/users/search', methods=['GET'])
def search_users():
    """
    搜索用户
    支持通过用户ID或用户名搜索
    """
    logger.info("=== 搜索用户 ===")
    
    keyword = request.args.get('keyword', '').strip()
    
    if not keyword:
        return jsonify({'success': False, 'message': '请输入搜索关键词'}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # 尝试按ID精确匹配或用户名模糊匹配
        query = """
            SELECT user_id, username, avatar_url 
            FROM user 
            WHERE user_id = %s OR username LIKE %s
            LIMIT 20
        """
        
        cursor.execute(query, (keyword, f'%{keyword}%'))
        users = cursor.fetchall()
        
        result = []
        for user in users:
            result.append({
                'user_id': user[0],
                'username': user[1],
                'avatar': user[2]
            })
        
        logger.info(f"找到 {len(result)} 个用户")
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        logger.error(f"搜索用户失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
