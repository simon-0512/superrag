"""
用户数据模型
"""

from datetime import datetime
from enum import Enum
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

# 注意：db 实例应该从 app.database 导入，而不是在这里创建
# 这里只是为了类型提示，实际的 db 实例在 app.database 中
from app.database import db
from app.utils.timezone_utils import get_beijing_time_for_db

class UserRole(Enum):
    """用户角色枚举"""
    ADMIN = "admin"          # 管理员：具有增删改查测试全部权限
    TESTER = "tester"        # 测试人员：可以看到页面中的测试按钮
    VIP = "vip"              # VIP用户：暂时只做后台区分
    USER = "user"            # 普通用户：基础用户

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
    disabled = db.Column(db.Boolean, default=False, nullable=False)  # 是否禁用
    deleted = db.Column(db.Boolean, default=False, nullable=False)  # 是否软删除
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=get_beijing_time_for_db, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_beijing_time_for_db, onupdate=get_beijing_time_for_db, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    
    # 用户角色
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    
    # 用户设置
    preferences = db.Column(db.JSON, default=dict, nullable=False)
    
    # 关联关系
    knowledge_bases = db.relationship('KnowledgeBase', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # 社区相关关系 - 恢复关系定义
    community_posts = db.relationship('CommunityPost', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    community_interactions = db.relationship('CommunityInteraction', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # 关注关系 - 恢复关系定义
    following_relationships = db.relationship(
        'UserFollow', 
        foreign_keys='UserFollow.follower_id',
        back_populates='follower', 
        lazy='dynamic', 
        cascade='all, delete-orphan'
    )
    follower_relationships = db.relationship(
        'UserFollow', 
        foreign_keys='UserFollow.following_id',
        back_populates='following', 
        lazy='dynamic', 
        cascade='all, delete-orphan'
    )
    
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
        self.last_login_at = get_beijing_time_for_db()
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
    
    # 社区相关方法
    def update_post_count(self):
        """更新用户帖子数量（用于缓存优化）"""
        # 这里可以添加缓存逻辑
        pass
    
    def update_like_count(self):
        """更新用户获赞总数（用于缓存优化）"""
        # 这里可以添加缓存逻辑
        pass
    
    def is_following(self, user_id):
        """检查是否关注某用户"""
        from app.models.community import UserFollow
        return UserFollow.query.filter_by(
            follower_id=self.id,
            following_id=user_id
        ).first() is not None
    
    def get_following_count(self):
        """获取关注数量"""
        return self.following_relationships.count()
    
    def get_followers_count(self):
        """获取粉丝数量"""
        return self.follower_relationships.count()
    
    def get_posts_count(self):
        """获取帖子数量"""
        return self.community_posts.filter_by(status='published').count()
    
    def get_total_likes(self):
        """获取总获赞数"""
        from app.models.community import CommunityInteraction, InteractionType
        return db.session.query(CommunityInteraction).join(
            'post'
        ).filter(
            CommunityInteraction.interaction_type == InteractionType.LIKE,
            CommunityInteraction.post.has(user_id=self.id)
        ).count()
    
    # =============== 角色相关方法 ===============
    
    def set_role(self, role_value):
        """设置用户角色"""
        if isinstance(role_value, str):
            # 根据字符串查找对应的枚举值
            role_map = {
                'admin': UserRole.ADMIN,
                'tester': UserRole.TESTER,
                'vip': UserRole.VIP,
                'user': UserRole.USER
            }
            if role_value not in role_map:
                raise ValueError(f"无效的角色: {role_value}")
            self.role = role_map[role_value]
        elif isinstance(role_value, UserRole):
            self.role = role_value
        else:
            raise ValueError(f"角色值类型错误: {type(role_value)}")
        
        db.session.commit()
    
    def get_role_code(self):
        """获取用户角色代码"""
        return self.role.value if self.role else 'user'
    
    def get_role_name(self):
        """获取用户角色中文名称"""
        role_names = {
            UserRole.ADMIN: '系统管理员',
            UserRole.TESTER: '测试人员', 
            UserRole.VIP: 'VIP用户',
            UserRole.USER: '普通用户'
        }
        return role_names.get(self.role, '普通用户')
    
    def has_role(self, role_code):
        """检查用户是否有指定角色"""
        return self.get_role_code() == role_code
    
    def has_permission(self, permission):
        """检查用户是否有指定权限"""
        # 管理员拥有所有权限
        if self.is_admin():
            return True
        
        # 根据角色定义权限
        permissions = {
            UserRole.ADMIN: ['*'],  # 所有权限
            UserRole.TESTER: ['test_access', 'knowledge_manage', 'data_export'],
            UserRole.VIP: ['knowledge_manage', 'advanced_features'],
            UserRole.USER: ['basic_usage', 'knowledge_view']
        }
        
        user_permissions = permissions.get(self.role, [])
        return '*' in user_permissions or permission in user_permissions
    
    def is_admin(self):
        """检查是否为管理员"""
        return self.role == UserRole.ADMIN
    
    def is_tester(self):
        """检查是否为测试人员"""
        return self.role == UserRole.TESTER
    
    def is_vip(self):
        """检查是否为VIP用户"""
        return self.role == UserRole.VIP
    
    def is_normal_user(self):
        """检查是否为普通用户"""
        return self.role == UserRole.USER
    
    def can_see_test_buttons(self):
        """检查是否可以看到测试按钮"""
        return self.is_admin() or self.is_tester()
    
    # =============== 状态管理方法 ===============
    
    def disable_user(self):
        """禁用用户"""
        self.disabled = True
        db.session.commit()
    
    def enable_user(self):
        """启用用户"""
        self.disabled = False
        db.session.commit()
    
    def soft_delete(self):
        """软删除用户"""
        self.deleted = True
        db.session.commit()
    
    def restore_user(self):
        """恢复用户（取消软删除）"""
        self.deleted = False
        db.session.commit()
    
    def is_disabled(self):
        """检查用户是否被禁用"""
        return self.disabled
    
    def is_deleted(self):
        """检查用户是否被软删除"""
        return self.deleted
    
    def can_login(self):
        """检查用户是否可以登录"""
        return not self.deleted  # 禁用用户可以登录，但不能使用功能
    
    def can_use_features(self):
        """检查用户是否可以使用功能"""
        return not self.disabled and not self.deleted
    
    def get_avatar_letter(self):
        """获取头像字母（用户昵称或用户名的第一个字符）"""
        name = self.nickname or self.username
        return name[0].upper() if name else 'U'
    
    def get_display_avatar(self):
        """获取显示用的头像URL或字母"""
        if self.avatar_url:
            return self.avatar_url
        return self.get_avatar_letter()
    
    def to_dict(self, include_private=False, include_roles=True):
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
        
        # 包含角色信息
        if include_roles:
            data.update({
                'role': self.get_role_code(),
                'role_name': self.get_role_name(),
                'is_admin': self.is_admin(),
                'is_tester': self.is_tester(),
                'is_vip': self.is_vip(),
                'is_normal_user': self.is_normal_user(),
                'can_see_test_buttons': self.can_see_test_buttons()
            })
        
        if include_private:
            data.update({
                'email': self.email,
                'is_active': self.is_active,
                'disabled': self.disabled,
                'deleted': self.deleted,
                'preferences': self.preferences,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            })
        
        return data
    
    def __repr__(self):
        return f'<User {self.username}>' 