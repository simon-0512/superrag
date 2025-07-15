#!/usr/bin/env python3
"""
数据库清理脚本
删除冗余的数据表和修复数据类型问题
"""

import os
import sys
import sqlite3
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def cleanup_redundant_tables(db_path):
    """清理冗余的表"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"🗄️  开始清理数据库: {db_path}")
        print(f"⏰ 清理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        tables_to_remove = ['roles', 'user_roles']
        
        for table in tables_to_remove:
            if table in existing_tables:
                # 检查表中是否有数据
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                if count > 0:
                    print(f"⚠️  警告: {table} 表中有 {count} 条数据，请确认是否继续删除？")
                    response = input(f"是否删除 {table} 表？(y/N): ")
                    if response.lower() != 'y':
                        print(f"跳过删除 {table} 表")
                        continue
                
                # 删除表
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"✅ 已删除冗余表: {table}")
            else:
                print(f"ℹ️  表 {table} 不存在，跳过")
        
        conn.commit()
        print()
        print("🎉 数据库清理完成！")
        
        # 显示清理后的表列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        remaining_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 剩余数据表 ({len(remaining_tables)} 个):")
        for table in remaining_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   - {table}: {count} 条记录")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        return False
    
    return True

def backup_database(db_path):
    """备份数据库"""
    try:
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 使用sqlite3命令进行备份
        import shutil
        shutil.copy2(db_path, backup_path)
        
        print(f"📦 数据库备份完成: {backup_path}")
        return backup_path
        
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return None

def show_database_structure(db_path):
    """显示数据库结构"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📊 当前数据库结构:")
        print("=" * 50)
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            print(f"\n🔸 {table}")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_id, name, col_type, not_null, default, pk = col
                nullable = "NOT NULL" if not_null else "NULL"
                pk_info = " (PRIMARY KEY)" if pk else ""
                default_info = f" DEFAULT {default}" if default is not None else ""
                print(f"   {name}: {col_type} {nullable}{default_info}{pk_info}")
            
            # 获取记录数量
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   📊 记录数: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 获取数据库结构失败: {e}")

def main():
    """主函数"""
    # 数据库路径
    db_paths = [
        'instance/superrag_dev.db',
        'instance/superrag.db'
    ]
    
    print("🚀 SuperRAG 数据库清理工具")
    print("=" * 40)
    print()
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"📁 发现数据库: {db_path}")
            
            # 显示当前结构
            show_database_structure(db_path)
            print()
            
            # 询问是否继续
            response = input(f"是否对 {db_path} 执行清理操作？(y/N): ")
            if response.lower() != 'y':
                print("跳过清理")
                continue
            
            # 备份数据库
            backup_path = backup_database(db_path)
            if not backup_path:
                print("备份失败，跳过清理")
                continue
            
            # 执行清理
            if cleanup_redundant_tables(db_path):
                print(f"✅ {db_path} 清理成功")
            else:
                print(f"❌ {db_path} 清理失败")
                # 恢复备份
                print("正在恢复备份...")
                shutil.copy2(backup_path, db_path)
                print("备份已恢复")
            
            print()
        else:
            print(f"⚠️  数据库文件不存在: {db_path}")
    
    print("🏁 清理完成")

if __name__ == "__main__":
    main() 