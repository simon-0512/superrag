"""
思维导图数据模型
"""

import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship, backref
from app.database import db


class Mindmap(db.Model):
    """思维导图模型"""
    __tablename__ = 'mindmaps'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    canvas_data = Column(JSON, nullable=False, default=dict)
    thumbnail_url = Column(String(255))
    is_public = Column(Boolean, default=False)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", backref=backref("mindmaps", lazy="dynamic"))
    nodes = relationship("MindmapNode", backref="mindmap", lazy="dynamic", cascade="all, delete-orphan")
    ai_expansions = relationship("MindmapAIExpansion", backref="mindmap", lazy="dynamic", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Mindmap {self.title}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'user_id': self.user_id,
            'canvas_data': self.canvas_data,
            'thumbnail_url': self.thumbnail_url,
            'is_public': self.is_public,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'nickname': self.user.nickname
            } if self.user else None
        }
    
    @classmethod
    def create_from_dict(cls, data, user_id):
        """从字典创建思维导图"""
        mindmap = cls(
            title=data.get('title', '新建思维导图'),
            description=data.get('description'),
            user_id=user_id,
            canvas_data=data.get('canvas_data', {}),
            is_public=data.get('is_public', False),
            tags=data.get('tags', [])
        )
        return mindmap


class MindmapNode(db.Model):
    """思维导图节点模型"""
    __tablename__ = 'mindmap_nodes'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mindmap_id = Column(String(36), ForeignKey('mindmaps.id'), nullable=False)
    parent_id = Column(String(36), ForeignKey('mindmap_nodes.id'))
    content = Column(Text, nullable=False)
    node_type = Column(String(20), default='text')  # text, image, link, ai_generated
    position_x = Column(Float)
    position_y = Column(Float)
    style_data = Column(JSON, default=dict)
    ai_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    parent = relationship("MindmapNode", remote_side=[id], backref="children")
    ai_expansions = relationship("MindmapAIExpansion", backref="node", lazy="dynamic")
    
    def __repr__(self):
        return f'<MindmapNode {self.content[:20]}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'mindmap_id': self.mindmap_id,
            'parent_id': self.parent_id,
            'content': self.content,
            'node_type': self.node_type,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'style_data': self.style_data,
            'ai_metadata': self.ai_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'children': [child.to_dict() for child in self.children]
        }


class MindmapAIExpansion(db.Model):
    """思维导图AI扩展历史模型"""
    __tablename__ = 'mindmap_ai_expansions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mindmap_id = Column(String(36), ForeignKey('mindmaps.id'), nullable=False)
    node_id = Column(String(36), ForeignKey('mindmap_nodes.id'), nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    expansion_type = Column(String(20))  # expand, learn, supplement, relate
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MindmapAIExpansion {self.expansion_type}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'mindmap_id': self.mindmap_id,
            'node_id': self.node_id,
            'prompt': self.prompt,
            'response': self.response,
            'expansion_type': self.expansion_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }