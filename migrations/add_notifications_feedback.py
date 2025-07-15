"""
创建通知和反馈相关表的迁移脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db
from app.models.notification import Notification, UserFeedback, NotificationView

def upgrade():
    """创建通知和反馈相关表"""
    print("创建通知和反馈相关表...")
    
    try:
        # 创建所有表
        db.create_all()
        print("✓ 所有表创建成功")
        
        # 可以在这里添加一些初始数据
        from app.models.user import User
        from app.models.notification import NotificationType, NotificationStatus
        from datetime import datetime
        
        # 查找第一个管理员用户
        admin_user = User.query.filter_by(role='admin').first()
        if admin_user:
            # 创建一个欢迎通知
            welcome_notification = Notification(
                title="欢迎使用 Agorix！",
                content="感谢您使用 Agorix 系统。我们将通过通知功能为您提供重要的系统更新和功能介绍。",
                type=NotificationType.ANNOUNCEMENT,
                status=NotificationStatus.PUBLISHED,
                priority=5,
                icon="bi-heart",
                color="success",
                created_by=admin_user.id
            )
            db.session.add(welcome_notification)
            
            # 创建一个功能介绍通知
            feature_notification = Notification(
                title="新功能：通知和反馈系统",
                content="我们新增了通知和反馈系统！您可以通过首页的通知按钮查看系统消息，通过反馈按钮向我们提供宝贵建议。",
                type=NotificationType.FEATURE,
                status=NotificationStatus.PUBLISHED,
                priority=3,
                icon="bi-star",
                color="info",
                created_by=admin_user.id
            )
            db.session.add(feature_notification)
            
            db.session.commit()
            print("✓ 初始通知数据创建成功")
        else:
            print("⚠ 未找到管理员用户，跳过初始通知创建")
            
    except Exception as e:
        print(f"✗ 创建表时出错: {str(e)}")
        db.session.rollback()
        raise

def downgrade():
    """删除通知和反馈相关表"""
    print("删除通知和反馈相关表...")
    
    try:
        # 删除表
        db.drop_all(bind=None, tables=[
            NotificationView.__table__,
            UserFeedback.__table__, 
            Notification.__table__
        ])
        print("✓ 通知和反馈表删除成功")
        
    except Exception as e:
        print(f"✗ 删除表时出错: {str(e)}")
        raise

if __name__ == '__main__':
    """直接运行此脚本进行迁移"""
    from app import create_app
    
    app = create_app()
    with app.app_context():
        try:
            upgrade()
            print("\n✅ 数据库迁移完成！")
        except Exception as e:
            print(f"\n❌ 迁移失败: {str(e)}") 