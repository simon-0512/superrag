"""
用户认证模块
"""

from flask import Blueprint
from flask_login import LoginManager

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# 初始化登录管理器
login_manager = LoginManager()

def init_auth(app):
    """初始化认证系统"""
    
    # 配置登录管理器
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录访问该页面。'
    login_manager.login_message_category = 'info'
    
    # 用户加载回调
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(user_id)
    
    # 注册认证蓝图
    from . import routes
    app.register_blueprint(auth_bp)
    
    return login_manager 