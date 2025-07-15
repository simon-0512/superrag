"""
管理员后台数据管理路由
仅限管理员访问的数据可视化和管理工具
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import text, desc, asc
from datetime import datetime, timedelta
import json

from app.database import db
from app.models.user import User, UserRole
from app.models.knowledge_base import Conversation, Message
from app.models.community import CommunityPost, CommunityInteraction, UserFollow
from app.utils.timezone_utils import get_beijing_time_for_db, format_beijing_time
from app.models.notification import Notification, UserFeedback, NotificationView, NotificationType, NotificationStatus, FeedbackStatus
from app.decorators import inject_unread_notifications_count

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('需要管理员权限才能访问此页面', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
@inject_unread_notifications_count
def dashboard():
    """管理员仪表板"""
    try:
        # 统计数据
        stats = {
            'users': {
                'total': User.query.count(),
                'active': User.query.filter_by(is_active=True).count(),
                'admin': User.query.filter_by(role=UserRole.ADMIN).count(),
                'tester': User.query.filter_by(role=UserRole.TESTER).count(),
                'vip': User.query.filter_by(role=UserRole.VIP).count(),
                'normal': User.query.filter_by(role=UserRole.USER).count(),
            },
            'conversations': {
                'total': Conversation.query.count(),
                'active': Conversation.query.filter_by(is_active=True).count(),
                'messages': Message.query.count(),
            },
            'community': {
                'posts': CommunityPost.query.count(),
                'interactions': CommunityInteraction.query.count(),
                'follows': UserFollow.query.count(),
            }
        }
        
        # 最近数据
        recent_data = {
            'users': User.query.order_by(desc(User.created_at)).limit(5).all(),
            'conversations': Conversation.query.order_by(desc(Conversation.created_at)).limit(5).all(),
            'posts': CommunityPost.query.order_by(desc(CommunityPost.created_at)).limit(5).all(),
        }
        
        # 趋势数据
        now = get_beijing_time_for_db()
        trend_data = {
            'labels': [],
            'users': [],
            'conversations': [],
            'posts': []
        }
        
        # 获取最近7天的数据
        for i in range(6, -1, -1):
            day_start = now - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            # 添加日期标签
            if i == 0:
                trend_data['labels'].append('今天')
            else:
                trend_data['labels'].append(f'{i}天前')
            
            # 新增用户数
            new_users = User.query.filter(
                User.created_at >= day_start,
                User.created_at < day_end
            ).count()
            trend_data['users'].append(new_users)
            
            # 新增对话数
            new_conversations = Conversation.query.filter(
                Conversation.created_at >= day_start,
                Conversation.created_at < day_end
            ).count()
            trend_data['conversations'].append(new_conversations)
            
            # 新增帖子数
            new_posts = CommunityPost.query.filter(
                CommunityPost.created_at >= day_start,
                CommunityPost.created_at < day_end
            ).count()
            trend_data['posts'].append(new_posts)
        
        return render_template('admin/dashboard.html', 
                             stats=stats, 
                             recent_data=recent_data,
                             trend_data=trend_data)
        
    except Exception as e:
        flash(f'获取统计数据失败: {str(e)}', 'error')
        return render_template('admin/dashboard.html', 
                             stats={}, 
                             recent_data={},
                             trend_data={'labels': [], 'users': [], 'conversations': [], 'posts': []})

# =============== 用户管理 ===============

@admin_bp.route('/users')
@login_required
@admin_required
@inject_unread_notifications_count
def users():
    """用户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    
    query = User.query
    
    # 搜索过滤
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.nickname.contains(search))
        )
    
    # 角色过滤
    if role_filter:
        query = query.filter_by(role=UserRole(role_filter))
    
    # 分页
    users_page = query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users.html', 
                         users=users_page, 
                         search=search, 
                         role_filter=role_filter,
                         roles=UserRole)

@admin_bp.route('/users/<user_id>')
@login_required
@admin_required
@inject_unread_notifications_count
def user_detail(user_id):
    """用户详情"""
    user = User.query.get_or_404(user_id)
    
    # 用户统计
    user_stats = {
        'conversations_count': Conversation.query.filter_by(user_id=user_id).count(),
        'messages_count': db.session.query(Message).join(Conversation).filter(
            Conversation.user_id == user_id
        ).count(),
        'posts_count': CommunityPost.query.filter_by(user_id=user_id).count(),
        'interactions_count': CommunityInteraction.query.filter_by(user_id=user_id).count(),
    }
    
    return render_template('admin/user_detail.html', user=user, stats=user_stats)

@admin_bp.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
@inject_unread_notifications_count
def edit_user(user_id):
    """编辑用户"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # 更新基本信息
            if 'username' in data:
                # 检查用户名是否已存在
                existing = User.query.filter(User.username == data['username'], User.id != user_id).first()
                if existing:
                    return jsonify({'success': False, 'message': '用户名已存在'})
                user.username = data['username']
            
            if 'email' in data:
                # 检查邮箱是否已存在
                existing = User.query.filter(User.email == data['email'], User.id != user_id).first()
                if existing:
                    return jsonify({'success': False, 'message': '邮箱已存在'})
                user.email = data['email']
            
            if 'nickname' in data:
                user.nickname = data['nickname']
            
            if 'role' in data:
                user.set_role(data['role'])
            
            if 'is_active' in data:
                user.is_active = data['is_active']
            
            if 'is_verified' in data:
                user.is_verified = data['is_verified']
            
            user.updated_at = get_beijing_time_for_db()
            db.session.commit()
            
            return jsonify({'success': True, 'message': '用户信息更新成功'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})
    
    return render_template('admin/edit_user.html', user=user, roles=UserRole)

@admin_bp.route('/users/<user_id>/toggle_disable', methods=['POST'])
@login_required
@admin_required
def toggle_disable_user(user_id):
    """禁用/启用用户"""
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': '不能禁用自己的账号'})
    
    try:
        user = User.query.get_or_404(user_id)
        
        if user.is_disabled():
            user.enable_user()
            message = f'用户 {user.username} 已启用'
        else:
            user.disable_user()
            message = f'用户 {user.username} 已禁用'
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})

@admin_bp.route('/users/<user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """软删除用户"""
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': '不能删除自己的账号'})
    
    try:
        user = User.query.get_or_404(user_id)
        
        # 软删除
        user.soft_delete()
        
        return jsonify({'success': True, 'message': f'用户 {user.username} 已删除'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

# =============== 对话管理 ===============

@admin_bp.route('/conversations')
@login_required
@admin_required
@inject_unread_notifications_count
def conversations():
    """对话列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    user_filter = request.args.get('user_id', '')
    
    query = Conversation.query
    
    # 搜索过滤
    if search:
        query = query.filter(Conversation.title.contains(search))
    
    # 用户过滤
    if user_filter:
        query = query.filter_by(user_id=user_filter)
    
    # 连接用户表获取用户信息
    query = query.join(User, Conversation.user_id == User.id)
    
    # 分页
    conversations_page = query.order_by(desc(Conversation.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取所有用户用于过滤器
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    
    return render_template('admin/conversations.html', 
                         conversations=conversations_page,
                         search=search,
                         user_filter=user_filter)

@admin_bp.route('/conversations/<conversation_id>')
@login_required
@admin_required
@inject_unread_notifications_count
def conversation_detail(conversation_id):
    """对话详情"""
    conversation = Conversation.query.get_or_404(conversation_id)
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(asc(Message.created_at)).all()
    
    return render_template('admin/conversation_detail.html', 
                         conversation=conversation,
                         messages=messages)

@admin_bp.route('/conversations/<conversation_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_conversation(conversation_id):
    """删除对话"""
    try:
        conversation = Conversation.query.get_or_404(conversation_id)
        
        # 软删除：设置为非活跃
        conversation.is_active = False
        conversation.updated_at = get_beijing_time_for_db()
        db.session.commit()
        
        return jsonify({'success': True, 'message': '对话已删除'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

# =============== 论坛管理 ===============

@admin_bp.route('/community')
@login_required
@admin_required
@inject_unread_notifications_count
def community():
    """论坛管理"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    user_filter = request.args.get('user_id', '')
    
    query = CommunityPost.query
    
    # 搜索过滤
    if search:
        query = query.filter(CommunityPost.content.contains(search))
    
    # 用户过滤
    if user_filter:
        query = query.filter_by(user_id=user_filter)
    
    # 连接用户表获取用户信息
    query = query.join(User, CommunityPost.user_id == User.id)
    
    # 分页
    posts_page = query.order_by(desc(CommunityPost.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/community.html', 
                         posts=posts_page,
                         search=search,
                         user_filter=user_filter)

@admin_bp.route('/community/<int:post_id>')
@login_required
@admin_required
@inject_unread_notifications_count
def post_detail(post_id):
    """帖子详情"""
    post = CommunityPost.query.get_or_404(post_id)
    interactions = CommunityInteraction.query.filter_by(post_id=post_id).order_by(asc(CommunityInteraction.created_at)).all()
    
    return render_template('admin/post_detail.html', 
                         post=post,
                         interactions=interactions)

@admin_bp.route('/community/<int:post_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_post(post_id):
    """删除帖子"""
    try:
        post = CommunityPost.query.get_or_404(post_id)
        
        # 删除相关互动
        CommunityInteraction.query.filter_by(post_id=post_id).delete()
        
        # 删除帖子
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '帖子已删除'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

# =============== 系统工具 ===============

@admin_bp.route('/tools/database')
@login_required
@admin_required
@inject_unread_notifications_count
def database_tools():
    """数据库工具"""
    return render_template('admin/database_tools.html')

@admin_bp.route('/tools/sql', methods=['POST'])
@login_required
@admin_required
def execute_sql():
    """执行SQL查询（管理员权限）"""
    try:
        data = request.get_json()
        sql = data.get('sql', '').strip()
        
        if not sql:
            return jsonify({'success': False, 'message': 'SQL语句不能为空'})
        
        # 执行查询
        result = db.session.execute(text(sql))
        
        # 处理不同类型的SQL语句
        if sql.upper().strip().startswith(('INSERT', 'UPDATE', 'DELETE')):
            # 对于修改数据的语句，提交事务并返回影响的行数
            db.session.commit()
            return jsonify({
                'success': True, 
                'message': f'SQL执行成功，影响了 {result.rowcount} 行',
                'affected_rows': result.rowcount,
                'columns': [],
                'rows': []
            })
        else:
            # 对于查询语句，返回结果集
            # 获取列名
            columns = list(result.keys()) if result.keys() else []
            
            # 获取数据
            rows = []
            for row in result:
                row_data = []
                for value in row:
                    if isinstance(value, datetime):
                        row_data.append(format_beijing_time(value))
                    else:
                        row_data.append(str(value) if value is not None else '')
                rows.append(row_data)
            
            return jsonify({
                'success': True, 
                'columns': columns,
                'rows': rows,
                'count': len(rows)
            })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'SQL执行失败: {str(e)}'})

@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """获取统计数据API"""
    try:
        # 过去7天的数据统计
        seven_days_ago = get_beijing_time_for_db() - timedelta(days=7)
        
        # 用户增长
        users_growth = []
        conversations_growth = []
        posts_growth = []
        
        for i in range(7):
            date = seven_days_ago + timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            users_count = User.query.filter(
                User.created_at >= date,
                User.created_at < next_date
            ).count()
            
            conversations_count = Conversation.query.filter(
                Conversation.created_at >= date,
                Conversation.created_at < next_date
            ).count()
            
            posts_count = CommunityPost.query.filter(
                CommunityPost.created_at >= date,
                CommunityPost.created_at < next_date
            ).count()
            
            users_growth.append({
                'date': format_beijing_time(date, '%Y-%m-%d'),
                'count': users_count
            })
            
            conversations_growth.append({
                'date': format_beijing_time(date, '%Y-%m-%d'),
                'count': conversations_count
            })
            
            posts_growth.append({
                'date': format_beijing_time(date, '%Y-%m-%d'),
                'count': posts_count
            })
        
        return jsonify({
            'success': True,
            'data': {
                'users_growth': users_growth,
                'conversations_growth': conversations_growth,
                'posts_growth': posts_growth
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取统计数据失败: {str(e)}'}) 

# =============== 通知管理 ===============

@admin_bp.route('/notifications')
@login_required
@admin_required
@inject_unread_notifications_count
def notifications():
    """通知管理"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', '')
    type_filter = request.args.get('type', '')
    
    query = Notification.query
    
    # 状态过滤
    if status_filter:
        query = query.filter_by(status=NotificationStatus(status_filter))
    
    # 类型过滤
    if type_filter:
        query = query.filter_by(type=NotificationType(type_filter))
    
    # 分页
    notifications_page = query.order_by(desc(Notification.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/notifications.html',
                         notifications=notifications_page,
                         status_filter=status_filter,
                         type_filter=type_filter,
                         notification_types=NotificationType,
                         notification_statuses=NotificationStatus)

@admin_bp.route('/api/notifications')
@login_required
@admin_required
def api_notifications():
    """获取通知列表API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        
        query = Notification.query
        
        # 搜索过滤
        if search:
            query = query.filter(
                (Notification.title.contains(search)) |
                (Notification.content.contains(search))
            )
        
        # 分页
        notifications_page = query.order_by(desc(Notification.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 统计数据
        stats = {
            'total': Notification.query.count(),
            'published': Notification.query.filter_by(status=NotificationStatus.PUBLISHED).count(),
            'draft': Notification.query.filter_by(status=NotificationStatus.DRAFT).count(),
            'total_views': db.session.query(db.func.sum(Notification.view_count)).scalar() or 0
        }
        
        return jsonify({
            'success': True,
            'notifications': [notification.to_dict() for notification in notifications_page.items],
            'pagination': {
                'page': notifications_page.page,
                'pages': notifications_page.pages,
                'per_page': notifications_page.per_page,
                'total': notifications_page.total
            },
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/notifications/<int:notification_id>')
@login_required
@admin_required
def api_notification_detail(notification_id):
    """获取通知详情API"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        return jsonify({
            'success': True,
            'notification': notification.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/notifications', methods=['POST'])
@login_required
@admin_required
def api_create_notification():
    """创建通知API"""
    try:
        data = request.get_json()
        
        notification = Notification(
            title=data['title'],
            content=data['content'],
            type=NotificationType(data['type']),
            status=NotificationStatus(data['status']),
            priority=data.get('priority', 0),
            icon=data.get('icon', 'bi-bell'),
            color=data.get('color', 'primary'),
            publish_at=datetime.fromisoformat(data['publish_at']) if data.get('publish_at') else None,
            expire_at=datetime.fromisoformat(data['expire_at']) if data.get('expire_at') else None,
            created_by=current_user.id
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '通知创建成功',
            'notification': notification.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/notifications/<int:notification_id>', methods=['PUT'])
@login_required
@admin_required
def api_update_notification(notification_id):
    """更新通知API"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        data = request.get_json()
        
        notification.title = data['title']
        notification.content = data['content']
        notification.type = NotificationType(data['type'])
        notification.status = NotificationStatus(data['status'])
        notification.priority = data.get('priority', 0)
        notification.icon = data.get('icon', 'bi-bell')
        notification.color = data.get('color', 'primary')
        notification.publish_at = datetime.fromisoformat(data['publish_at']) if data.get('publish_at') else None
        notification.expire_at = datetime.fromisoformat(data['expire_at']) if data.get('expire_at') else None
        notification.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '通知更新成功',
            'notification': notification.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_notification(notification_id):
    """删除通知API"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        
        # 删除相关的查看记录
        NotificationView.query.filter_by(notification_id=notification_id).delete()
        
        # 删除通知
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '通知删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# =============== 反馈管理 ===============

@admin_bp.route('/feedbacks')
@login_required
@admin_required
@inject_unread_notifications_count
def feedbacks():
    """意见反馈管理"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', '')
    
    query = UserFeedback.query
    
    # 状态过滤
    if status_filter:
        query = query.filter_by(status=FeedbackStatus(status_filter))
    
    # 分页
    feedbacks_page = query.order_by(desc(UserFeedback.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/feedbacks.html',
                         feedbacks=feedbacks_page,
                         status_filter=status_filter,
                         feedback_statuses=FeedbackStatus)

@admin_bp.route('/api/feedbacks')
@login_required
@admin_required
def api_feedbacks():
    """获取反馈列表API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        status_filter = request.args.get('status', '')
        
        query = UserFeedback.query
        
        # 搜索过滤
        if search:
            query = query.filter(
                (UserFeedback.title.contains(search)) |
                (UserFeedback.content.contains(search))
            )
        
        # 状态过滤
        if status_filter:
            query = query.filter_by(status=FeedbackStatus(status_filter))
        
        # 分页
        feedbacks_page = query.order_by(desc(UserFeedback.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 统计数据
        stats = {
            'total': UserFeedback.query.count(),
            'pending': UserFeedback.query.filter_by(status=FeedbackStatus.PENDING).count(),
            'processing': UserFeedback.query.filter_by(status=FeedbackStatus.PROCESSING).count(),
            'resolved': UserFeedback.query.filter_by(status=FeedbackStatus.RESOLVED).count()
        }
        
        return jsonify({
            'success': True,
            'feedbacks': [feedback.to_dict() for feedback in feedbacks_page.items],
            'pagination': {
                'page': feedbacks_page.page,
                'pages': feedbacks_page.pages,
                'per_page': feedbacks_page.per_page,
                'total': feedbacks_page.total
            },
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/feedbacks/<int:feedback_id>', methods=['PUT'])
@login_required
@admin_required
def api_update_feedback(feedback_id):
    """更新反馈状态API"""
    try:
        feedback = UserFeedback.query.get_or_404(feedback_id)
        data = request.get_json()
        
        if 'status' in data:
            feedback.status = FeedbackStatus(data['status'])
        
        if 'admin_response' in data:
            feedback.admin_response = data['admin_response']
        
        if 'assigned_to' in data:
            feedback.assigned_to = data['assigned_to']
        
        if 'priority' in data:
            feedback.priority = data['priority']
        
        if data.get('status') == 'resolved':
            feedback.resolved_at = datetime.utcnow()
        
        feedback.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '反馈更新成功',
            'feedback': feedback.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/feedbacks/<int:feedback_id>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_feedback(feedback_id):
    """删除反馈API"""
    try:
        feedback = UserFeedback.query.get_or_404(feedback_id)
        db.session.delete(feedback)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '反馈删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}) 