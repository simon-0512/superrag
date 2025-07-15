"""
角色管理API接口
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import User, UserRole
from app.services.role_service import RoleService
from app.database import db

# 创建蓝图
role_api_bp = Blueprint('role_api', __name__, url_prefix='/api/roles')

def require_admin(f):
    """装饰器：要求管理员权限"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        
        if not current_user.is_admin():
            return jsonify({'success': False, 'message': '需要管理员权限'}), 403
        
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@role_api_bp.route('/', methods=['GET'])
@login_required
def get_roles():
    """获取所有角色列表"""
    try:
        # 只有管理员可以查看所有角色
        if not current_user.is_admin():
            return jsonify({'success': False, 'message': '需要管理员权限'}), 403
        
        roles = RoleService.get_all_roles()
        
        return jsonify({
            'success': True,
            'data': roles
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取角色列表失败: {str(e)}'}), 500

@role_api_bp.route('/set', methods=['POST'])
@require_admin
def set_role():
    """设置用户角色"""
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        role_code = data.get('role_code')
        
        if not user_id or not role_code:
            return jsonify({'success': False, 'message': '用户ID和角色代码不能为空'}), 400
        
        success = RoleService.set_user_role(user_id, role_code)
        
        if success:
            user = User.query.get(user_id)
            return jsonify({
                'success': True,
                'message': '角色设置成功',
                'data': {
                    'user_id': user_id,
                    'role_code': role_code,
                    'role_name': user.get_role_name() if user else None
                }
            })
        else:
            return jsonify({'success': False, 'message': '角色设置失败'}), 500
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'角色设置失败: {str(e)}'}), 500

@role_api_bp.route('/user/<user_id>', methods=['GET'])
@login_required
def get_user_role(user_id):
    """获取用户角色"""
    try:
        # 只有管理员或用户本人可以查看
        if not current_user.is_admin() and current_user.id != user_id:
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': user_id,
                'role_code': user.get_role_code(),
                'role_name': user.get_role_name(),
                'is_admin': user.is_admin(),
                'is_tester': user.is_tester(),
                'is_vip': user.is_vip(),
                'is_normal_user': user.is_normal_user(),
                'can_see_test_buttons': user.can_see_test_buttons()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取用户角色失败: {str(e)}'}), 500

@role_api_bp.route('/users/<role_code>', methods=['GET'])
@require_admin
def get_role_users(role_code):
    """获取指定角色的所有用户"""
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        users = RoleService.get_users_by_role(role_code, include_inactive=include_inactive)
        
        return jsonify({
            'success': True,
            'data': [user.to_dict() for user in users]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取角色用户失败: {str(e)}'}), 500

@role_api_bp.route('/statistics', methods=['GET'])
@require_admin
def get_role_statistics():
    """获取角色统计信息"""
    try:
        stats = RoleService.get_role_statistics()
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取统计信息失败: {str(e)}'}), 500 