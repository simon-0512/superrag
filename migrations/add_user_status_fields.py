"""
数据库迁移：为用户表添加状态字段
添加字段：disabled(是否禁用)、deleted(是否软删除)
"""

from app.database import db

def upgrade():
    """升级数据库"""
    try:
        # 添加 disabled 字段
        db.engine.execute("""
            ALTER TABLE users 
            ADD COLUMN disabled BOOLEAN DEFAULT FALSE NOT NULL
        """)
        
        # 添加 deleted 字段  
        db.engine.execute("""
            ALTER TABLE users 
            ADD COLUMN deleted BOOLEAN DEFAULT FALSE NOT NULL
        """)
        
        print("✅ 用户状态字段添加成功")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        raise

def downgrade():
    """降级数据库"""
    try:
        # 移除字段
        db.engine.execute("ALTER TABLE users DROP COLUMN disabled")
        db.engine.execute("ALTER TABLE users DROP COLUMN deleted")
        
        print("✅ 用户状态字段移除成功")
        
    except Exception as e:
        print(f"❌ 回滚失败: {e}")
        raise

if __name__ == "__main__":
    # 手动执行迁移
    from app import create_app
    app = create_app()
    
    with app.app_context():
        upgrade() 