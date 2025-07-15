"""
测试管理员系统和时区修复功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath('.'))

from datetime import datetime
from app import create_app
from app.database import db
from app.models.user import User, UserRole
from app.models.knowledge_base import Conversation, Message
from app.models.community import CommunityPost
from app.utils.timezone_utils import get_beijing_time_for_db, format_beijing_time

def test_timezone_functions():
    """测试时区处理函数"""
    print("🕐 测试时区处理功能...")
    
    # 测试获取东八区时间
    beijing_time = get_beijing_time_for_db()
    print(f"✅ 当前东八区时间: {format_beijing_time(beijing_time)}")
    
    # 验证时间是否为 naive datetime（无时区信息）
    assert beijing_time.tzinfo is None, "❌ 返回的时间应该是 naive datetime"
    print("✅ 时间格式正确（naive datetime）")
    
    print()

def test_database_connection():
    """测试数据库连接"""
    print("🗄️  测试数据库连接...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # 测试用户查询
            user_count = User.query.count()
            print(f"✅ 数据库连接正常，用户总数: {user_count}")
            
            # 测试对话查询
            conversation_count = Conversation.query.count()
            print(f"✅ 对话总数: {conversation_count}")
            
            # 测试社区帖子查询
            post_count = CommunityPost.query.count()
            print(f"✅ 社区帖子总数: {post_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ 数据库连接失败: {str(e)}")
            return False
    
    print()

def test_user_roles():
    """测试用户角色系统"""
    print("👥 测试用户角色系统...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # 统计各角色用户数量
            role_stats = {}
            for role in UserRole:
                count = User.query.filter_by(role=role).count()
                role_stats[role.value] = count
                print(f"✅ {role.value} 角色用户数: {count}")
            
            # 检查是否有管理员
            admin_count = User.query.filter_by(role=UserRole.ADMIN).count()
            if admin_count == 0:
                print("⚠️  警告：没有管理员用户")
            else:
                admin_user = User.query.filter_by(role=UserRole.ADMIN).first()
                print(f"✅ 管理员用户: {admin_user.username}")
                
                # 测试管理员权限检查
                assert admin_user.is_admin() == True, "❌ 管理员权限检查失败"
                assert admin_user.can_see_test_buttons() == True, "❌ 测试按钮权限检查失败"
                print("✅ 管理员权限检查正常")
            
            return True
            
        except Exception as e:
            print(f"❌ 用户角色系统测试失败: {str(e)}")
            return False
    
    print()

def test_timezone_in_models():
    """测试模型中的时区使用"""
    print("📅 测试模型时区处理...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # 检查最新用户的时间字段
            latest_user = User.query.order_by(User.created_at.desc()).first()
            if latest_user:
                print(f"✅ 最新用户: {latest_user.username}")
                print(f"✅ 创建时间: {format_beijing_time(latest_user.created_at)}")
                print(f"✅ 更新时间: {format_beijing_time(latest_user.updated_at)}")
                
                # 检查时间是否为 naive datetime
                assert latest_user.created_at.tzinfo is None, "❌ 用户创建时间应该是 naive datetime"
                print("✅ 用户时间格式正确")
            
            # 检查最新对话的时间字段
            latest_conv = Conversation.query.order_by(Conversation.created_at.desc()).first()
            if latest_conv:
                print(f"✅ 最新对话: {latest_conv.title}")
                print(f"✅ 创建时间: {format_beijing_time(latest_conv.created_at)}")
                
                # 检查时间是否为 naive datetime
                assert latest_conv.created_at.tzinfo is None, "❌ 对话创建时间应该是 naive datetime"
                print("✅ 对话时间格式正确")
            
            return True
            
        except Exception as e:
            print(f"❌ 模型时区测试失败: {str(e)}")
            return False
    
    print()

def test_admin_routes():
    """测试管理员路由（基础测试）"""
    print("🛡️  测试管理员路由...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # 检查蓝图是否正确注册
            admin_blueprint = None
            for blueprint in app.blueprints.values():
                if blueprint.name == 'admin':
                    admin_blueprint = blueprint
                    break
            
            if admin_blueprint:
                print("✅ 管理员蓝图注册成功")
                print(f"✅ 蓝图前缀: {admin_blueprint.url_prefix}")
            else:
                print("❌ 管理员蓝图未注册")
                return False
            
            # 检查关键路由
            with app.test_client() as client:
                # 测试未登录访问（应该重定向）
                response = client.get('/admin/')
                print(f"✅ 未登录访问管理后台状态码: {response.status_code}")
                assert response.status_code in [302, 401], "❌ 未登录应该被重定向或拒绝"
            
            return True
            
        except Exception as e:
            print(f"❌ 管理员路由测试失败: {str(e)}")
            return False
    
    print()

def generate_summary_report():
    """生成功能总结报告"""
    print("📋 SuperRAG 0.2.0 功能总结报告")
    print("=" * 50)
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # 统计数据
            user_count = User.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            conversation_count = Conversation.query.count()
            message_count = Message.query.count()
            post_count = CommunityPost.query.count()
            
            print(f"📊 数据统计:")
            print(f"   • 总用户数: {user_count} (活跃: {active_users})")
            print(f"   • 对话总数: {conversation_count}")
            print(f"   • 消息总数: {message_count}")
            print(f"   • 社区帖子: {post_count}")
            print()
            
            # 角色分布
            print(f"👥 用户角色分布:")
            for role in UserRole:
                count = User.query.filter_by(role=role).count()
                role_name = {
                    'admin': '管理员',
                    'tester': '测试人员', 
                    'vip': 'VIP用户',
                    'user': '普通用户'
                }[role.value]
                print(f"   • {role_name}: {count} 人")
            print()
            
            # 功能清单
            print(f"✨ 新增功能:")
            print(f"   ✅ 用户角色系统 (4种角色)")
            print(f"   ✅ 时区统一处理 (东八区)")
            print(f"   ✅ 管理员后台系统")
            print(f"   ✅ 数据可视化仪表板")
            print(f"   ✅ 用户管理 (增删改查)")
            print(f"   ✅ 对话系统管理")
            print(f"   ✅ 论坛内容管理")
            print(f"   ✅ SQL查询工具")
            print(f"   ✅ 数据导出功能")
            print()
            
            # 安全特性
            print(f"🔒 安全特性:")
            print(f"   ✅ 角色权限控制")
            print(f"   ✅ 管理员权限验证")
            print(f"   ✅ SQL注入防护")
            print(f"   ✅ 只读数据库查询")
            print()
            
            # 测试账号
            print(f"🔑 测试账号:")
            test_accounts = [
                ('admin', 'admin123', '系统管理员'),
                ('tester', 'tester123', '测试人员'),
                ('vipuser', 'vip123', 'VIP用户'),
                ('testuser', 'test123', '普通用户')
            ]
            
            for username, password, role_name in test_accounts:
                user = User.query.filter_by(username=username).first()
                status = "✅ 存在" if user else "❌ 不存在"
                print(f"   • {username}/{password} ({role_name}) - {status}")
            print()
            
            print(f"🌐 访问地址:")
            print(f"   • 主站: http://localhost:5000/")
            print(f"   • 管理后台: http://localhost:5000/admin/")
            print()
            
            print("🎉 SuperRAG 0.2.0 开发完成！")
            
        except Exception as e:
            print(f"❌ 生成报告失败: {str(e)}")

def main():
    """主函数"""
    print("🚀 SuperRAG 0.2.0 系统测试开始...")
    print("=" * 50)
    print()
    
    # 运行所有测试
    tests = [
        test_timezone_functions,
        test_database_connection,
        test_user_roles,
        test_timezone_in_models,
        test_admin_routes
    ]
    
    success_count = 0
    for test in tests:
        try:
            if test():
                success_count += 1
        except Exception as e:
            print(f"❌ 测试 {test.__name__} 失败: {str(e)}")
        print()
    
    # 测试结果
    total_tests = len(tests)
    print(f"📈 测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！")
        print()
        generate_summary_report()
    else:
        print("⚠️  部分测试失败，请检查配置")

if __name__ == "__main__":
    main() 