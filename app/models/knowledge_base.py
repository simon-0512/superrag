"""
知识库相关数据模型
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text
import uuid
import os
from app.database import db
from app.utils.timezone_utils import get_beijing_time_for_db

class KnowledgeBase(db.Model):
    """知识库模型"""
    
    __tablename__ = 'knowledge_bases'
    
    # 主键
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 基本信息
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # 关联用户
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # 状态
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # 统计信息
    document_count = db.Column(db.Integer, default=0, nullable=False)
    total_size = db.Column(db.BigInteger, default=0, nullable=False)  # 字节
    
    # 向量化设置
    embedding_model = db.Column(db.String(50), default='text-embedding-ada-002', nullable=False)
    chunk_size = db.Column(db.Integer, default=1000, nullable=False)
    chunk_overlap = db.Column(db.Integer, default=200, nullable=False)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=get_beijing_time_for_db, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_beijing_time_for_db, onupdate=get_beijing_time_for_db, nullable=False)
    
    # 关联关系
    documents = db.relationship('Document', backref='knowledge_base', lazy='dynamic', cascade='all, delete-orphan')
    
    def update_stats(self):
        """更新统计信息"""
        self.document_count = self.documents.filter_by(is_active=True).count()
        self.total_size = sum(doc.file_size for doc in self.documents.filter_by(is_active=True)) or 0
        db.session.commit()
    
    def get_chunk_count(self):
        """计算知识库中的总块数"""
        from sqlalchemy import func
        result = db.session.query(func.sum(Document.chunk_count)).filter(
            Document.knowledge_base_id == self.id,
            Document.is_active == True
        ).scalar()
        return result or 0
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_public': self.is_public,
            'is_active': self.is_active,
            'document_count': self.document_count,
            'total_size': self.total_size,
            'chunk_count': self.get_chunk_count(),
            'embedding_model': self.embedding_model,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<KnowledgeBase {self.name}>'


class Document(db.Model):
    """文档模型"""
    
    __tablename__ = 'documents'
    
    # 主键
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 基本信息
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # pdf, docx, txt, md
    file_size = db.Column(db.BigInteger, nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    
    # 内容信息
    title = db.Column(db.String(200), nullable=True)
    content_hash = db.Column(db.String(64), nullable=False, index=True)  # SHA256
    text_content = db.Column(db.Text, nullable=True)
    doc_metadata = db.Column(db.JSON, default=dict, nullable=False)
    
    # 关联
    knowledge_base_id = db.Column(db.String(36), db.ForeignKey('knowledge_bases.id'), nullable=False, index=True)
    
    # 处理状态
    processing_status = db.Column(db.String(20), default='pending', nullable=False)  # pending, processing, completed, failed
    processing_error = db.Column(db.Text, nullable=True)
    
    # 向量化状态
    is_vectorized = db.Column(db.Boolean, default=False, nullable=False)
    chunk_count = db.Column(db.Integer, default=0, nullable=False)
    
    # 状态
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=get_beijing_time_for_db, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_beijing_time_for_db, onupdate=get_beijing_time_for_db, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # 关联关系
    chunks = db.relationship('DocumentChunk', backref='document', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_file_size_human(self):
        """获取人类可读的文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    def delete_file(self):
        """删除物理文件"""
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'file_size_human': self.get_file_size_human(),
            'title': self.title,
            'doc_metadata': self.doc_metadata,
            'processing_status': self.processing_status,
            'processing_error': self.processing_error,
            'is_vectorized': self.is_vectorized,
            'chunk_count': self.chunk_count,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
    
    def __repr__(self):
        return f'<Document {self.filename}>'


class DocumentChunk(db.Model):
    """文档分块模型"""
    
    __tablename__ = 'document_chunks'
    
    # 主键
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关联文档
    document_id = db.Column(db.String(36), db.ForeignKey('documents.id'), nullable=False, index=True)
    
    # 分块信息
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_hash = db.Column(db.String(64), nullable=False, index=True)
    
    # 元数据
    chunk_metadata = db.Column(db.JSON, default=dict, nullable=False)
    
    # 向量信息
    embedding = db.Column(db.JSON, nullable=True)  # 存储向量嵌入
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=get_beijing_time_for_db, nullable=False)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'chunk_index': self.chunk_index,
            'content': self.content,
            'chunk_metadata': self.chunk_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<DocumentChunk {self.document_id}:{self.chunk_index}>'


class Conversation(db.Model):
    """对话模型"""
    
    __tablename__ = 'conversations'
    
    # 主键
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 基本信息
    title = db.Column(db.String(200), nullable=False, default='新对话')
    
    # 关联用户
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # 关联知识库（可选）
    knowledge_base_id = db.Column(db.String(36), db.ForeignKey('knowledge_bases.id'), nullable=True, index=True)
    
    # 对话设置 - V0.3.0 扩展
    model_name = db.Column(db.String(50), default='deepseek-chat', nullable=False)  # deepseek-chat 或 deepseek-reasoner
    system_prompt = db.Column(db.Text, nullable=True)  # 初始提示词（2k字以内）
    temperature = db.Column(db.Float, default=1.0, nullable=False)  # 0, 1.0, 1.5
    max_tokens = db.Column(db.Integer, default=4000, nullable=False)  # V3: 4k/8k, R1: 32k/64k
    
    # 统计信息
    message_count = db.Column(db.Integer, default=0, nullable=False)
    total_tokens = db.Column(db.Integer, default=0, nullable=False)
    
    # 状态
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=get_beijing_time_for_db, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_beijing_time_for_db, onupdate=get_beijing_time_for_db, nullable=False)
    
    # 关联关系
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    knowledge_base = db.relationship('KnowledgeBase', backref='conversations_ref')
    
    def update_stats(self):
        """更新统计信息"""
        self.message_count = self.messages.count()
        self.total_tokens = sum(msg.token_count for msg in self.messages if msg.token_count) or 0
        db.session.commit()
    
    def get_model_display_name(self):
        """获取模型显示名称"""
        model_names = {
            'deepseek-chat': 'DeepSeek-V3',
            'deepseek-reasoner': 'DeepSeek-R1'
        }
        return model_names.get(self.model_name, self.model_name)
    
    def get_temperature_display_name(self):
        """获取温度显示名称"""
        temp_names = {
            0.0: '代码生成',
            1.0: '通用对话',
            1.5: '创意写作'
        }
        return temp_names.get(self.temperature, f'自定义({self.temperature})')
    
    def get_max_tokens_options(self):
        """获取当前模型支持的输出长度选项"""
        if self.model_name == 'deepseek-chat':
            return [4000, 8000]  # V3: 4k, 8k
        elif self.model_name == 'deepseek-reasoner':
            return [32000, 64000]  # R1: 32k, 64k
        else:
            return [4000, 8000]  # 默认
    
    def validate_system_prompt(self, prompt):
        """验证系统提示词长度（2k字以内）"""
        if prompt and len(prompt) > 2000:
            return False, "系统提示词不能超过2000字"
        return True, ""
    
    def update_conversation_config(self, model_name=None, temperature=None, max_tokens=None, system_prompt=None):
        """更新对话配置参数"""
        if model_name is not None:
            # 验证模型名称
            valid_models = ['deepseek-chat', 'deepseek-reasoner']
            if model_name in valid_models:
                self.model_name = model_name
                # 切换模型时重置max_tokens为默认值
                if model_name == 'deepseek-chat':
                    self.max_tokens = 4000
                elif model_name == 'deepseek-reasoner':
                    self.max_tokens = 32000
        
        if temperature is not None:
            # 验证温度值
            valid_temps = [0.0, 1.0, 1.5]
            if temperature in valid_temps:
                self.temperature = temperature
        
        if max_tokens is not None:
            # 验证输出长度
            valid_tokens = self.get_max_tokens_options()
            if max_tokens in valid_tokens:
                self.max_tokens = max_tokens
        
        if system_prompt is not None:
            # 验证系统提示词
            valid, error_msg = self.validate_system_prompt(system_prompt)
            if valid:
                self.system_prompt = system_prompt
            else:
                raise ValueError(error_msg)
        
        db.session.commit()
    
    def get_conversation_config(self):
        """获取对话配置参数 - V0.3.0"""
        return {
            'model_name': self.model_name,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'system_prompt': self.system_prompt
        }
    
    def to_dict(self, include_messages=False):
        """转换为字典 - V0.3.0 增强版"""
        data = {
            'id': self.id,
            'title': self.title,
            'model_name': self.model_name,
            'model_display_name': self.get_model_display_name(),
            'system_prompt': self.system_prompt,
            'temperature': self.temperature,
            'temperature_display_name': self.get_temperature_display_name(),
            'max_tokens': self.max_tokens,
            'max_tokens_options': self.get_max_tokens_options(),
            'message_count': self.message_count,
            'total_tokens': self.total_tokens,
            'is_active': self.is_active,
            'knowledge_base_id': self.knowledge_base_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_messages:
            data['messages'] = [msg.to_dict() for msg in self.messages.order_by(Message.created_at)]
        
        return data

    def __repr__(self):
        return f'<Conversation {self.title}>'


class Message(db.Model):
    """消息模型"""
    
    __tablename__ = 'messages'
    
    # 主键
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关联对话
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversations.id'), nullable=False, index=True)
    
    # 消息内容
    role = db.Column(db.String(20), nullable=False)  # user, assistant, system
    content = db.Column(db.Text, nullable=False)
    
    # 元数据（V0.3.1 思考过程存储在这里）
    msg_metadata = db.Column(db.JSON, default=dict, nullable=False)
    
    # 统计信息
    token_count = db.Column(db.Integer, nullable=True)
    
    # RAG相关
    used_knowledge_base = db.Column(db.Boolean, default=False, nullable=False)
    relevant_chunks = db.Column(db.JSON, nullable=True)  # 相关文档块ID列表
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=get_beijing_time_for_db, nullable=False)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'thinking_process': self.msg_metadata.get('thinking_process') if self.msg_metadata else None,  # V0.3.1 从metadata获取
            'msg_metadata': self.msg_metadata,
            'token_count': self.token_count,
            'used_knowledge_base': self.used_knowledge_base,
            'relevant_chunks': self.relevant_chunks,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Message {self.role}: {self.content[:50]}...>' 