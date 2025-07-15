"""
装饰器模块
用于存放各种装饰器函数
"""

from functools import wraps
from flask import jsonify, redirect, url_for, flash, request, g
from flask_login import current_user
from app.models.notification import Notification, NotificationStatus

def require_active_user(f):
    """要求用户处于活跃状态（未被禁用或删除）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'success': False, 'message': '请先登录'}), 401
            return redirect(url_for('auth.login'))
        
        # 检查用户是否可以使用功能
        if not current_user.can_use_features():
            if current_user.is_deleted():
                # 已删除用户强制登出
                from flask_login import logout_user
                logout_user()
                message = '账号已被删除，请联系管理员'
                if request.is_json:
                    return jsonify({'success': False, 'message': message}), 403
                flash(message, 'error')
                return redirect(url_for('auth.login'))
            
            if current_user.is_disabled():
                message = '账号已被禁用，无法使用此功能，请联系管理员'
                if request.is_json:
                    return jsonify({'success': False, 'message': message}), 403
                flash(message, 'warning')
                return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def require_read_permission(f):
    """要求读取权限（禁用用户可以查看，删除用户不行）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'success': False, 'message': '请先登录'}), 401
            return redirect(url_for('auth.login'))
        
        # 删除用户强制登出
        if current_user.is_deleted():
            from flask_login import logout_user
            logout_user()
            message = '账号已被删除，请联系管理员'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 403
            flash(message, 'error')
            return redirect(url_for('auth.login'))
        
        # 禁用用户可以查看内容
        return f(*args, **kwargs)
    return decorated_function

def require_write_permission(f):
    """要求写入权限（禁用用户和删除用户都不能写入）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'success': False, 'message': '请先登录'}), 401
            return redirect(url_for('auth.login'))
        
        # 检查用户是否可以使用功能
        if not current_user.can_use_features():
            if current_user.is_deleted():
                # 已删除用户强制登出
                from flask_login import logout_user
                logout_user()
                message = '账号已被删除，请联系管理员'
                if request.is_json:
                    return jsonify({'success': False, 'message': message}), 403
                flash(message, 'error')
                return redirect(url_for('auth.login'))
            
            if current_user.is_disabled():
                message = '账号已被禁用，无法进行此操作。您可以查看过往内容，但无法创建新内容'
                if request.is_json:
                    return jsonify({'success': False, 'message': message}), 403
                flash(message, 'warning')
                # 对于禁用用户，跳转到仪表板而不是首页
                return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """要求管理员权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'success': False, 'message': '请先登录'}), 401
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            message = '需要管理员权限'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 403
            flash(message, 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def inject_unread_notifications_count(f):
    """为管理后台模板注入未读通知数量"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取未读通知数量（已发布但未查看的通知）
        g.unread_notifications_count = Notification.query.filter(
            Notification.status == NotificationStatus.PUBLISHED,
            ~Notification.views.any()  # 没有任何查看记录的通知
        ).count()
        return f(*args, **kwargs)
    return decorated_function 