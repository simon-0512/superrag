"""
数据库初始化和管理
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config.database import get_database_config

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()

def init_database(app: Flask, config_name=None):
    """初始化数据库"""
    
    # 获取数据库配置
    db_config = get_database_config(config_name)
    
    # 应用数据库配置到Flask应用
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': db_config.SQLALCHEMY_DATABASE_URI,
        'SQLALCHEMY_TRACK_MODIFICATIONS': db_config.SQLALCHEMY_TRACK_MODIFICATIONS,
        'SQLALCHEMY_RECORD_QUERIES': db_config.SQLALCHEMY_RECORD_QUERIES,
        'SQLALCHEMY_ECHO': db_config.SQLALCHEMY_ECHO,
        'SQLALCHEMY_ENGINE_OPTIONS': db_config.SQLALCHEMY_ENGINE_OPTIONS
    })
    
    # 初始化数据库扩展
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 确保instance目录存在（SQLite需要）
    instance_path = os.path.join(app.root_path, '..', 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    return db

def create_tables(app: Flask):
    """创建所有数据表"""
    with app.app_context():
        # 导入所有模型以确保它们被注册
        from app.models import User, UserRole, KnowledgeBase, Document, DocumentChunk, Conversation, Message
        
        # 创建所有表
        db.create_all()
        print("✅ 数据库表创建完成")

def drop_tables(app: Flask):
    """删除所有数据表"""
    with app.app_context():
        db.drop_all()
        print("⚠️  所有数据库表已删除")

def init_sample_data(app: Flask):
    """初始化示例数据"""
    with app.app_context():
        from app.models import User, UserRole, KnowledgeBase
        
        # 检查是否已有数据
        if User.query.first():
            print("ℹ️  数据库已有数据，跳过初始化")
            return
        
        # 创建示例用户
        admin_user = User(
            username='admin',
            email='admin@superrag.com',
            password='admin123'
        )
        admin_user.nickname = '系统管理员'
        admin_user.is_verified = True
        admin_user.role = UserRole.ADMIN
        
        tester_user = User(
            username='tester',
            email='tester@superrag.com',
            password='tester123'
        )
        tester_user.nickname = '测试人员'
        tester_user.is_verified = True
        tester_user.role = UserRole.TESTER
        
        vip_user = User(
            username='vipuser',
            email='vip@superrag.com',
            password='vip123'
        )
        vip_user.nickname = 'VIP用户'
        vip_user.is_verified = True
        vip_user.role = UserRole.VIP
        
        test_user = User(
            username='testuser',
            email='test@superrag.com',
            password='test123'
        )
        test_user.nickname = '普通用户'
        test_user.role = UserRole.USER
        
        # 保存用户
        db.session.add(admin_user)
        db.session.add(tester_user)
        db.session.add(vip_user)
        db.session.add(test_user)
        db.session.commit()
        
        # 创建示例知识库
        demo_kb = KnowledgeBase(
            name='演示知识库',
            description='这是一个演示用的知识库，包含了一些示例文档。',
            user_id=admin_user.id,
            is_public=True
        )
        
        personal_kb = KnowledgeBase(
            name='个人笔记',
            description='我的个人学习笔记和资料收集。',
            user_id=test_user.id,
            is_public=False
        )
        
        test_kb = KnowledgeBase(
            name='测试知识库',
            description='用于测试功能的知识库。',
            user_id=tester_user.id,
            is_public=False
        )
        
        vip_kb = KnowledgeBase(
            name='VIP资源库',
            description='VIP用户专属资源。',
            user_id=vip_user.id,
            is_public=False
        )
        
        db.session.add(demo_kb)
        db.session.add(personal_kb)
        db.session.add(test_kb)
        db.session.add(vip_kb)
        db.session.commit()
        
        print("✅ 示例数据初始化完成")
        print(f"   - 管理员账号: admin / admin123 (角色: {admin_user.get_role_name()})")
        print(f"   - 测试账号: tester / tester123 (角色: {tester_user.get_role_name()})")
        print(f"   - VIP账号: vipuser / vip123 (角色: {vip_user.get_role_name()})")
        print(f"   - 普通账号: testuser / test123 (角色: {test_user.get_role_name()})")

def reset_database(app: Flask):
    """重置数据库（删除并重新创建）"""
    print("🔄 正在重置数据库...")
    drop_tables(app)
    create_tables(app)
    init_sample_data(app)
    print("✅ 数据库重置完成")

def get_database_info(app: Flask):
    """获取数据库信息"""
    with app.app_context():
        from app.models import User, UserRole, KnowledgeBase, Document, Conversation, Message
        
        # 统计各角色用户数量
        role_stats = {}
        for role in UserRole:
            count = User.query.filter_by(role=role).count()
            role_stats[role.value] = count
        
        info = {
            'database_uri': app.config['SQLALCHEMY_DATABASE_URI'],
            'tables': {
                'users': User.query.count(),
                'knowledge_bases': KnowledgeBase.query.count(),
                'documents': Document.query.count(),
                'conversations': Conversation.query.count(),
                'messages': Message.query.count()
            },
            'user_roles': role_stats
        }
        
        return info

def health_check(app: Flask):
    """数据库健康检查"""
    try:
        with app.app_context():
            # 尝试执行一个简单的查询
            db.session.execute(db.text('SELECT 1'))
            return {
                'status': 'healthy',
                'message': '数据库连接正常'
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'数据库连接失败: {str(e)}'
        } 