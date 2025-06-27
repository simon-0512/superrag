"""
社区功能服务层
Community Service for SuperRAG
"""

from datetime import datetime, timedelta
from sqlalchemy import desc, func, and_, or_
from sqlalchemy.orm import joinedload
from app.database import db
from app.models.community import CommunityPost, CommunityInteraction, UserFollow, PostContentType, PostStatus, InteractionType
from app.models.user import User
from app.models.knowledge_base import Conversation
import json
import re


class CommunityService:
    """社区功能服务类"""
    
    @staticmethod
    def create_post(user_id, content, ai_prompt=None, ai_content_type=None, 
                   ai_content_data=None, conversation_id=None, pdf_url=None, 
                   tags=None, status=PostStatus.PUBLISHED):
        """创建社区帖子"""
        try:
            # 验证内容长度
            if len(content) > 140:
                return {'success': False, 'message': '文字描述不能超过140字'}
            
            # 创建帖子
            post = CommunityPost(
                user_id=user_id,
                content=content,
                ai_prompt=ai_prompt,
                ai_content_type=ai_content_type,
                ai_content_data=ai_content_data,
                conversation_id=conversation_id,
                pdf_url=pdf_url,
                tags=tags or [],
                status=status
            )
            
            db.session.add(post)
            db.session.commit()
            
            # 更新用户帖子数量
            user = User.query.get(user_id)
            if user:
                user.update_post_count()
                db.session.commit()
            
            return {'success': True, 'post': post.to_dict()}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'创建帖子失败: {str(e)}'}
    
    @staticmethod
    def get_feed(user_id=None, feed_type='recommended', page=1, limit=20):
        """获取时间流数据"""
        try:
            query = CommunityPost.query.filter_by(status=PostStatus.PUBLISHED)
            
            # 根据类型筛选
            if feed_type == 'following' and user_id:
                # 关注的用户的帖子
                following_ids = db.session.query(UserFollow.following_id).filter_by(follower_id=user_id).subquery()
                query = query.filter(CommunityPost.user_id.in_(following_ids))
            elif feed_type == 'trending':
                # 热门帖子（按互动量排序）
                query = query.filter(
                    CommunityPost.created_at >= datetime.utcnow() - timedelta(days=7)
                ).order_by(
                    desc(CommunityPost.like_count + CommunityPost.comment_count + CommunityPost.share_count)
                )
            elif feed_type == 'featured':
                # 精选帖子
                query = query.filter_by(is_featured=True)
            else:
                # 推荐算法（简单版本：时间 + 互动量）
                query = query.order_by(
                    desc(CommunityPost.created_at),
                    desc(CommunityPost.like_count)
                )
            
            # 分页
            posts = query.options(
                joinedload(CommunityPost.user),
                joinedload(CommunityPost.conversation)
            ).offset((page - 1) * limit).limit(limit).all()
            
            # 增加浏览量
            for post in posts:
                post.view_count += 1
            db.session.commit()
            
            return {
                'success': True,
                'posts': [post.to_dict() for post in posts],
                'total': query.count(),
                'page': page,
                'limit': limit
            }
            
        except Exception as e:
            return {'success': False, 'message': f'获取时间流失败: {str(e)}'}
    
    @staticmethod
    def get_post_detail(post_id, user_id=None):
        """获取帖子详情"""
        try:
            post = CommunityPost.query.options(
                joinedload(CommunityPost.user),
                joinedload(CommunityPost.conversation),
                joinedload(CommunityPost.interactions)
            ).filter_by(id=post_id, status=PostStatus.PUBLISHED).first()
            
            if not post:
                return {'success': False, 'message': '帖子不存在'}
            
            # 增加浏览量
            post.view_count += 1
            db.session.commit()
            
            # 获取用户交互状态
            user_interactions = {}
            if user_id:
                interactions = CommunityInteraction.query.filter_by(
                    user_id=user_id, 
                    post_id=post_id
                ).all()
                user_interactions = {
                    interaction.interaction_type.value: True 
                    for interaction in interactions
                }
            
            post_data = post.to_dict()
            post_data['user_interactions'] = user_interactions
            
            return {'success': True, 'post': post_data}
            
        except Exception as e:
            return {'success': False, 'message': f'获取帖子详情失败: {str(e)}'}
    
    @staticmethod
    def like_post(user_id, post_id):
        """点赞/取消点赞帖子"""
        try:
            post = CommunityPost.query.get(post_id)
            if not post:
                return {'success': False, 'message': '帖子不存在'}
            
            # 检查是否已点赞
            existing_like = CommunityInteraction.query.filter_by(
                user_id=user_id,
                post_id=post_id,
                interaction_type=InteractionType.LIKE
            ).first()
            
            if existing_like:
                # 取消点赞
                db.session.delete(existing_like)
                post.like_count = max(post.like_count - 1, 0)
                action = 'unliked'
            else:
                # 点赞
                like = CommunityInteraction(
                    user_id=user_id,
                    post_id=post_id,
                    interaction_type=InteractionType.LIKE
                )
                db.session.add(like)
                post.like_count += 1
                action = 'liked'
            
            db.session.commit()
            
            # 更新帖子作者的获赞总数
            post_author = User.query.get(post.user_id)
            if post_author:
                post_author.update_like_count()
                db.session.commit()
            
            return {
                'success': True, 
                'action': action, 
                'like_count': post.like_count
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'点赞操作失败: {str(e)}'}
    
    @staticmethod
    def comment_post(user_id, post_id, content):
        """评论帖子"""
        try:
            post = CommunityPost.query.get(post_id)
            if not post:
                return {'success': False, 'message': '帖子不存在'}
            
            if not content or len(content.strip()) == 0:
                return {'success': False, 'message': '评论内容不能为空'}
            
            # 创建评论
            comment = CommunityInteraction(
                user_id=user_id,
                post_id=post_id,
                interaction_type=InteractionType.COMMENT,
                content=content.strip()
            )
            
            db.session.add(comment)
            post.comment_count += 1
            db.session.commit()
            
            return {
                'success': True, 
                'comment': comment.to_dict(),
                'comment_count': post.comment_count
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'评论失败: {str(e)}'}
    
    @staticmethod
    def share_post(user_id, post_id, content=None):
        """转发帖子"""
        try:
            post = CommunityPost.query.get(post_id)
            if not post:
                return {'success': False, 'message': '帖子不存在'}
            
            # 检查是否已转发
            existing_share = CommunityInteraction.query.filter_by(
                user_id=user_id,
                post_id=post_id,
                interaction_type=InteractionType.SHARE
            ).first()
            
            if existing_share:
                return {'success': False, 'message': '已经转发过这个帖子'}
            
            # 创建转发记录
            share = CommunityInteraction(
                user_id=user_id,
                post_id=post_id,
                interaction_type=InteractionType.SHARE,
                content=content
            )
            
            db.session.add(share)
            post.share_count += 1
            db.session.commit()
            
            return {
                'success': True, 
                'share': share.to_dict(),
                'share_count': post.share_count
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'转发失败: {str(e)}'}
    
    @staticmethod
    def bookmark_post(user_id, post_id):
        """收藏/取消收藏帖子"""
        try:
            post = CommunityPost.query.get(post_id)
            if not post:
                return {'success': False, 'message': '帖子不存在'}
            
            # 检查是否已收藏
            existing_bookmark = CommunityInteraction.query.filter_by(
                user_id=user_id,
                post_id=post_id,
                interaction_type=InteractionType.BOOKMARK
            ).first()
            
            if existing_bookmark:
                # 取消收藏
                db.session.delete(existing_bookmark)
                action = 'unbookmarked'
            else:
                # 收藏
                bookmark = CommunityInteraction(
                    user_id=user_id,
                    post_id=post_id,
                    interaction_type=InteractionType.BOOKMARK
                )
                db.session.add(bookmark)
                action = 'bookmarked'
            
            db.session.commit()
            
            return {'success': True, 'action': action}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'收藏操作失败: {str(e)}'}
    
    @staticmethod
    def get_post_comments(post_id, page=1, limit=20):
        """获取帖子评论"""
        try:
            comments = CommunityInteraction.query.options(
                joinedload(CommunityInteraction.user)
            ).filter_by(
                post_id=post_id,
                interaction_type=InteractionType.COMMENT
            ).order_by(
                desc(CommunityInteraction.created_at)
            ).offset((page - 1) * limit).limit(limit).all()
            
            total = CommunityInteraction.query.filter_by(
                post_id=post_id,
                interaction_type=InteractionType.COMMENT
            ).count()
            
            return {
                'success': True,
                'comments': [comment.to_dict() for comment in comments],
                'total': total,
                'page': page,
                'limit': limit
            }
            
        except Exception as e:
            return {'success': False, 'message': f'获取评论失败: {str(e)}'}
    
    @staticmethod
    def follow_user(follower_id, following_id):
        """关注用户"""
        try:
            if follower_id == following_id:
                return {'success': False, 'message': '不能关注自己'}
            
            follower = User.query.get(follower_id)
            following = User.query.get(following_id)
            
            if not follower or not following:
                return {'success': False, 'message': '用户不存在'}
            
            success = follower.follow(following_id)
            if success:
                db.session.commit()
                return {'success': True, 'message': '关注成功'}
            else:
                return {'success': False, 'message': '已经关注过这个用户'}
                
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'关注失败: {str(e)}'}
    
    @staticmethod
    def unfollow_user(follower_id, following_id):
        """取消关注用户"""
        try:
            follower = User.query.get(follower_id)
            if not follower:
                return {'success': False, 'message': '用户不存在'}
            
            success = follower.unfollow(following_id)
            if success:
                db.session.commit()
                return {'success': True, 'message': '取消关注成功'}
            else:
                return {'success': False, 'message': '没有关注过这个用户'}
                
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'取消关注失败: {str(e)}'}
    
    @staticmethod
    def get_user_posts(user_id, page=1, limit=20):
        """获取用户的帖子"""
        try:
            posts = CommunityPost.query.options(
                joinedload(CommunityPost.user)
            ).filter_by(
                user_id=user_id,
                status=PostStatus.PUBLISHED
            ).order_by(
                desc(CommunityPost.created_at)
            ).offset((page - 1) * limit).limit(limit).all()
            
            total = CommunityPost.query.filter_by(
                user_id=user_id,
                status=PostStatus.PUBLISHED
            ).count()
            
            return {
                'success': True,
                'posts': [post.to_dict() for post in posts],
                'total': total,
                'page': page,
                'limit': limit
            }
            
        except Exception as e:
            return {'success': False, 'message': f'获取用户帖子失败: {str(e)}'}
    
    @staticmethod
    def get_user_bookmarks(user_id, page=1, limit=20):
        """获取用户收藏的帖子"""
        try:
            bookmarks = db.session.query(CommunityPost).join(
                CommunityInteraction,
                and_(
                    CommunityPost.id == CommunityInteraction.post_id,
                    CommunityInteraction.user_id == user_id,
                    CommunityInteraction.interaction_type == InteractionType.BOOKMARK
                )
            ).options(
                joinedload(CommunityPost.user)
            ).filter(
                CommunityPost.status == PostStatus.PUBLISHED
            ).order_by(
                desc(CommunityInteraction.created_at)
            ).offset((page - 1) * limit).limit(limit).all()
            
            total = db.session.query(CommunityPost).join(
                CommunityInteraction,
                and_(
                    CommunityPost.id == CommunityInteraction.post_id,
                    CommunityInteraction.user_id == user_id,
                    CommunityInteraction.interaction_type == InteractionType.BOOKMARK
                )
            ).filter(
                CommunityPost.status == PostStatus.PUBLISHED
            ).count()
            
            return {
                'success': True,
                'posts': [post.to_dict() for post in bookmarks],
                'total': total,
                'page': page,
                'limit': limit
            }
            
        except Exception as e:
            return {'success': False, 'message': f'获取收藏失败: {str(e)}'}
    
    @staticmethod
    def search_posts(query, page=1, limit=20):
        """搜索帖子"""
        try:
            # 简单的文本搜索
            search_filter = or_(
                CommunityPost.content.contains(query),
                CommunityPost.ai_prompt.contains(query),
                CommunityPost.tags.contains(query)
            )
            
            posts = CommunityPost.query.options(
                joinedload(CommunityPost.user)
            ).filter(
                and_(
                    CommunityPost.status == PostStatus.PUBLISHED,
                    search_filter
                )
            ).order_by(
                desc(CommunityPost.created_at)
            ).offset((page - 1) * limit).limit(limit).all()
            
            total = CommunityPost.query.filter(
                and_(
                    CommunityPost.status == PostStatus.PUBLISHED,
                    search_filter
                )
            ).count()
            
            return {
                'success': True,
                'posts': [post.to_dict() for post in posts],
                'total': total,
                'page': page,
                'limit': limit,
                'query': query
            }
            
        except Exception as e:
            return {'success': False, 'message': f'搜索失败: {str(e)}'}
    
    @staticmethod
    def get_trending_tags(limit=10):
        """获取热门标签"""
        try:
            # 这里需要更复杂的查询来统计标签频率
            # 简化版本：获取最近的标签
            recent_posts = CommunityPost.query.filter(
                and_(
                    CommunityPost.status == PostStatus.PUBLISHED,
                    CommunityPost.created_at >= datetime.utcnow() - timedelta(days=7),
                    CommunityPost.tags.is_not(None)
                )
            ).limit(100).all()
            
            tag_count = {}
            for post in recent_posts:
                if post.tags:
                    for tag in post.tags:
                        tag_count[tag] = tag_count.get(tag, 0) + 1
            
            # 按频率排序
            trending_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:limit]
            
            return {
                'success': True,
                'tags': [{'name': tag, 'count': count} for tag, count in trending_tags]
            }
            
        except Exception as e:
            return {'success': False, 'message': f'获取热门标签失败: {str(e)}'}
    
    @staticmethod
    def import_conversation_to_post(user_id, conversation_id, content, selected_messages=None):
        """从对话导入创建帖子"""
        try:
            conversation = Conversation.query.get(conversation_id)
            if not conversation:
                return {'success': False, 'message': '对话不存在'}
            
            if conversation.user_id != user_id:
                return {'success': False, 'message': '无权限访问此对话'}
            
            # 准备AI内容数据
            ai_content_data = {
                'conversation_id': conversation_id,
                'conversation_title': conversation.title,
                'selected_messages': selected_messages or [],
                'import_time': datetime.utcnow().isoformat()
            }
            
            # 创建帖子
            return CommunityService.create_post(
                user_id=user_id,
                content=content,
                ai_content_type=PostContentType.CONVERSATION,
                ai_content_data=ai_content_data,
                conversation_id=conversation_id,
                tags=['AI对话', '知识分享']
            )
            
        except Exception as e:
            return {'success': False, 'message': f'导入对话失败: {str(e)}'} 