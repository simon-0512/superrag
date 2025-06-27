#!/usr/bin/env python3
"""
SuperRAG 数据库管理工具

使用方法:
    python manage.py init_db              # 初始化数据库
    python manage.py reset_db             # 重置数据库
    python manage.py create_sample_data   # 创建示例数据
    python manage.py db_info              # 显示数据库信息
    python manage.py health_check         # 数据库健康检查
"""

import sys
import os
from flask import Flask

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 基本配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # 初始化数据库
    from app.database import init_database
    init_database(app)
    
    # 初始化认证系统
    from app.auth import init_auth
    init_auth(app)
    
    return app

def init_db():
    """初始化数据库"""
    print("🚀 正在初始化数据库...")
    app = create_app()
    
    from app.database import create_tables, init_sample_data
    
    create_tables(app)
    init_sample_data(app)
    
    print("✅ 数据库初始化完成！")
    print("   可以访问 http://127.0.0.1:5000 开始使用系统")

def reset_db():
    """重置数据库"""
    app = create_app()
    
    from app.database import reset_database
    
    # 确认操作
    confirm = input("⚠️  这将删除所有数据！确认重置数据库？(y/N): ")
    if confirm.lower() != 'y':
        print("❌ 操作已取消")
        return
    
    reset_database(app)

def create_sample_data():
    """创建示例数据"""
    print("📝 正在创建示例数据...")
    app = create_app()
    
    from app.database import init_sample_data
    init_sample_data(app)

def db_info():
    """显示数据库信息"""
    app = create_app()
    
    from app.database import get_database_info
    info = get_database_info(app)
    
    print("📊 数据库信息:")
    print(f"   数据库URI: {info['database_uri']}")
    print("   数据表统计:")
    for table, count in info['tables'].items():
        print(f"     - {table}: {count} 条记录")

def health_check():
    """数据库健康检查"""
    app = create_app()
    
    from app.database import health_check as db_health_check
    result = db_health_check(app)
    
    status_icon = "✅" if result['status'] == 'healthy' else "❌"
    print(f"{status_icon} 数据库状态: {result['status']}")
    print(f"   信息: {result['message']}")

def create_user():
    """创建新用户"""
    app = create_app()
    
    with app.app_context():
        from app.models import User
        from app.database import db
        
        print("👤 创建新用户")
        username = input("用户名: ")
        email = input("邮箱: ")
        password = input("密码: ")
        nickname = input("昵称 (可选): ")
        
        if not username or not email or not password:
            print("❌ 用户名、邮箱和密码不能为空")
            return
        
        # 检查用户是否已存在
        if User.query.filter_by(username=username).first():
            print(f"❌ 用户名 '{username}' 已存在")
            return
        
        if User.query.filter_by(email=email).first():
            print(f"❌ 邮箱 '{email}' 已被注册")
            return
        
        # 创建用户
        user = User(username=username, email=email, password=password)
        if nickname:
            user.nickname = nickname
        
        db.session.add(user)
        db.session.commit()
        
        print(f"✅ 用户 '{username}' 创建成功！")

def list_users():
    """列出所有用户"""
    app = create_app()
    
    with app.app_context():
        from app.models import User
        
        users = User.query.all()
        
        if not users:
            print("📝 暂无用户")
            return
        
        print(f"👥 用户列表 (共 {len(users)} 人):")
        print("-" * 80)
        print(f"{'ID':<36} {'用户名':<15} {'昵称':<15} {'邮箱':<25} {'状态'}")
        print("-" * 80)
        
        for user in users:
            status = "活跃" if user.is_active else "禁用"
            print(f"{user.id:<36} {user.username:<15} {user.nickname or '':<15} {user.email:<25} {status}")

def show_help():
    """显示帮助信息"""
    print(__doc__)
    print("\n可用命令:")
    print("  init_db             - 初始化数据库")
    print("  reset_db            - 重置数据库 (谨慎使用)")
    print("  create_sample_data  - 创建示例数据")
    print("  db_info             - 显示数据库信息")
    print("  health_check        - 数据库健康检查")
    print("  create_user         - 创建新用户")
    print("  list_users          - 列出所有用户")
    print("  help                - 显示此帮助信息")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    commands = {
        'init_db': init_db,
        'reset_db': reset_db,
        'create_sample_data': create_sample_data,
        'db_info': db_info,
        'health_check': health_check,
        'create_user': create_user,
        'list_users': list_users,
        'help': show_help,
    }
    
    if command in commands:
        try:
            commands[command]()
        except Exception as e:
            print(f"❌ 执行命令时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print(f"❌ 未知命令: {command}")
        show_help()

if __name__ == '__main__':
    main() 