#!/usr/bin/env python3
"""
思维导图数据库表创建脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db

def create_mindmap_tables():
    """创建思维导图相关表"""
    
    # 创建思维导图表
    mindmaps_sql = """
    CREATE TABLE IF NOT EXISTS mindmaps (
        id VARCHAR(36) PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        description TEXT,
        user_id VARCHAR(36) NOT NULL,
        canvas_data JSON NOT NULL,
        thumbnail_url VARCHAR(255),
        is_public BOOLEAN DEFAULT FALSE,
        tags JSON,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """
    
    # 创建思维导图节点表
    mindmap_nodes_sql = """
    CREATE TABLE IF NOT EXISTS mindmap_nodes (
        id VARCHAR(36) PRIMARY KEY,
        mindmap_id VARCHAR(36) NOT NULL,
        parent_id VARCHAR(36),
        content TEXT NOT NULL,
        node_type VARCHAR(20) DEFAULT 'text',
        position_x FLOAT,
        position_y FLOAT,
        style_data JSON,
        ai_metadata JSON,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (mindmap_id) REFERENCES mindmaps(id),
        FOREIGN KEY (parent_id) REFERENCES mindmap_nodes(id)
    );
    """
    
    # 创建AI扩展历史表
    mindmap_ai_expansions_sql = """
    CREATE TABLE IF NOT EXISTS mindmap_ai_expansions (
        id VARCHAR(36) PRIMARY KEY,
        mindmap_id VARCHAR(36) NOT NULL,
        node_id VARCHAR(36) NOT NULL,
        prompt TEXT NOT NULL,
        response TEXT NOT NULL,
        expansion_type VARCHAR(20),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (mindmap_id) REFERENCES mindmaps(id),
        FOREIGN KEY (node_id) REFERENCES mindmap_nodes(id)
    );
    """
    
    try:
        # 执行SQL语句
        db.session.execute(mindmaps_sql)
        db.session.execute(mindmap_nodes_sql)
        db.session.execute(mindmap_ai_expansions_sql)
        db.session.commit()
        
        print("✅ 思维导图数据库表创建成功！")
        print("   - mindmaps: 思维导图主表")
        print("   - mindmap_nodes: 思维导图节点表")
        print("   - mindmap_ai_expansions: AI扩展历史表")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 创建表时发生错误: {str(e)}")
        raise

def main():
    """主函数"""
    print("🚀 开始创建思维导图数据库表...")
    
    app = create_app()
    with app.app_context():
        create_mindmap_tables()
        
    print("✅ 思维导图数据库表创建完成！")

if __name__ == '__main__':
    main()