"""
通知和反馈数据模型
"""
from datetime import datetime
from enum import Enum
from app.database import db

class NotificationType(Enum):
    """通知类型枚举"""
    SYSTEM = 'system'      # 系统通知
    FEATURE = 'feature'    # 功能更新
    MAINTENANCE = 'maintenance'  # 维护通知
    ANNOUNCEMENT = 'announcement'  # 公告

class NotificationStatus(Enum):
    """通知状态枚举"""
    DRAFT = 'draft'        # 草稿
    PUBLISHED = 'published'  # 已发布
    ARCHIVED = 'archived'   # 已归档

class FeedbackStatus(Enum):
    """反馈状态枚举"""
    PENDING = 'pending'    # 待处理
    PROCESSING = 'processing'  # 处理中
    RESOLVED = 'resolved'   # 已解决
    CLOSED = 'closed'      # 已关闭

class Notification(db.Model):
    """系统通知模型"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, comment='通知标题')
    content = db.Column(db.Text, nullable=False, comment='通知内容')
    type = db.Column(db.Enum(NotificationType), nullable=False, default=NotificationType.SYSTEM, comment='通知类型')
    status = db.Column(db.Enum(NotificationStatus), nullable=False, default=NotificationStatus.DRAFT, comment='通知状态')
    
    # 发布设置
    publish_at = db.Column(db.DateTime, nullable=True, comment='定时发布时间')
    expire_at = db.Column(db.DateTime, nullable=True, comment='过期时间')
    
    # 优先级和样式
    priority = db.Column(db.Integer, default=0, comment='优先级，数字越大优先级越高')
    icon = db.Column(db.String(50), default='bi-bell', comment='图标样式')
    color = db.Column(db.String(20), default='primary', comment='颜色主题')
    
    # 目标用户
    target_all_users = db.Column(db.Boolean, default=True, comment='是否面向所有用户')
    target_user_roles = db.Column(db.Text, comment='目标用户角色，JSON格式')
    
    # 统计数据
    view_count = db.Column(db.Integer, default=0, comment='查看次数')
    
    # 创建和更新时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 创建者
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    creator = db.relationship('User', backref='created_notifications', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'type': self.type.value if self.type else None,
            'status': self.status.value if self.status else None,
            'priority': self.priority,
            'icon': self.icon,
            'color': self.color,
            'view_count': self.view_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'publish_at': self.publish_at.isoformat() if self.publish_at else None,
            'expire_at': self.expire_at.isoformat() if self.expire_at else None,
            'creator': self.creator.username if self.creator else None
        }

class UserFeedback(db.Model):
    """用户反馈模型"""
    __tablename__ = 'user_feedbacks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, comment='反馈标题')
    content = db.Column(db.Text, nullable=False, comment='反馈内容')
    contact_info = db.Column(db.String(200), comment='联系方式')
    
    # 反馈分类
    category = db.Column(db.String(50), default='general', comment='反馈分类')
    tags = db.Column(db.Text, comment='标签，JSON格式')
    
    # 状态管理
    status = db.Column(db.Enum(FeedbackStatus), nullable=False, default=FeedbackStatus.PENDING, comment='处理状态')
    admin_response = db.Column(db.Text, comment='管理员回复')
    
    # 优先级
    priority = db.Column(db.Integer, default=0, comment='优先级')
    
    # 用户信息
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='用户ID，匿名反馈时为空')
    user = db.relationship('User', backref='feedbacks', foreign_keys=[user_id])
    
    # 处理信息
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='分配给的管理员')
    assignee = db.relationship('User', backref='assigned_feedbacks', foreign_keys=[assigned_to])
    resolved_at = db.Column(db.DateTime, comment='解决时间')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # IP地址（用于匿名反馈追踪）
    ip_address = db.Column(db.String(45), comment='用户IP地址')
    user_agent = db.Column(db.Text, comment='用户设备信息')
    
    def __repr__(self):
        return f'<UserFeedback {self.id}: {self.title}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'contact_info': self.contact_info,
            'category': self.category,
            'status': self.status.value if self.status else None,
            'admin_response': self.admin_response,
            'priority': self.priority,
            'user': self.user.username if self.user else '匿名用户',
            'assignee': self.assignee.username if self.assignee else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

class NotificationView(db.Model):
    """通知查看记录"""
    __tablename__ = 'notification_views'
    
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notifications.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 复合唯一索引
    __table_args__ = (
        db.UniqueConstraint('notification_id', 'user_id', name='unique_notification_user_view'),
    )
    
    notification = db.relationship('Notification', backref='views')
    user = db.relationship('User', backref='notification_views')
    
    def __repr__(self):
        return f'<NotificationView {self.notification_id}-{self.user_id}>' 