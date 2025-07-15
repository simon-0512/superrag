"""
社区功能API路由
Community API Routes for SuperRAG
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.services.community_service import CommunityService
from app.models.community import PostContentType, PostStatus
from app.decorators import require_read_permission, require_write_permission
import json
from datetime import datetime

# 创建蓝图
community_api = Blueprint('community_api', __name__, url_prefix='/api/community')


@community_api.route('/feed', methods=['GET'])
@login_required
@require_read_permission
def get_feed():
    """获取社区时间流"""
    import time
    start_time = time.time()
    current_app.logger.info(f"🔍 [DEBUG] 开始获取时间流 - {time.strftime('%H:%M:%S')}")
    
    try:
        feed_type = request.args.get('type', 'recommended')  # recommended, following, trending, featured
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # 限制每页数量
        limit = min(limit, 50)
        
        service_start = time.time()
        result = CommunityService.get_feed(
            user_id=current_user.id,
            feed_type=feed_type,
            page=page,
            limit=limit
        )
        service_time = (time.time() - service_start) * 1000
        
        total_time = (time.time() - start_time) * 1000
        current_app.logger.info(f"✅ [DEBUG] 时间流API完成: 服务层{service_time:.1f}ms, 总耗时{total_time:.1f}ms")
        
        return jsonify(result)
        
    except Exception as e:
        error_time = (time.time() - start_time) * 1000
        current_app.logger.error(f"❌ [DEBUG] 获取时间流失败: {str(e)} (耗时: {error_time:.1f}ms)")
        return jsonify({'success': False, 'message': '获取时间流失败'}), 500


@community_api.route('/posts', methods=['POST'])
@login_required
@require_write_permission
def create_post():
    """创建社区帖子"""
    try:
        data = request.get_json()
        
        if not data or not data.get('content'):
            return jsonify({'success': False, 'message': '内容不能为空'}), 400
        
        # 处理不同的参数格式
        ai_content_type = data.get('ai_content_type')
        ai_content_data_input = data.get('ai_content_data', {})
        conversation_id = ai_content_data_input.get('conversation_id') if ai_content_data_input else None
        
        # 如果是对话分享，需要获取对话数据
        ai_content_data = None
        if ai_content_type == 'conversation' and conversation_id:
            try:
                from app.models import Conversation, Message
                
                # 验证对话存在且属于当前用户
                conversation = Conversation.query.filter_by(
                    id=conversation_id,
                    user_id=current_user.id
                ).first()
                
                if not conversation:
                    return jsonify({'success': False, 'message': '对话不存在或无权限访问'}), 400
                
                # 获取对话消息
                messages = Message.query.filter_by(
                    conversation_id=conversation_id
                ).order_by(Message.created_at.asc()).all()
                
                # 构建对话数据 - V0.3.0 包含配置参数
                ai_content_data = {
                    'conversation_id': conversation_id,
                    'conversation_title': conversation.title,
                    'conversation_config': {
                        'model_name': conversation.model_name,
                        'model_display_name': conversation.get_model_display_name(),
                        'temperature': conversation.temperature,
                        'temperature_display_name': conversation.get_temperature_display_name(),
                        'max_tokens': conversation.max_tokens,
                        'system_prompt': conversation.system_prompt
                    },
                    'messages': [{
                        'id': msg.id,
                        'role': msg.role,
                        'content': msg.content,
                        'created_at': msg.created_at.isoformat()
                    } for msg in messages],
                    'import_time': datetime.now().isoformat()
                }
                
            except Exception as e:
                current_app.logger.error(f"获取对话数据失败: {e}")
                return jsonify({'success': False, 'message': '获取对话数据失败'}), 500
        
        # 创建帖子
        result = CommunityService.create_post(
            user_id=current_user.id,
            content=data['content'],
            ai_prompt=data.get('ai_prompt'),
            ai_content_type=PostContentType.CONVERSATION if ai_content_type == 'conversation' else None,
            ai_content_data=json.dumps(ai_content_data) if ai_content_data else None,
            conversation_id=conversation_id if ai_content_type == 'conversation' else None,
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
@require_read_permission
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
@require_write_permission
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
@require_read_permission
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
@require_write_permission
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
@require_write_permission
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
@require_write_permission
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
@require_write_permission
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
@require_write_permission
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
@require_read_permission
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
@require_read_permission
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
@require_read_permission
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
@require_read_permission
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
@require_read_permission
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
@require_write_permission
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
@require_read_permission
def get_community_stats():
    """获取社区统计数据"""
    try:
        result = CommunityService.get_community_stats()
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"获取统计数据失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取统计数据失败'}), 500


@community_api.route('/posts/<post_id>/conversation', methods=['GET'])
@login_required
@require_read_permission
def get_post_conversation(post_id):
    """获取帖子对话详情"""
    try:
        from app.models.community import CommunityPost
        from app.models import Conversation, Message
        
        # 获取帖子
        post = CommunityPost.query.filter_by(
            id=post_id,
            status=PostStatus.PUBLISHED
        ).first()
        
        if not post:
            return jsonify({'success': False, 'message': '帖子不存在'}), 404
        
        # 检查是否是对话分享
        if post.ai_content_type != PostContentType.CONVERSATION or not post.conversation_id:
            return jsonify({'success': False, 'message': '这不是对话分享帖子'}), 400
        
        # 获取对话
        conversation = Conversation.query.get(post.conversation_id)
        if not conversation:
            return jsonify({'success': False, 'message': '对话不存在'}), 404
        
        # 获取对话消息
        messages = Message.query.filter_by(
            conversation_id=conversation.id
        ).order_by(Message.created_at.asc()).all()
        
        # 构建响应数据
        conversation_data = {
            'id': conversation.id,
            'title': conversation.title,
            'created_at': conversation.created_at.isoformat(),
            'conversation_config': {
                'model_name': conversation.model_name,
                'model_display_name': conversation.get_model_display_name(),
                'temperature': conversation.temperature,
                'temperature_display_name': conversation.get_temperature_display_name(),
                'max_tokens': conversation.max_tokens,
                'system_prompt': conversation.system_prompt
            },
            'messages': []
        }
        
        for msg in messages:
            # V0.3.1 修复：添加思考过程字段到社区分享的对话数据中
            thinking_process = None
            if msg.msg_metadata and isinstance(msg.msg_metadata, dict):
                thinking_process = msg.msg_metadata.get('thinking_process')
            
            message_data = {
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'thinking_process': thinking_process,  # V0.3.1 新增：思考过程字段
                'created_at': msg.created_at.isoformat(),
                'tokens': getattr(msg, 'tokens', 0)
            }
            conversation_data['messages'].append(message_data)
        
        return jsonify({
            'success': True,
            'post': {
                'id': post.id,
                'content': post.content,
                'ai_prompt': post.ai_prompt,
                'created_at': post.created_at.isoformat(),
                'user': {
                    'username': post.user.username,
                    'nickname': post.user.nickname
                }
            },
            'conversation': conversation_data
        })
        
    except Exception as e:
        current_app.logger.error(f"获取对话详情失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取对话详情失败'}), 500 