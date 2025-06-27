"""
主要路由
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import User, KnowledgeBase, Conversation
from app.database import db

# 创建主蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """首页"""
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """用户仪表板"""
    # 获取用户的知识库
    knowledge_bases = current_user.knowledge_bases.filter_by(is_active=True).all()
    
    # 获取最近的对话
    recent_conversations = current_user.conversations.filter_by(is_active=True)\
                         .order_by(Conversation.updated_at.desc()).limit(5).all()
    
    # 统计信息
    stats = {
        'knowledge_bases_count': len(knowledge_bases),
        'conversations_count': current_user.conversations.filter_by(is_active=True).count(),
        'total_documents': sum(kb.document_count for kb in knowledge_bases),
        'total_messages': sum(conv.message_count for conv in current_user.conversations)
    }
    
    return render_template('dashboard.html', 
                         knowledge_bases=knowledge_bases,
                         recent_conversations=recent_conversations,
                         stats=stats)

@main_bp.route('/chat')
@login_required
def chat():
    """聊天页面"""
    return render_template('chat.html')

@main_bp.route('/knowledge')
@login_required
def knowledge():
    """知识库管理页面"""
    knowledge_bases = current_user.knowledge_bases.filter_by(is_active=True).all()
    return render_template('knowledge.html', knowledge_bases=knowledge_bases)

@main_bp.route('/knowledge/<knowledge_base_id>')
@login_required
def knowledge_detail(knowledge_base_id):
    """知识库详情页面"""
    kb = KnowledgeBase.query.filter_by(
        id=knowledge_base_id,
        user_id=current_user.id
    ).first_or_404()
    
    # 获取文档列表
    documents = kb.documents.filter_by(is_active=True).all()
    
    return render_template('knowledge_detail.html', 
                         knowledge_base=kb,
                         documents=documents)

@main_bp.route('/langchain')
@login_required
def langchain_demo():
    """LangChain 上下文管理演示页面"""
    return render_template('langchain_demo.html')

@main_bp.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')

@main_bp.route('/features')
def features():
    """功能介绍页面"""
    return render_template('features.html')

@main_bp.route('/contact')
def contact():
    """联系我们页面"""
    return render_template('contact.html')

# API路由
@main_bp.route('/api/stats')
@login_required
def api_stats():
    """获取用户统计信息API"""
    knowledge_bases = current_user.knowledge_bases.filter_by(is_active=True).all()
    
    stats = {
        'knowledge_bases_count': len(knowledge_bases),
        'conversations_count': current_user.conversations.filter_by(is_active=True).count(),
        'total_documents': sum(kb.document_count for kb in knowledge_bases),
        'total_messages': sum(conv.message_count for conv in current_user.conversations),
        'total_storage_size': sum(kb.total_size for kb in knowledge_bases)
    }
    
    return jsonify({'success': True, 'stats': stats})

@main_bp.route('/api/knowledge_bases')
@login_required  
def api_knowledge_bases():
    """获取用户知识库列表API"""
    knowledge_bases = current_user.knowledge_bases.filter_by(is_active=True).all()
    return jsonify({
        'success': True,
        'knowledge_bases': [kb.to_dict() for kb in knowledge_bases]
    })

@main_bp.route('/api/conversations')
@login_required
def api_conversations():
    """获取用户对话列表API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    conversations = current_user.conversations.filter_by(is_active=True)\
                   .order_by(Conversation.updated_at.desc())\
                   .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'conversations': [conv.to_dict() for conv in conversations.items],
        'pagination': {
            'page': page,
            'pages': conversations.pages,
            'per_page': per_page,
            'total': conversations.total,
            'has_next': conversations.has_next,
            'has_prev': conversations.has_prev
        }
    })

# 错误处理
@main_bp.app_errorhandler(404)
def not_found_error(error):
    """404错误处理"""
    return render_template('errors/404.html'), 404

@main_bp.app_errorhandler(500)
def internal_error(error):
    """500错误处理"""
    db.session.rollback()
    return render_template('errors/500.html'), 500 