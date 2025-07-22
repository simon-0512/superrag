"""
SuperRAG 应用包初始化
"""

import os
from flask import Flask

def create_app(config_name=None):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 简化配置加载 - 直接使用DevelopmentConfig
    from config.settings import DevelopmentConfig, ProductionConfig, TestingConfig
    
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig, 
        'testing': TestingConfig
    }
    
    config_class = config_map.get(config_name, DevelopmentConfig)
    app.config.from_object(config_class)
    
    # 确保实例文件夹存在
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # 初始化数据库
    from app.database import init_database
    init_database(app, config_name)
    
    # 初始化认证系统
    from app.auth import init_auth
    init_auth(app)
    
    # 注册蓝图
    from app.routes import main_bp, api_bp
    from app.routes.community_api import community_api
    from app.routes.role_api import role_api_bp
    from app.routes.admin import admin_bp
    from app.routes.notification_api import notification_api
    from app.routes.mindmap import mindmap_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(community_api)
    app.register_blueprint(role_api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notification_api)
    app.register_blueprint(mindmap_bp)
    
    # 注册自定义过滤器
    def format_number(value):
        """格式化数字，添加千位分隔符"""
        try:
            return "{:,}".format(int(value))
        except (ValueError, TypeError):
            return value
    
    app.jinja_env.filters['format_number'] = format_number
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        from app.database import db
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app 