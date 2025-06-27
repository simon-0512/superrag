"""
用户数据模型
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

# 注意：db 实例应该从 app.database 导入，而不是在这里创建
# 这里只是为了类型提示，实际的 db 实例在 app.database 中
from app.database import db

class User(UserMixin, db.Model):
    """用户模型"""
    
    __tablename__ = 'users'
    
    # 主键
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 基本信息
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # 用户资料
    nickname = db.Column(db.String(100), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    
    # 状态字段
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    
    # 用户设置
    preferences = db.Column(db.JSON, default=dict, nullable=False)
    
    # 关联关系
    knowledge_bases = db.relationship('KnowledgeBase', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, username, email, password):
        """初始化用户"""
        self.username = username
        self.email = email
        self.set_password(password)
        self.preferences = {
            'theme': 'light',
            'language': 'zh-CN',
            'timezone': 'Asia/Shanghai',
            'notifications': {
                'email': True,
                'push': True
            }
        }
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login_at = datetime.utcnow()
        db.session.commit()
    
    def get_preference(self, key, default=None):
        """获取用户偏好设置"""
        return self.preferences.get(key, default)
    
    def set_preference(self, key, value):
        """设置用户偏好"""
        if self.preferences is None:
            self.preferences = {}
        self.preferences[key] = value
        db.session.commit()
    
    def to_dict(self, include_private=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'username': self.username,
            'nickname': self.nickname,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
        
        if include_private:
            data.update({
                'email': self.email,
                'is_active': self.is_active,
                'preferences': self.preferences,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            })
        
        return data
    
    def __repr__(self):
        return f'<User {self.username}>' 