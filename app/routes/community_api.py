"""
社区功能API路由
Community API Routes for SuperRAG
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.services.community_service import CommunityService
from app.models.community import PostContentType, PostStatus
import json

# 创建蓝图
community_api = Blueprint('community_api', __name__, url_prefix='/api/community')


@community_api.route('/feed', methods=['GET'])
@login_required
def get_feed():
    """获取社区时间流"""
    try:
        feed_type = request.args.get('type', 'recommended')  # recommended, following, trending, featured
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # 限制每页数量
        limit = min(limit, 50)
        
        result = CommunityService.get_feed(
            user_id=current_user.id,
            feed_type=feed_type,
            page=page,
            limit=limit
        )
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"获取时间流失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取时间流失败'}), 500


@community_api.route('/posts', methods=['POST'])
@login_required
def create_post():
    """创建社区帖子"""
    try:
        data = request.get_json()
        
        if not data or not data.get('content'):
            return jsonify({'success': False, 'message': '内容不能为空'}), 400
        
        # 处理AI内容类型
        ai_content_type = None
        if data.get('ai_content_type'):
            try:
                ai_content_type = PostContentType(data['ai_content_type'])
            except ValueError:
                return jsonify({'success': False, 'message': '无效的AI内容类型'}), 400
        
        result = CommunityService.create_post(
            user_id=current_user.id,
            content=data['content'],
            ai_prompt=data.get('ai_prompt'),
            ai_content_type=ai_content_type,
            ai_content_data=data.get('ai_content_data'),
            conversation_id=data.get('conversation_id'),
            pdf_url=data.get('pdf_url'),
            tags=data.get('tags', []),
            status=PostStatus.PUBLISHED
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"创建帖子失败: {str(e)}")
        return jsonify({'success': False, 'message': '创建帖子失败'}), 500


@community_api.route('/posts/<int:post_id>', methods=['GET'])
@login_required
def get_post_detail(post_id):
    """获取帖子详情"""
    try:
        result = CommunityService.get_post_detail(post_id, current_user.id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        current_app.logger.error(f"获取帖子详情失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取帖子详情失败'}), 500


@community_api.route('/posts/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    """点赞/取消点赞帖子"""
    try:
        result = CommunityService.like_post(current_user.id, post_id)
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"点赞操作失败: {str(e)}")
        return jsonify({'success': False, 'message': '点赞操作失败'}), 500


@community_api.route('/posts/<int:post_id>/comments', methods=['GET'])
@login_required
def get_post_comments(post_id):
    """获取帖子评论"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 50)
        
        result = CommunityService.get_post_comments(post_id, page, limit)
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"获取评论失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取评论失败'}), 500


@community_api.route('/posts/<int:post_id>/comments', methods=['POST'])
@login_required
def comment_post(post_id):
    """评论帖子"""
    try:
        data = request.get_json()
        
        if not data or not data.get('content'):
            return jsonify({'success': False, 'message': '评论内容不能为空'}), 400
        
        result = CommunityService.comment_post(
            current_user.id, 
            post_id, 
            data['content']
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"评论失败: {str(e)}")
        return jsonify({'success': False, 'message': '评论失败'}), 500


@community_api.route('/posts/<int:post_id>/share', methods=['POST'])
@login_required
def share_post(post_id):
    """转发帖子"""
    try:
        data = request.get_json() or {}
        
        result = CommunityService.share_post(
            current_user.id, 
            post_id, 
            data.get('content')
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"转发失败: {str(e)}")
        return jsonify({'success': False, 'message': '转发失败'}), 500


@community_api.route('/posts/<int:post_id>/bookmark', methods=['POST'])
@login_required
def bookmark_post(post_id):
    """收藏/取消收藏帖子"""
    try:
        result = CommunityService.bookmark_post(current_user.id, post_id)
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"收藏操作失败: {str(e)}")
        return jsonify({'success': False, 'message': '收藏操作失败'}), 500


@community_api.route('/users/<int:user_id>/follow', methods=['POST'])
@login_required
def follow_user(user_id):
    """关注用户"""
    try:
        result = CommunityService.follow_user(current_user.id, user_id)
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"关注失败: {str(e)}")
        return jsonify({'success': False, 'message': '关注失败'}), 500


@community_api.route('/users/<int:user_id>/unfollow', methods=['POST'])
@login_required
def unfollow_user(user_id):
    """取消关注用户"""
    try:
        result = CommunityService.unfollow_user(current_user.id, user_id)
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"取消关注失败: {str(e)}")
        return jsonify({'success': False, 'message': '取消关注失败'}), 500


@community_api.route('/users/<int:user_id>/posts', methods=['GET'])
@login_required
def get_user_posts(user_id):
    """获取用户的帖子"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 50)
        
        result = CommunityService.get_user_posts(user_id, page, limit)
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"获取用户帖子失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取用户帖子失败'}), 500


@community_api.route('/users/<int:user_id>/profile', methods=['GET'])
@login_required
def get_user_profile(user_id):
    """获取用户资料"""
    try:
        from app.models.user import User
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 检查是否关注
        is_following = current_user.is_following(user_id) if hasattr(current_user, 'is_following') else False
        
        profile_data = user.to_dict()
        profile_data['is_following'] = is_following
        profile_data['is_self'] = (current_user.id == user_id)
        
        return jsonify({
            'success': True,
            'user': profile_data
        })
        
    except Exception as e:
        current_app.logger.error(f"获取用户资料失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取用户资料失败'}), 500


@community_api.route('/bookmarks', methods=['GET'])
@login_required
def get_user_bookmarks():
    """获取用户收藏的帖子"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 50)
        
        result = CommunityService.get_user_bookmarks(current_user.id, page, limit)
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"获取收藏失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取收藏失败'}), 500


@community_api.route('/search', methods=['GET'])
@login_required
def search_posts():
    """搜索帖子"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'success': False, 'message': '搜索关键词不能为空'}), 400
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 50)
        
        result = CommunityService.search_posts(query, page, limit)
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"搜索失败: {str(e)}")
        return jsonify({'success': False, 'message': '搜索失败'}), 500


@community_api.route('/trending/tags', methods=['GET'])
@login_required
def get_trending_tags():
    """获取热门标签"""
    try:
        limit = int(request.args.get('limit', 10))
        limit = min(limit, 20)
        
        result = CommunityService.get_trending_tags(limit)
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"获取热门标签失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取热门标签失败'}), 500


@community_api.route('/import/conversation', methods=['POST'])
@login_required
def import_conversation():
    """从对话导入创建帖子"""
    try:
        data = request.get_json()
        
        if not data or not data.get('conversation_id') or not data.get('content'):
            return jsonify({
                'success': False, 
                'message': '对话ID和内容不能为空'
            }), 400
        
        result = CommunityService.import_conversation_to_post(
            user_id=current_user.id,
            conversation_id=data['conversation_id'],
            content=data['content'],
            selected_messages=data.get('selected_messages')
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"导入对话失败: {str(e)}")
        return jsonify({'success': False, 'message': '导入对话失败'}), 500


@community_api.route('/stats', methods=['GET'])
@login_required
def get_community_stats():
    """获取社区统计数据"""
    try:
        from app.models.community import CommunityPost, CommunityInteraction
        from app.models.user import User
        from datetime import datetime, timedelta
        
        # 今日新增帖子
        today = datetime.utcnow().date()
        today_posts = CommunityPost.query.filter(
            CommunityPost.created_at >= today,
            CommunityPost.status == PostStatus.PUBLISHED
        ).count()
        
        # 总帖子数
        total_posts = CommunityPost.query.filter_by(status=PostStatus.PUBLISHED).count()
        
        # 总用户数
        total_users = User.query.count()
        
        # 今日活跃用户（有互动的用户）
        today_active_users = CommunityInteraction.query.filter(
            CommunityInteraction.created_at >= today
        ).distinct(CommunityInteraction.user_id).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'today_posts': today_posts,
                'total_posts': total_posts,
                'total_users': total_users,
                'today_active_users': today_active_users
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取统计数据失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取统计数据失败'}), 500 