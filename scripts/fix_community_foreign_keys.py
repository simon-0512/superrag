#!/usr/bin/env python3
"""
修复社区表外键类型不匹配问题
Fix Foreign Key Type Mismatch in Community Tables

问题：
- community_posts.user_id 定义为 INTEGER，但存储 VARCHAR(36) UUID
- community_posts.conversation_id 定义为 INTEGER，但应该是 VARCHAR(36) UUID  
- community_interactions.user_id 定义为 INTEGER，但应该是 VARCHAR(36) UUID
- user_follows.follower_id 和 following_id 定义为 INTEGER，但应该是 VARCHAR(36) UUID

解决方案：
- 重建表结构，修正所有外键字段类型为 VARCHAR(36)
- 迁移现有数据
"""

import sqlite3
import os
from datetime import datetime

def backup_database(db_path):
    """备份数据库"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_foreign_key_fix_{timestamp}"
    
    # 使用 SQLite 的 backup API
    source = sqlite3.connect(db_path)
    backup = sqlite3.connect(backup_path)
    source.backup(backup)
    source.close()
    backup.close()
    
    print(f"✅ 数据库已备份到: {backup_path}")
    return backup_path

def fix_community_posts_table(cursor):
    """修复 community_posts 表"""
    print("🔧 修复 community_posts 表...")
    
    # 1. 重命名原表
    cursor.execute("ALTER TABLE community_posts RENAME TO community_posts_old;")
    
    # 2. 创建新表结构
    cursor.execute("""
        CREATE TABLE community_posts (
            id INTEGER NOT NULL, 
            user_id VARCHAR(36) NOT NULL, 
            content TEXT NOT NULL, 
            ai_prompt TEXT, 
            ai_content_type VARCHAR(12), 
            ai_content_data JSON, 
            conversation_id VARCHAR(36), 
            pdf_url VARCHAR(255), 
            tags JSON, 
            is_featured BOOLEAN, 
            status VARCHAR(9), 
            like_count INTEGER, 
            comment_count INTEGER, 
            share_count INTEGER, 
            view_count INTEGER, 
            created_at DATETIME, 
            updated_at DATETIME, 
            PRIMARY KEY (id), 
            FOREIGN KEY(user_id) REFERENCES users (id), 
            FOREIGN KEY(conversation_id) REFERENCES conversations (id)
        );
    """)
    
    # 3. 迁移数据
    cursor.execute("""
        INSERT INTO community_posts 
        SELECT * FROM community_posts_old;
    """)
    
    # 4. 删除旧表
    cursor.execute("DROP TABLE community_posts_old;")
    
    print("✅ community_posts 表修复完成")

def fix_community_interactions_table(cursor):
    """修复 community_interactions 表"""
    print("🔧 修复 community_interactions 表...")
    
    # 1. 重命名原表
    cursor.execute("ALTER TABLE community_interactions RENAME TO community_interactions_old;")
    
    # 2. 创建新表结构
    cursor.execute("""
        CREATE TABLE community_interactions (
            id INTEGER NOT NULL, 
            user_id VARCHAR(36) NOT NULL, 
            post_id INTEGER NOT NULL, 
            interaction_type VARCHAR(8) NOT NULL, 
            content TEXT, 
            created_at DATETIME, 
            PRIMARY KEY (id), 
            FOREIGN KEY(user_id) REFERENCES users (id), 
            FOREIGN KEY(post_id) REFERENCES community_posts (id), 
            CONSTRAINT uq_user_post_interaction UNIQUE (user_id, post_id, interaction_type)
        );
    """)
    
    # 3. 迁移数据
    cursor.execute("""
        INSERT INTO community_interactions 
        SELECT * FROM community_interactions_old;
    """)
    
    # 4. 删除旧表
    cursor.execute("DROP TABLE community_interactions_old;")
    
    print("✅ community_interactions 表修复完成")

def fix_user_follows_table(cursor):
    """修复 user_follows 表"""
    print("🔧 修复 user_follows 表...")
    
    # 1. 重命名原表
    cursor.execute("ALTER TABLE user_follows RENAME TO user_follows_old;")
    
    # 2. 创建新表结构
    cursor.execute("""
        CREATE TABLE user_follows (
            id INTEGER NOT NULL, 
            follower_id VARCHAR(36) NOT NULL, 
            following_id VARCHAR(36) NOT NULL, 
            created_at DATETIME, 
            PRIMARY KEY (id), 
            FOREIGN KEY(follower_id) REFERENCES users (id), 
            FOREIGN KEY(following_id) REFERENCES users (id), 
            CONSTRAINT uq_follower_following UNIQUE (follower_id, following_id)
        );
    """)
    
    # 3. 迁移数据
    cursor.execute("""
        INSERT INTO user_follows 
        SELECT * FROM user_follows_old;
    """)
    
    # 4. 删除旧表
    cursor.execute("DROP TABLE user_follows_old;")
    
    print("✅ user_follows 表修复完成")

def verify_fix(cursor):
    """验证修复结果"""
    print("🔍 验证修复结果...")
    
    # 测试外键关联是否正常工作
    cursor.execute("""
        SELECT 
            cp.id as post_id,
            cp.user_id as post_user_id,
            u.id as user_id,
            u.username,
            COUNT(*) as total
        FROM community_posts cp
        LEFT JOIN users u ON cp.user_id = u.id
        GROUP BY u.id IS NOT NULL;
    """)
    
    results = cursor.fetchall()
    print("📊 外键关联统计:")
    for row in results:
        status = "成功关联" if row[2] is not None else "未关联"
        print(f"   {status}: {row[4]} 条记录")
    
    # 检查所有表的外键约束
    cursor.execute("PRAGMA foreign_key_check;")
    fk_errors = cursor.fetchall()
    
    if fk_errors:
        print("❌ 发现外键约束错误:")
        for error in fk_errors:
            print(f"   {error}")
        return False
    else:
        print("✅ 所有外键约束检查通过")
        return True

def main():
    """主函数"""
    db_path = "instance/superrag_dev.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    print("🚀 开始修复社区表外键类型不匹配问题...")
    print("=" * 50)
    
    # 备份数据库
    backup_path = backup_database(db_path)
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 先禁用外键约束以避免迁移时的约束冲突
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        # 开始事务
        cursor.execute("BEGIN TRANSACTION;")
        
        # 修复各个表
        fix_community_posts_table(cursor)
        fix_community_interactions_table(cursor)
        fix_user_follows_table(cursor)
        
        # 重新启用外键约束进行验证
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # 验证修复
        if verify_fix(cursor):
            # 提交事务
            conn.commit()
            print("=" * 50)
            print("🎉 社区表外键类型修复成功！")
            print(f"📁 备份文件: {backup_path}")
            print("🔗 现在所有外键关联都应该正常工作了")
        else:
            # 回滚事务
            conn.rollback()
            print("❌ 修复验证失败，已回滚所有更改")
            
    except Exception as e:
        # 回滚事务
        conn.rollback()
        print(f"❌ 修复过程中发生错误: {e}")
        print(f"📁 数据库已从备份恢复: {backup_path}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main() 