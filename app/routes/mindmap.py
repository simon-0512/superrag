"""
思维导图路由和API
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.mindmap import Mindmap, MindmapNode, MindmapAIExpansion
from app.models.user import User
from app.database import db
import json
from datetime import datetime
import uuid

mindmap_bp = Blueprint('mindmap', __name__, url_prefix='/mindmap')

@mindmap_bp.route('/')
@mindmap_bp.route('/<mindmap_id>')
@login_required
def index(mindmap_id=None):
    """思维导图主页 - 编辑指定思维导图或最新思维导图"""
    # 获取用户所有思维导图用于侧边栏
    user_mindmaps = Mindmap.query.filter_by(user_id=current_user.id)\
        .order_by(Mindmap.updated_at.desc()).all()
    
    if mindmap_id:
        # 编辑指定的思维导图
        mindmap = Mindmap.query.get_or_404(mindmap_id)
        
        # 检查权限
        if mindmap.user_id != current_user.id and not current_user.role == 'admin':
            flash('您没有权限编辑此思维导图', 'error')
            return redirect(url_for('mindmap.index'))
    else:
        # 加载用户最新的思维导图，如果没有则为None
        mindmap = user_mindmaps[0] if user_mindmaps else None
    
    return render_template('mindmap/editor.html', 
                          mindmap=mindmap, 
                          mindmaps=[m.to_dict() for m in user_mindmaps])

@mindmap_bp.route('/view/<mindmap_id>')
def view(mindmap_id):
    """查看思维导图（支持公开访问）"""
    mindmap = Mindmap.query.get_or_404(mindmap_id)
    
    # 检查访问权限
    if not mindmap.is_public:
        if not current_user.is_authenticated or mindmap.user_id != current_user.id:
            flash('此思维导图不公开访问', 'error')
            return redirect(url_for('main.index'))
    
    return render_template('mindmap/view.html', mindmap=mindmap)

# API 路由
@mindmap_bp.route('/api/list', methods=['GET'])
@login_required
def api_list():
    """获取思维导图列表API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 分页查询
        mindmaps = Mindmap.query.filter_by(user_id=current_user.id)\
            .order_by(Mindmap.updated_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'mindmaps': [mindmap.to_dict() for mindmap in mindmaps.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': mindmaps.total,
                    'pages': mindmaps.pages
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@mindmap_bp.route('/api/create', methods=['POST'])
@login_required
def api_create():
    """创建思维导图API"""
    try:
        data = request.get_json()
        
        mindmap = Mindmap(
            title=data.get('title', '新建思维导图'),
            description=data.get('description', ''),
            user_id=current_user.id,
            canvas_data=data.get('canvas_data', {}),
            is_public=data.get('is_public', False),
            tags=data.get('tags', [])
        )
        
        db.session.add(mindmap)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': mindmap.to_dict(),
            'message': '思维导图创建成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@mindmap_bp.route('/api/get/<mindmap_id>', methods=['GET'])
@login_required
def api_get(mindmap_id):
    """获取思维导图详情API"""
    try:
        mindmap = Mindmap.query.get_or_404(mindmap_id)
        
        # 检查访问权限
        if not mindmap.is_public and mindmap.user_id != current_user.id:
            return jsonify({'success': False, 'error': '没有访问权限'}), 403
        
        return jsonify({
            'success': True,
            'data': mindmap.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@mindmap_bp.route('/api/update/<mindmap_id>', methods=['PUT'])
@login_required
def api_update(mindmap_id):
    """更新思维导图API"""
    try:
        mindmap = Mindmap.query.get_or_404(mindmap_id)
        
        # 检查权限
        if mindmap.user_id != current_user.id and not current_user.role == 'admin':
            return jsonify({'success': False, 'error': '没有修改权限'}), 403
        
        data = request.get_json()
        
        # 更新字段
        if 'title' in data:
            mindmap.title = data['title']
        if 'description' in data:
            mindmap.description = data['description']
        if 'canvas_data' in data:
            mindmap.canvas_data = data['canvas_data']
        if 'is_public' in data:
            mindmap.is_public = data['is_public']
        if 'tags' in data:
            mindmap.tags = data['tags']
        
        mindmap.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': mindmap.to_dict(),
            'message': '思维导图更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@mindmap_bp.route('/api/delete/<mindmap_id>', methods=['DELETE'])
@login_required
def api_delete(mindmap_id):
    """删除思维导图API"""
    try:
        mindmap = Mindmap.query.get_or_404(mindmap_id)
        
        # 检查权限
        if mindmap.user_id != current_user.id and not current_user.role == 'admin':
            return jsonify({'success': False, 'error': '没有删除权限'}), 403
        
        db.session.delete(mindmap)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '思维导图删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@mindmap_bp.route('/api/duplicate/<mindmap_id>', methods=['POST'])
@login_required
def api_duplicate(mindmap_id):
    """复制思维导图API"""
    try:
        original = Mindmap.query.get_or_404(mindmap_id)
        
        # 检查访问权限
        if not original.is_public and original.user_id != current_user.id:
            return jsonify({'success': False, 'error': '没有访问权限'}), 403
        
        # 创建副本
        duplicate = Mindmap(
            title=f"{original.title} (副本)",
            description=original.description,
            user_id=current_user.id,
            canvas_data=original.canvas_data,
            is_public=False,
            tags=original.tags
        )
        
        db.session.add(duplicate)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': duplicate.to_dict(),
            'message': '思维导图复制成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@mindmap_bp.route('/api/export/<mindmap_id>', methods=['GET'])
@login_required
def api_export(mindmap_id):
    """导出思维导图API"""
    try:
        mindmap = Mindmap.query.get_or_404(mindmap_id)
        
        # 检查访问权限
        if not mindmap.is_public and mindmap.user_id != current_user.id:
            return jsonify({'success': False, 'error': '没有访问权限'}), 403
        
        export_format = request.args.get('format', 'json')
        
        if export_format == 'json':
            return jsonify({
                'success': True,
                'data': mindmap.to_dict()
            })
        else:
            return jsonify({'success': False, 'error': '不支持的导出格式'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@mindmap_bp.route('/api/public', methods=['GET'])
def api_public():
    """获取公开的思维导图列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 分页查询公开的思维导图
        mindmaps = Mindmap.query.filter_by(is_public=True)\
            .order_by(Mindmap.updated_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'mindmaps': [mindmap.to_dict() for mindmap in mindmaps.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': mindmaps.total,
                    'pages': mindmaps.pages
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
@mindmap_bp.route("/api/ai_expand", methods=["POST"])
@login_required
def api_ai_expand():
    """AI智能扩展节点"""
    try:
        data = request.get_json()
        node_text = data.get("node_text", "")
        expand_type = data.get("type", "expand")  # expand 或 explain
        context = data.get("context", "")
        
        # 导入AI服务
        from app.services.deepseek_service import DeepSeekService
        ai_service = DeepSeekService()
        
        if expand_type == "expand":
            prompt = f"请为以下思维导图节点生成3-5个相关的子节点，只返回节点文本，每行一个：\n节点：{node_text}\n上下文：{context}"
        else:  # explain
            prompt = f"请为以下思维导图节点提供详细说明，控制在100字以内：\n节点：{node_text}\n上下文：{context}"
        
        response = ai_service.generate_response([{"role": "user", "content": prompt}])
        
        if expand_type == "expand":
            # 解析扩展节点
            lines = response.strip().split("\n")
            nodes = [line.strip() for line in lines if line.strip()]
            result = {"nodes": nodes}
        else:
            result = {"explanation": response.strip()}
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@mindmap_bp.route('/api/share/<mindmap_id>', methods=['POST'])
@login_required
def api_share(mindmap_id):
    """分享思维导图到社区"""
    try:
        mindmap = Mindmap.query.get_or_404(mindmap_id)
        
        # 检查权限
        if mindmap.user_id != current_user.id and not current_user.role == 'admin':
            return jsonify({'success': False, 'error': '没有分享权限'}), 403
        
        # 设置为公开
        mindmap.is_public = True
        mindmap.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '思维导图已分享到社区',
            'data': mindmap.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

