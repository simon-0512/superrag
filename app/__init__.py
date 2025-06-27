"""
SuperRAG 应用包初始化
"""

import os
from flask import Flask
from config.settings import Config

def create_app(config_name=None):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    if config_name:
        app.config.from_object(Config.get_config(config_name))
    else:
        app.config.from_object(Config.get_config())
    
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
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
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