"""
SuperRAG配置文件示例
重命名此文件为settings.py并填入你的实际配置
"""

import os
from datetime import timedelta

class BaseConfig:
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
    DEEPSEEK_API_KEY = "sk-157323fda4204a02afa405149a0fefcf"
    DEEPSEEK_API_BASE = "https://api.deepseek.com"
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
    
    # LangChain配置
    LANGCHAIN_ENABLED = False
    LANGCHAIN_MEMORY_TYPE = "buffer"
    LANGCHAIN_MAX_TOKEN_LIMIT = 8000
    LANGCHAIN_WINDOW_SIZE = 10
    LANGCHAIN_DEBUG = False
    LANGCHAIN_VERBOSE = False
    
    # 对话相关配置
    CONVERSATION_SUMMARY_ROUNDS = 10
    CONVERSATION_SUMMARY_TOKEN_LIMIT = 3000
    MAX_CONTEXT_MESSAGES = 20
    
    # 其他配置
    DEBUG = False
    TESTING = False
    
class DevelopmentConfig(BaseConfig):
    DEBUG = True
    
class ProductionConfig(BaseConfig):
    # 生产环境特定配置
    pass
    
class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:" 