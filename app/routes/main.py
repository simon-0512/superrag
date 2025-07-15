"""
主要路由
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import User, KnowledgeBase, Conversation

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
    """知识库页面"""
    knowledge_bases = current_user.knowledge_bases.filter_by(is_active=True).all()
    return render_template('knowledge.html', knowledge_bases=knowledge_bases)

@main_bp.route('/knowledge/<knowledge_base_id>')
@login_required
def knowledge_detail(knowledge_base_id):
    """知识库详情页面"""
    knowledge_base = KnowledgeBase.query.get_or_404(knowledge_base_id)
    if knowledge_base.user_id != current_user.id:
        flash('您没有权限访问该知识库', 'error')
        return redirect(url_for('main.knowledge'))
    
    documents = knowledge_base.documents.filter_by(is_active=True).all()
    return render_template('knowledge_detail.html', 
                         knowledge_base=knowledge_base,
                         documents=documents)

@main_bp.route('/community')
@login_required
def community():
    """社区页面"""
    return render_template('community.html')

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
    """获取统计数据"""
    knowledge_bases = current_user.knowledge_bases.filter_by(is_active=True).all()
    
    stats = {
        'knowledge_bases_count': len(knowledge_bases),
        'conversations_count': current_user.conversations.filter_by(is_active=True).count(),
        'total_documents': sum(kb.document_count for kb in knowledge_bases),
        'total_messages': sum(conv.message_count for conv in current_user.conversations)
    }
    
    return jsonify({'success': True, 'stats': stats})

@main_bp.route('/api/knowledge_bases')
@login_required  
def api_knowledge_bases():
    """获取知识库列表"""
    knowledge_bases = current_user.knowledge_bases.filter_by(is_active=True).all()
    return jsonify({
        'success': True,
        'knowledge_bases': [
            {
                'id': kb.id,
                'name': kb.name,
                'document_count': kb.document_count,
                'created_at': kb.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for kb in knowledge_bases
        ]
    })

@main_bp.route('/api/conversations')
@login_required
def api_conversations():
    """获取对话列表"""
    conversations = current_user.conversations.filter_by(is_active=True)\
                   .order_by(Conversation.updated_at.desc()).all()
    return jsonify({
        'success': True,
        'conversations': [
            {
                'id': conv.id,
                'title': conv.title,
                'message_count': conv.message_count,
                'updated_at': conv.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for conv in conversations
        ]
    })

# 错误处理
@main_bp.app_errorhandler(404)
def not_found_error(error):
    """404错误处理"""
    return render_template('errors/404.html'), 404

@main_bp.app_errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return render_template('errors/500.html'), 500 