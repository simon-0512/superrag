"""
AI思维导图API路由
提供AI扩展、说明、优化等功能的RESTful接口
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.ai_mindmap_service import AIMindmapService
from app.models.mindmap import Mindmap
from app.database import db
import logging

logger = logging.getLogger(__name__)

ai_mindmap_bp = Blueprint('ai_mindmap', __name__, url_prefix='/mindmap/ai')

# 初始化AI服务
ai_service = AIMindmapService()


def expand_node():
    """
    AI智能扩展节点
    
    Request Body:
    {
        "node_text": "节点文本",
        "mindmap_id": "思维导图ID",
        "context": {
            "parent": "父节点文本",
            "siblings": ["同级节点1", "同级节点2"]
        },
        "mode": "creative|deep_analysis|practical|academic",
        "count": 4,
        "include_parent": true,
        "include_siblings": false
    }
    """
    try:
        data = request.get_json()
        
        # 验证必要参数
        if not data or not data.get('node_text'):
            return jsonify({
                'success': False,
                'error': '缺少必要参数: node_text'
            }), 400
        
        node_text = data['node_text']
        mindmap_id = data.get('mindmap_id')
        context = data.get('context', {})
        mode = data.get('mode', 'creative')
        count = data.get('count', 4)
        include_parent = data.get('include_parent', True)
        include_siblings = data.get('include_siblings', False)
        
        # 验证用户权限
        if mindmap_id:
            mindmap = Mindmap.query.get(mindmap_id)
            if not mindmap or (mindmap.user_id != current_user.id and not current_user.role == 'admin'):
                return jsonify({
                    'success': False,
                    'error': '无权限访问该思维导图'
                }), 403
        
        # 调用AI服务 - 移除await
        result = ai_service.expand_node(
            node_text=node_text,
            context=context,
            mode=mode,
            count=count,
            include_parent=include_parent,
            include_siblings=include_siblings
        )
        
        # 记录使用统计
        if result.get('success'):
            logger.info(f"用户 {current_user.id} 使用AI扩展节点: {node_text}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"AI节点扩展接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


def explain_node():
    """
    AI智能说明节点
    
    Request Body:
    {
        "node_text": "节点文本",
        "mindmap_id": "思维导图ID",
        "context": {
            "parent": "父节点文本"
        },
        "explanation_type": "summary|detailed|examples|academic"
    }
    """
    try:
        data = request.get_json()
        
        # 验证必要参数
        if not data or not data.get('node_text'):
            return jsonify({
                'success': False,
                'error': '缺少必要参数: node_text'
            }), 400
        
        node_text = data['node_text']
        mindmap_id = data.get('mindmap_id')
        context = data.get('context', {})
        explanation_type = data.get('explanation_type', 'detailed')
        
        # 验证用户权限
        if mindmap_id:
            mindmap = Mindmap.query.get(mindmap_id)
            if not mindmap or (mindmap.user_id != current_user.id and not current_user.role == 'admin'):
                return jsonify({
                    'success': False,
                    'error': '无权限访问该思维导图'
                }), 403
        
        # 调用AI服务 - 移除await
        result = ai_service.explain_node(
            node_text=node_text,
            context=context,
            explanation_type=explanation_type
        )
        
        # 记录使用统计
        if result.get('success'):
            logger.info(f"用户 {current_user.id} 使用AI说明节点: {node_text}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"AI节点说明接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


def generate_theme_mindmap():
    """
    AI生成主题思维导图
    
    Request Body:
    {
        "theme": "主题关键词",
        "framework": "default|swot|5w1h|pyramid",
        "depth": 3
    }
    """
    try:
        data = request.get_json()
        
        # 验证必要参数
        if not data or not data.get('theme'):
            return jsonify({
                'success': False,
                'error': '缺少必要参数: theme'
            }), 400
        
        theme = data['theme']
        framework = data.get('framework', 'default')
        depth = data.get('depth', 3)
        
        # 验证参数范围
        if depth < 1 or depth > 5:
            return jsonify({
                'success': False,
                'error': '深度参数应在1-5之间'
            }), 400
        
        # 调用AI服务 - 移除await
        result = ai_service.generate_theme_mindmap(
            theme=theme,
            framework=framework,
            depth=depth
        )
        
        # 记录使用统计
        if result.get('success'):
            logger.info(f"用户 {current_user.id} 使用AI生成主题: {theme}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"AI主题生成接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@ai_mindmap_bp.route('/usage-stats', methods=['GET'])
@login_required
def get_usage_stats():
    """
    获取AI功能使用统计
    """
    try:
        # TODO: 实现使用统计查询
        # 从数据库查询用户的AI使用记录
        
        stats = {
            'expand_count': 0,
            'explain_count': 0,
            'theme_count': 0,
            'total_count': 0,
            'this_month': 0
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"AI使用统计接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@ai_mindmap_bp.route('/feedback', methods=['POST'])
@login_required
def submit_feedback():
    """
    提交AI功能反馈
    
    Request Body:
    {
        "action": "expand|explain|theme",
        "node_text": "相关节点文本",
        "rating": 1-5,
        "feedback": "用户反馈内容"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '缺少反馈数据'
            }), 400
        
        action = data.get('action')
        node_text = data.get('node_text', '')
        rating = data.get('rating')
        feedback = data.get('feedback', '')
        
        # 验证参数
        if not action or rating is None:
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400
        
        if rating < 1 or rating > 5:
            return jsonify({
                'success': False,
                'error': '评分应在1-5之间'
            }), 400
        
        # TODO: 保存反馈到数据库
        logger.info(f"收到AI功能反馈: 用户{current_user.id}, 操作{action}, 评分{rating}")
        
        return jsonify({
            'success': True,
            'message': '反馈提交成功'
        })
        
    except Exception as e:
        logger.error(f"AI反馈接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


# 修正路由，添加登录验证
@login_required
def expand_node_wrapper():
    """节点扩展接口包装器"""
    return expand_node()


@login_required  
def explain_node_wrapper():
    """节点说明接口包装器"""
    return explain_node()


@login_required
def generate_theme_wrapper():
    """主题生成接口包装器"""
    return generate_theme_mindmap()


# 注册路由
ai_mindmap_bp.add_url_rule('/expand', 'expand_node', expand_node_wrapper, methods=['POST'])
ai_mindmap_bp.add_url_rule('/explain', 'explain_node', explain_node_wrapper, methods=['POST'])
ai_mindmap_bp.add_url_rule('/generate-theme', 'generate_theme', generate_theme_wrapper, methods=['POST']) 