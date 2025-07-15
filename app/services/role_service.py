"""
角色管理服务
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models import User, UserRole
from app.database import db

class RoleService:
    """角色管理服务类"""
    
    @staticmethod
    def get_all_roles() -> List[Dict[str, str]]:
        """获取所有可用角色"""
        return [
            {'code': 'admin', 'name': '系统管理员', 'description': '拥有系统所有权限，可以管理用户、数据和系统配置'},
            {'code': 'tester', 'name': '测试人员', 'description': '可以使用测试功能，协助系统测试和问题排查'},
            {'code': 'vip', 'name': 'VIP用户', 'description': 'VIP级别用户，享有高级功能权限'},
            {'code': 'user', 'name': '普通用户', 'description': '基础用户权限，可以使用基本功能'}
        ]
    
    @staticmethod
    def get_role_info(role_code: str) -> Optional[Dict[str, str]]:
        """根据角色代码获取角色信息"""
        roles = RoleService.get_all_roles()
        for role in roles:
            if role['code'] == role_code:
                return role
        return None
    
    @staticmethod
    def set_user_role(user_id: str, role_code: str) -> bool:
        """设置用户角色"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"用户ID {user_id} 不存在")
        
        # 验证角色代码
        if role_code not in ['admin', 'tester', 'vip', 'user']:
            raise ValueError(f"无效的角色代码: {role_code}")
        
        user.set_role(role_code)
        return True
    
    @staticmethod
    def get_user_role(user_id: str) -> Optional[str]:
        """获取用户角色"""
        user = User.query.get(user_id)
        if not user:
            return None
        
        return user.get_role_code()
    
    @staticmethod
    def check_user_permission(user_id: str, permission: str) -> bool:
        """检查用户是否有指定权限"""
        user = User.query.get(user_id)
        if not user:
            return False
        
        return user.has_permission(permission)
    
    @staticmethod
    def get_users_by_role(role_code: str, include_inactive=False) -> List[User]:
        """获取指定角色的所有用户"""
        # 验证角色代码
        if role_code not in ['admin', 'tester', 'vip', 'user']:
            return []
        
        # 转换为枚举值
        role_enum_map = {
            'admin': UserRole.ADMIN,
            'tester': UserRole.TESTER,
            'vip': UserRole.VIP,
            'user': UserRole.USER
        }
        
        query = User.query.filter_by(role=role_enum_map[role_code])
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        return query.all()
    
    @staticmethod
    def bulk_set_roles(user_role_mappings: List[Dict[str, str]]) -> Dict[str, Any]:
        """批量设置角色"""
        success_count = 0
        error_count = 0
        errors = []
        
        for mapping in user_role_mappings:
            try:
                user_id = mapping.get('user_id')
                role_code = mapping.get('role_code')
                
                RoleService.set_user_role(user_id, role_code)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append({
                    'user_id': mapping.get('user_id'),
                    'role_code': mapping.get('role_code'),
                    'error': str(e)
                })
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        }
    
    @staticmethod
    def get_role_statistics() -> Dict[str, Any]:
        """获取角色统计信息"""
        total_users = User.query.count()
        
        # 各角色用户数量统计
        role_stats = {}
        for role in UserRole:
            count = User.query.filter_by(role=role).count()
            role_stats[role.value] = count
        
        return {
            'total_users': total_users,
            'role_distribution': role_stats,
            'roles': RoleService.get_all_roles()
        } 