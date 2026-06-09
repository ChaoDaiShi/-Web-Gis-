from flask import Blueprint, request, jsonify
from admin.admin_common import get_conn
import pymysql
import json
import os
import base64
import uuid
from datetime import datetime

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/posts', methods=['GET'])
def get_posts():
    try:
        category = request.args.get('category', 'all')
        user_id = request.args.get('user_id')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        count_query = "SELECT COUNT(*) as total FROM community_posts"
        cursor.execute(count_query)
        total = cursor.fetchone()['total']
        
        offset = (page - 1) * page_size
        query = """
            SELECT p.*, u.username as author_name, u.avatar_url
            FROM community_posts p
            LEFT JOIN user u ON p.user_id = u.user_id
            ORDER BY p.created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (page_size, offset))
        posts = cursor.fetchall()
        
        for post in posts:
            if post.get('images'):
                try:
                    post['images'] = json.loads(post['images'])
                except:
                    post['images'] = []
            else:
                post['images'] = []
            
            # 查询标签
            cursor.execute("SELECT tag_name FROM post_tag WHERE post_id = %s", (post['post_id'],))
            tags = cursor.fetchall()
            post['tags'] = [t['tag_name'] for t in tags]
            
            cursor.execute("SELECT COUNT(*) as count FROM post_likes WHERE post_id = %s", (post['post_id'],))
            post['likes_count'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM community_comments WHERE post_id = %s", (post['post_id'],))
            post['comments_count'] = cursor.fetchone()['count']
            
            post['is_liked'] = False
            if user_id:
                cursor.execute(
                    "SELECT 1 FROM post_likes WHERE post_id = %s AND user_id = %s",
                    (post['post_id'], user_id)
                )
                if cursor.fetchone():
                    post['is_liked'] = True
            
            post['is_following'] = False
            if user_id and post.get('user_id'):
                cursor.execute(
                    "SELECT 1 FROM user_follow WHERE follower_id = %s AND followee_id = %s",
                    (user_id, post['user_id'])
                )
                if cursor.fetchone():
                    post['is_following'] = True
            
            post['created_at'] = post['created_at'].strftime('%Y-%m-%d %H:%M:%S') if post['created_at'] else ''
            post['author_avatar'] = post['avatar_url'] if post['avatar_url'] else ''
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': posts,
            'total': total,
            'page': page,
            'page_size': page_size
        })
    except Exception as e:
        print(f"获取帖子列表错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@posts_bp.route('/posts/stats/<int:user_id>', methods=['GET'])
def get_user_stats(user_id):
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 帖子数
        cursor.execute("""
            SELECT COUNT(*) as post_count 
            FROM community_posts 
            WHERE user_id = %s
        """, (user_id,))
        result = cursor.fetchone()
        post_count = result['post_count'] if result else 0
        
        # 我获得的点赞数（别人点赞我的帖子）
        cursor.execute("""
            SELECT COUNT(*) as received_likes 
            FROM post_likes pl 
            JOIN community_posts p ON pl.post_id = p.post_id 
            WHERE p.user_id = %s
        """, (user_id,))
        result = cursor.fetchone()
        received_likes = result['received_likes'] if result and result['received_likes'] else 0
        
        # 我的点赞数（我点赞别人的帖子）
        cursor.execute("""
            SELECT COUNT(*) as my_likes 
            FROM post_likes 
            WHERE user_id = %s
        """, (user_id,))
        result = cursor.fetchone()
        my_likes = result['my_likes'] if result and result['my_likes'] else 0
        
        # 我获得的评论数（别人评论我的帖子）
        cursor.execute("""
            SELECT COUNT(*) as received_comments 
            FROM community_comments 
            WHERE post_id IN (SELECT post_id FROM community_posts WHERE user_id = %s)
        """, (user_id,))
        result = cursor.fetchone()
        received_comments = result['received_comments'] if result else 0
        
        # 我的评论数（我评论别人的帖子）
        cursor.execute("""
            SELECT COUNT(*) as my_comments 
            FROM community_comments 
            WHERE user_id = %s
        """, (user_id,))
        result = cursor.fetchone()
        my_comments = result['my_comments'] if result else 0
        
        # 粉丝数
        cursor.execute("""
            SELECT COUNT(*) as fan_count 
            FROM user_follow 
            WHERE followee_id = %s
        """, (user_id,))
        result = cursor.fetchone()
        fan_count = result['fan_count'] if result else 0
        
        # 关注数
        cursor.execute("""
            SELECT COUNT(*) as following_count 
            FROM user_follow 
            WHERE follower_id = %s
        """, (user_id,))
        result = cursor.fetchone()
        following_count = result['following_count'] if result else 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'post_count': post_count,
                'received_likes': received_likes,
                'my_likes': my_likes,
                'received_comments': received_comments,
                'my_comments': my_comments,
                'fans': fan_count,
                'following': following_count
            }
        })
    except Exception as e:
        print(f"获取用户统计数据错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@posts_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post_detail(post_id):
    try:
        user_id = request.args.get('user_id')
        
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT p.*, u.username as author_name, u.avatar_url
            FROM community_posts p
            LEFT JOIN user u ON p.user_id = u.user_id
            WHERE p.post_id = %s
        """, (post_id,))
        post = cursor.fetchone()
        
        if not post:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '帖子不存在'}), 404
        
        # 确保 user_id 存在
        if 'user_id' not in post or post['user_id'] is None:
            print(f"警告: 帖子 {post_id} 没有 user_id")
        
        if post.get('images'):
            try:
                post['images'] = json.loads(post['images'])
            except:
                post['images'] = []
        else:
            post['images'] = []
        
        # 查询标签
        cursor.execute("SELECT tag_name FROM post_tag WHERE post_id = %s", (post['post_id'],))
        tags = cursor.fetchall()
        post['tags'] = [t['tag_name'] for t in tags]
        
        cursor.execute("SELECT COUNT(*) as count FROM post_likes WHERE post_id = %s", (post['post_id'],))
        post['likes_count'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM community_comments WHERE post_id = %s", (post['post_id'],))
        post['comments_count'] = cursor.fetchone()['count']
        
        post['is_liked'] = False
        if user_id:
            cursor.execute(
                "SELECT 1 FROM post_likes WHERE post_id = %s AND user_id = %s",
                (post_id, user_id)
            )
            if cursor.fetchone():
                post['is_liked'] = True
        
        post['is_following'] = False
        if user_id and post.get('user_id'):
            cursor.execute(
                "SELECT 1 FROM user_follow WHERE follower_id = %s AND followee_id = %s",
                (user_id, post['user_id'])
            )
            if cursor.fetchone():
                post['is_following'] = True
        
        post['created_at'] = post['created_at'].strftime('%Y-%m-%d %H:%M:%S') if post['created_at'] else ''
        post['author_avatar'] = post['avatar_url'] if post['avatar_url'] else ''
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': post})
    except Exception as e:
        print(f"获取帖子详情错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

def save_base64_image(base64_data):
    try:
        if base64_data.startswith('data:image/'):
            header, encoded = base64_data.split(',', 1)
            img_format = header.split('/')[1].split(';')[0]
            img_data = base64.b64decode(encoded)
            filename = f"post_{uuid.uuid4().hex}.{img_format}"
            save_path = os.path.join(os.path.dirname(__file__), '..', 'images', 'tiezifengmian', filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(img_data)
            return f"/images/tiezifengmian/{filename}"
        return None
    except Exception as e:
        print(f"保存图片失败: {e}")
        return None

@posts_bp.route('/posts', methods=['POST'])
def create_post():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        images = data.get('images', [])
        tags = data.get('tags', [])
        
        if not user_id:
            return jsonify({'success': False, 'message': '用户未登录'}), 401
        
        if not title or not content:
            return jsonify({'success': False, 'message': '标题和内容不能为空'}), 400
        
        saved_paths = []
        for img in images:
            if img:
                path = save_base64_image(img)
                if path:
                    saved_paths.append(path)
        
        images_json = json.dumps(saved_paths) if saved_paths else None
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO community_posts (user_id, title, content, images, created_at, is_public, is_commentable)
            VALUES (%s, %s, %s, %s, %s, 1, 1)
        """, (user_id, title, content, images_json, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        post_id = cursor.lastrowid
        
        # 保存标签
        if tags and isinstance(tags, list):
            for tag_name in tags:
                if tag_name and isinstance(tag_name, str) and tag_name.strip():
                    cursor.execute(
                        "INSERT INTO post_tag (post_id, tag_name, created_at) VALUES (%s, %s, %s)",
                        (post_id, tag_name.strip(), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    )
            conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '发布成功', 'post_id': post_id})
    except Exception as e:
        print(f"发布帖子错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@posts_bp.route('/posts/user/<int:user_id>', methods=['GET'])
def get_user_posts(user_id):
    try:
        current_user_id = request.args.get('user_id')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        count_query = "SELECT COUNT(*) as total FROM community_posts WHERE user_id = %s"
        cursor.execute(count_query, (user_id,))
        total = cursor.fetchone()['total']
        
        offset = (page - 1) * page_size
        query = """
            SELECT p.*, u.username as author_name, u.avatar_url
            FROM community_posts p
            LEFT JOIN user u ON p.user_id = u.user_id
            WHERE p.user_id = %s
            ORDER BY p.created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (user_id, page_size, offset))
        posts = cursor.fetchall()
        
        for post in posts:
            if post.get('images'):
                try:
                    post['images'] = json.loads(post['images'])
                except:
                    post['images'] = []
            else:
                post['images'] = []
            
            cursor.execute("SELECT COUNT(*) as count FROM post_likes WHERE post_id = %s", (post['post_id'],))
            post['likes_count'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM community_comments WHERE post_id = %s", (post['post_id'],))
            post['comments_count'] = cursor.fetchone()['count']
            
            post['is_liked'] = False
            if current_user_id:
                cursor.execute(
                    "SELECT 1 FROM post_likes WHERE post_id = %s AND user_id = %s",
                    (post['post_id'], current_user_id)
                )
                if cursor.fetchone():
                    post['is_liked'] = True
            
            post['is_following'] = False
            if current_user_id and post.get('user_id'):
                cursor.execute(
                    "SELECT 1 FROM user_follow WHERE follower_id = %s AND followee_id = %s",
                    (current_user_id, post['user_id'])
                )
                if cursor.fetchone():
                    post['is_following'] = True
            
            post['created_at'] = post['created_at'].strftime('%Y-%m-%d %H:%M:%S') if post['created_at'] else ''
            post['author_avatar'] = post['avatar_url'] if post['avatar_url'] else ''
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': posts,
            'total': total,
            'page': page,
            'page_size': page_size
        })
    except Exception as e:
        print(f"获取用户帖子错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@posts_bp.route('/posts/liked', methods=['GET'])
def get_liked_posts():
    try:
        user_id = request.args.get('user_id')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        
        if not user_id:
            return jsonify({'success': False, 'message': '用户未登录'}), 401
        
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        count_query = "SELECT COUNT(*) as total FROM post_likes WHERE user_id = %s"
        cursor.execute(count_query, (user_id,))
        total = cursor.fetchone()['total']
        
        offset = (page - 1) * page_size
        query = """
            SELECT p.*, u.username as author_name, u.avatar_url
            FROM post_likes pl
            JOIN community_posts p ON pl.post_id = p.post_id
            LEFT JOIN user u ON p.user_id = u.user_id
            WHERE pl.user_id = %s
            ORDER BY pl.created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (user_id, page_size, offset))
        posts = cursor.fetchall()
        
        for post in posts:
            if post.get('images'):
                try:
                    post['images'] = json.loads(post['images'])
                except:
                    post['images'] = []
            else:
                post['images'] = []
            
            cursor.execute("SELECT COUNT(*) as count FROM post_likes WHERE post_id = %s", (post['post_id'],))
            post['likes_count'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM community_comments WHERE post_id = %s", (post['post_id'],))
            post['comments_count'] = cursor.fetchone()['count']
            
            post['is_liked'] = True
            
            post['is_following'] = False
            if post.get('user_id'):
                cursor.execute(
                    "SELECT 1 FROM user_follow WHERE follower_id = %s AND followee_id = %s",
                    (user_id, post['user_id'])
                )
                if cursor.fetchone():
                    post['is_following'] = True
            
            post['created_at'] = post['created_at'].strftime('%Y-%m-%d %H:%M:%S') if post['created_at'] else ''
            post['author_avatar'] = post['avatar_url'] if post['avatar_url'] else ''
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': posts,
            'total': total,
            'page': page,
            'page_size': page_size
        })
    except Exception as e:
        print(f"获取点赞帖子错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@posts_bp.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': '用户未登录'}), 401
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id FROM community_posts WHERE post_id = %s", (post_id,))
        post = cursor.fetchone()
        
        if not post:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '帖子不存在'}), 404
        
        if str(post[0]) != str(user_id):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '无权限删除'}), 403
        
        cursor.execute("DELETE FROM post_likes WHERE post_id = %s", (post_id,))
        
        cursor.execute("SELECT comment_id FROM community_comments WHERE post_id = %s", (post_id,))
        comments = cursor.fetchall()
        for comment in comments:
            cursor.execute("DELETE FROM comment_likes WHERE comment_id = %s", (comment[0],))
        
        cursor.execute("DELETE FROM community_comments WHERE post_id = %s", (post_id,))
        
        cursor.execute("DELETE FROM notifications WHERE post_id = %s", (post_id,))
        
        cursor.execute("DELETE FROM community_posts WHERE post_id = %s", (post_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        print(f"删除帖子错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
