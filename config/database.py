"""
数据库配置
"""

import os
from urllib.parse import quote_plus

class DatabaseConfig:
    """数据库配置基类"""
    
    # SQLAlchemy配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True,
        'max_overflow': 20,
        'pool_timeout': 30
    }

class DevelopmentConfig(DatabaseConfig):
    """开发环境数据库配置"""
    
    # SQLite数据库（开发环境）
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(__file__), '..', 'instance', 'superrag_dev.db')
    
    # 开发环境启用调试
    SQLALCHEMY_ECHO = True

class TestingConfig(DatabaseConfig):
    """测试环境数据库配置"""
    
    # 内存SQLite数据库（测试环境）
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False

class ProductionConfig(DatabaseConfig):
    """生产环境数据库配置"""
    
    # PostgreSQL数据库（生产环境）
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'superrag')
    DB_USER = os.environ.get('DB_USER', 'superrag')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    
    # 如果环境变量中直接提供了完整的数据库URL
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    else:
        # 构建PostgreSQL连接字符串
        SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # 生产环境不启用SQL回显
    SQLALCHEMY_ECHO = False
    
    # 生产环境连接池配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'max_overflow': 50,
        'pool_timeout': 60
    }

# 配置映射
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_database_config(config_name=None):
    """获取数据库配置"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config_map.get(config_name, config_map['default']) 