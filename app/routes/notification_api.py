"""
通知和反馈API路由
"""
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import json

from app.database import db
from app.models.notification import Notification, UserFeedback, NotificationView, NotificationStatus, FeedbackStatus
from app.decorators import require_admin

notification_api = Blueprint('notification_api', __name__)

@notification_api.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    """获取用户通知列表"""
    try:
        # 获取已发布的通知
        notifications = Notification.query.filter(
            Notification.status == NotificationStatus.PUBLISHED,
            db.or_(
                Notification.expire_at.is_(None),
                Notification.expire_at > datetime.utcnow()
            ),
            db.or_(
                Notification.publish_at.is_(None),
                Notification.publish_at <= datetime.utcnow()
            )
        ).order_by(Notification.priority.desc(), Notification.created_at.desc()).all()
        
        # 获取用户已查看的通知ID
        viewed_notifications = set(
            view.notification_id for view in NotificationView.query.filter_by(user_id=current_user.id).all()
        )
        
        result = []
        for notification in notifications:
            data = notification.to_dict()
            data['is_viewed'] = notification.id in viewed_notifications
            result.append(data)
        
        return jsonify({
            'success': True,
            'notifications': result
        })
        
    except Exception as e:
        current_app.logger.error(f"获取通知列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取通知失败'
        }), 500

@notification_api.route('/api/notifications/<int:notification_id>/view', methods=['POST'])
@login_required  
def mark_notification_viewed(notification_id):
    """标记通知为已查看"""
    try:
        # 检查通知是否存在
        notification = Notification.query.get_or_404(notification_id)
        
        # 检查是否已经查看过
        existing_view = NotificationView.query.filter_by(
            notification_id=notification_id,
            user_id=current_user.id
        ).first()
        
        if not existing_view:
            # 创建查看记录
            view = NotificationView(
                notification_id=notification_id,
                user_id=current_user.id
            )
            db.session.add(view)
            
            # 更新通知查看次数
            notification.view_count += 1
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '标记为已查看'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"标记通知已查看失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': '操作失败'
        }), 500

@notification_api.route('/api/notifications/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    """获取未读通知数量"""
    try:
        # 获取所有已发布的有效通知
        all_notifications = Notification.query.filter(
            Notification.status == NotificationStatus.PUBLISHED,
            db.or_(
                Notification.expire_at.is_(None),
                Notification.expire_at > datetime.utcnow()
            ),
            db.or_(
                Notification.publish_at.is_(None),
                Notification.publish_at <= datetime.utcnow()
            )
        ).count()
        
        # 获取用户已查看的通知数量
        viewed_count = NotificationView.query.filter_by(user_id=current_user.id).count()
        
        unread_count = max(0, all_notifications - viewed_count)
        
        return jsonify({
            'success': True,
            'unread_count': unread_count
        })
        
    except Exception as e:
        current_app.logger.error(f"获取未读通知数量失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取失败'
        }), 500

@notification_api.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """提交用户反馈"""
    try:
        data = request.get_json()
        
        if not data or not data.get('title') or not data.get('content'):
            return jsonify({
                'success': False,
                'error': '标题和内容不能为空'
            }), 400
        
        # 创建反馈记录
        feedback = UserFeedback(
            title=data['title'].strip(),
            content=data['content'].strip(),
            contact_info=data.get('contact_info', '').strip(),
            category=data.get('category', 'general'),
            user_id=current_user.id if current_user.is_authenticated else None,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '反馈提交成功，感谢您的建议！',
            'feedback_id': feedback.id
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"提交反馈失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': '提交失败，请稍后重试'
        }), 500

@notification_api.route('/api/feedback/<int:feedback_id>', methods=['GET'])
@login_required
def get_feedback(feedback_id):
    """获取反馈详情（仅用户自己的反馈）"""
    try:
        feedback = UserFeedback.query.filter_by(
            id=feedback_id,
            user_id=current_user.id
        ).first_or_404()
        
        return jsonify({
            'success': True,
            'feedback': feedback.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"获取反馈详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取失败'
        }), 500

@notification_api.route('/api/user/feedbacks', methods=['GET'])
@login_required
def get_user_feedbacks():
    """获取用户的反馈列表"""
    try:
        feedbacks = UserFeedback.query.filter_by(
            user_id=current_user.id
        ).order_by(UserFeedback.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'feedbacks': [feedback.to_dict() for feedback in feedbacks]
        })
        
    except Exception as e:
        current_app.logger.error(f"获取用户反馈列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取失败'
        }), 500 