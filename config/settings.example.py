"""
SuperRAG配置文件示例
重命名此文件为settings.py并填入你的实际配置
"""

import os
from datetime import timedelta

class Config:
    """配置基类"""
    
    # Flask配置
    SECRET_KEY = "your-secret-key-here"
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = "your-jwt-secret-key"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # API密钥
    OPENAI_API_KEY = "your-openai-api-key"
    DEEPSEEK_API_KEY = "your-deepseek-api-key"
    DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL = "deepseek-chat"
    
    # 文件上传配置
    UPLOAD_FOLDER = "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 缓存配置
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 会话配置
    SESSION_TYPE = "filesystem"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
    LOG_FILE = "logs/app.log"
    
    # 其他配置
    DEBUG = False
    TESTING = False
    
    @classmethod
    def get_config(cls, config_name=None):
        """获取配置类"""
        config_mapping = {
            'development': DevelopmentConfig,
            'production': ProductionConfig,
            'testing': TestingConfig
        }
        
        if config_name:
            return config_mapping.get(config_name, DevelopmentConfig)
        
        # 默认使用开发配置
        return DevelopmentConfig

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    
class ProductionConfig(Config):
    """生产环境配置"""
    pass
    
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:" 