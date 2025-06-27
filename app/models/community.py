"""
社区功能数据模型
Community Models for SuperRAG
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import db
import enum


class PostContentType(enum.Enum):
    """AI内容类型枚举"""
    CONVERSATION = "conversation"  # 对话内容
    PDF = "pdf"                   # PDF文档
    TEXT = "text"                 # 纯文本

class PostStatus(enum.Enum):
    """帖子状态枚举"""
    DRAFT = "draft"               # 草稿
    PUBLISHED = "published"       # 已发布
    HIDDEN = "hidden"             # 隐藏

class InteractionType(enum.Enum):
    """互动类型枚举"""
    LIKE = "like"                 # 点赞
    COMMENT = "comment"           # 评论
    SHARE = "share"               # 转发
    BOOKMARK = "bookmark"         # 收藏


class CommunityPost(db.Model):
    """社区帖子模型"""
    __tablename__ = 'community_posts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # 内容相关
    content = Column(Text, nullable=False, comment='用户文字描述(≤140字)')
    ai_prompt = Column(Text, comment='AI提示词(可选)')
    ai_content_type = Column(Enum(PostContentType), comment='AI内容类型')
    ai_content_data = Column(JSON, comment='AI内容数据')
    conversation_id = Column(Integer, ForeignKey('conversations.id'), comment='关联的对话ID')
    pdf_url = Column(String(255), comment='PDF文件URL')
    tags = Column(JSON, comment='标签数组')
    
    # 状态相关
    is_featured = Column(Boolean, default=False, comment='是否精选')
    status = Column(Enum(PostStatus), default=PostStatus.PUBLISHED, comment='帖子状态')
    
    # 统计数据
    like_count = Column(Integer, default=0, comment='点赞数')
    comment_count = Column(Integer, default=0, comment='评论数')
    share_count = Column(Integer, default=0, comment='转发数')
    view_count = Column(Integer, default=0, comment='浏览数')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    user = relationship("User", back_populates="community_posts")
    conversation = relationship("Conversation", backref="community_posts")
    interactions = relationship("CommunityInteraction", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<CommunityPost {self.id}: {self.content[:50]}...>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'ai_prompt': self.ai_prompt,
            'ai_content_type': self.ai_content_type.value if self.ai_content_type else None,
            'ai_content_data': self.ai_content_data,
            'conversation_id': self.conversation_id,
            'pdf_url': self.pdf_url,
            'tags': self.tags or [],
            'is_featured': self.is_featured,
            'status': self.status.value,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'share_count': self.share_count,
            'view_count': self.view_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user': self.user.to_dict() if self.user else None
        }


class CommunityInteraction(db.Model):
    """社区互动模型"""
    __tablename__ = 'community_interactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('community_posts.id'), nullable=False)
    interaction_type = Column(Enum(InteractionType), nullable=False)
    content = Column(Text, comment='评论内容(comment类型时使用)')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    user = relationship("User", back_populates="community_interactions")
    post = relationship("CommunityPost", back_populates="interactions")
    
    # 唯一约束：防止重复点赞等
    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', 'interaction_type', name='uq_user_post_interaction'),
    )
    
    def __repr__(self):
        return f'<CommunityInteraction {self.user_id} {self.interaction_type.value} {self.post_id}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'post_id': self.post_id,
            'interaction_type': self.interaction_type.value,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user': self.user.to_dict() if self.user else None
        }


class UserFollow(db.Model):
    """用户关注关系模型"""
    __tablename__ = 'user_follows'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    follower_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='关注者ID')
    following_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='被关注者ID')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    follower = relationship("User", foreign_keys=[follower_id], back_populates="following_relationships")
    following = relationship("User", foreign_keys=[following_id], back_populates="follower_relationships")
    
    # 唯一约束：防止重复关注
    __table_args__ = (
        UniqueConstraint('follower_id', 'following_id', name='uq_follower_following'),
    )
    
    def __repr__(self):
        return f'<UserFollow {self.follower_id} -> {self.following_id}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'follower_id': self.follower_id,
            'following_id': self.following_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'follower': self.follower.to_dict() if self.follower else None,
            'following': self.following.to_dict() if self.following else None
        }


# 扩展User模型以支持社区功能
def extend_user_model():
    """扩展User模型以支持社区功能"""
    from app.models.user import User
    
    # 添加社区相关字段
    if not hasattr(User, 'nickname'):
        User.nickname = Column(String(50), comment='昵称')
        User.avatar_url = Column(String(255), comment='头像URL')
        User.bio = Column(Text, comment='个人简介')
        User.follower_count = Column(Integer, default=0, comment='粉丝数')
        User.following_count = Column(Integer, default=0, comment='关注数')
        User.post_count = Column(Integer, default=0, comment='分享数')
        User.like_count = Column(Integer, default=0, comment='获赞总数')
        User.badges = Column(JSON, comment='成就徽章')
    
    # 添加关联关系
    if not hasattr(User, 'community_posts'):
        User.community_posts = relationship("CommunityPost", back_populates="user", cascade="all, delete-orphan")
        User.community_interactions = relationship("CommunityInteraction", back_populates="user", cascade="all, delete-orphan")
        User.following_relationships = relationship("UserFollow", foreign_keys="UserFollow.follower_id", back_populates="follower")
        User.follower_relationships = relationship("UserFollow", foreign_keys="UserFollow.following_id", back_populates="following")
    
    # 添加方法
    def get_followers(self):
        """获取粉丝列表"""
        return [rel.follower for rel in self.follower_relationships]
    
    def get_following(self):
        """获取关注列表"""
        return [rel.following for rel in self.following_relationships]
    
    def is_following(self, user_id):
        """检查是否关注某用户"""
        return any(rel.following_id == user_id for rel in self.following_relationships)
    
    def follow(self, user_id):
        """关注用户"""
        from app.database import db
        if not self.is_following(user_id) and user_id != self.id:
            follow_rel = UserFollow(follower_id=self.id, following_id=user_id)
            db.session.add(follow_rel)
            # 更新统计数据
            self.following_count = (self.following_count or 0) + 1
            target_user = User.query.get(user_id)
            if target_user:
                target_user.follower_count = (target_user.follower_count or 0) + 1
            return True
        return False
    
    def unfollow(self, user_id):
        """取消关注用户"""
        from app.database import db
        follow_rel = UserFollow.query.filter_by(follower_id=self.id, following_id=user_id).first()
        if follow_rel:
            db.session.delete(follow_rel)
            # 更新统计数据
            self.following_count = max((self.following_count or 0) - 1, 0)
            target_user = User.query.get(user_id)
            if target_user:
                target_user.follower_count = max((target_user.follower_count or 0) - 1, 0)
            return True
        return False
    
    def update_post_count(self):
        """更新帖子数量"""
        self.post_count = CommunityPost.query.filter_by(user_id=self.id, status=PostStatus.PUBLISHED).count()
    
    def update_like_count(self):
        """更新获赞总数"""
        total_likes = db.session.query(db.func.sum(CommunityPost.like_count)).filter_by(user_id=self.id).scalar()
        self.like_count = total_likes or 0
    
    # 将方法添加到User类
    User.get_followers = get_followers
    User.get_following = get_following
    User.is_following = is_following
    User.follow = follow
    User.unfollow = unfollow
    User.update_post_count = update_post_count
    User.update_like_count = update_like_count
    
    # 更新to_dict方法以包含社区字段
    original_to_dict = User.to_dict
    
    def enhanced_to_dict(self):
        data = original_to_dict(self)
        data.update({
            'nickname': self.nickname,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'follower_count': self.follower_count or 0,
            'following_count': self.following_count or 0,
            'post_count': self.post_count or 0,
            'like_count': self.like_count or 0,
            'badges': self.badges or []
        })
        return data
    
    User.to_dict = enhanced_to_dict 