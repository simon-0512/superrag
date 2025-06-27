"""
SuperRAG 应用配置
"""

import os
from config.database import get_database_config

class BaseConfig:
    """基础配置"""
    
    # Flask 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # 文件上传配置
    UPLOAD_PATH = os.environ.get('UPLOAD_PATH', os.path.join(os.getcwd(), 'uploads'))
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc', 'md'}
    
    # DeepSeek API 配置
    DEEPSEEK_API_KEY = "sk-157323fda4204a02afa405149a0fefcf"
    DEEPSEEK_API_BASE = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"
    
    # 对话管理配置
    CONVERSATION_SUMMARY_ROUNDS = int(os.environ.get('CONVERSATION_SUMMARY_ROUNDS', '5'))  # 每几轮对话进行总结
    MAX_CONTEXT_MESSAGES = int(os.environ.get('MAX_CONTEXT_MESSAGES', '20'))  # 最大上下文消息数
    CONTEXT_WINDOW_SIZE = int(os.environ.get('CONTEXT_WINDOW_SIZE', '4000'))  # 上下文窗口大小（token数）
    
    # LangChain 配置
    LANGCHAIN_ENABLED = os.environ.get('LANGCHAIN_ENABLED', 'true').lower() == 'true'  # 是否启用LangChain
    LANGCHAIN_MEMORY_TYPE = os.environ.get('LANGCHAIN_MEMORY_TYPE', 'summary_buffer')  # 记忆类型
    LANGCHAIN_MAX_TOKEN_LIMIT = int(os.environ.get('LANGCHAIN_MAX_TOKEN_LIMIT', '2000'))  # 摘要触发的token阈值
    LANGCHAIN_WINDOW_SIZE = int(os.environ.get('LANGCHAIN_WINDOW_SIZE', '10'))  # 窗口记忆保留的消息数
    LANGCHAIN_DEBUG = os.environ.get('LANGCHAIN_DEBUG', 'false').lower() == 'true'  # 是否启用调试模式
    LANGCHAIN_VERBOSE = os.environ.get('LANGCHAIN_VERBOSE', 'false').lower() == 'true'  # 是否启用详细日志
    
    # Redis 配置
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    
    # 安全配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # 统一的对话管理配置
    CONVERSATION_SUMMARY_TOKEN_LIMIT = LANGCHAIN_MAX_TOKEN_LIMIT

class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    
    DEBUG = True
    
    # 开发环境数据库配置
    db_config = get_database_config('development')
    SQLALCHEMY_DATABASE_URI = db_config.SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = db_config.SQLALCHEMY_TRACK_MODIFICATIONS
    SQLALCHEMY_RECORD_QUERIES = db_config.SQLALCHEMY_RECORD_QUERIES
    SQLALCHEMY_ECHO = db_config.SQLALCHEMY_ECHO
    SQLALCHEMY_ENGINE_OPTIONS = db_config.SQLALCHEMY_ENGINE_OPTIONS

class TestingConfig(BaseConfig):
    """测试环境配置"""
    
    TESTING = True
    WTF_CSRF_ENABLED = False
    
    # 测试环境数据库配置
    db_config = get_database_config('testing')
    SQLALCHEMY_DATABASE_URI = db_config.SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = db_config.SQLALCHEMY_TRACK_MODIFICATIONS
    SQLALCHEMY_ECHO = db_config.SQLALCHEMY_ECHO

class ProductionConfig(BaseConfig):
    """生产环境配置"""
    
    DEBUG = False
    
    # 生产环境数据库配置
    db_config = get_database_config('production')
    SQLALCHEMY_DATABASE_URI = db_config.SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = db_config.SQLALCHEMY_TRACK_MODIFICATIONS
    SQLALCHEMY_RECORD_QUERIES = db_config.SQLALCHEMY_RECORD_QUERIES
    SQLALCHEMY_ECHO = db_config.SQLALCHEMY_ECHO
    SQLALCHEMY_ENGINE_OPTIONS = db_config.SQLALCHEMY_ENGINE_OPTIONS
    
    # 生产环境安全配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

# 配置映射
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

class Config:
    """配置管理类"""
    
    @staticmethod
    def get_config(config_name=None):
        """获取配置类"""
        if config_name is None:
            config_name = os.environ.get('FLASK_ENV', 'development')
        
        return config_map.get(config_name, config_map['default']) 