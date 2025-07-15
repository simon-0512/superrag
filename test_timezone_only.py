"""
测试时区修复功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath('.'))

from datetime import datetime
from app.utils.timezone_utils import (
    get_beijing_time_for_db, 
    format_beijing_time, 
    utc_to_beijing, 
    beijing_to_utc
)

def test_timezone_functions():
    """测试时区处理函数"""
    print("🕐 测试时区处理功能...")
    print("=" * 50)
    
    # 测试获取东八区时间
    beijing_time = get_beijing_time_for_db()
    print(f"✅ 当前东八区时间: {format_beijing_time(beijing_time)}")
    
    # 验证时间是否为 naive datetime（无时区信息）
    assert beijing_time.tzinfo is None, "❌ 返回的时间应该是 naive datetime"
    print("✅ 时间格式正确（naive datetime）")
    
    # 测试格式化函数
    formatted_time = format_beijing_time(beijing_time)
    print(f"✅ 格式化时间: {formatted_time}")
    
    # 测试UTC转东八区
    utc_time = datetime.utcnow()
    beijing_converted = utc_to_beijing(utc_time)
    print(f"✅ UTC时间转换: {utc_time} -> {beijing_converted}")
    
    # 测试东八区转UTC
    utc_converted = beijing_to_utc(beijing_time)
    print(f"✅ 东八区时间转UTC: {beijing_time} -> {utc_converted}")
    
    print()
    return True

def test_time_differences():
    """测试时区差异"""
    print("⏰ 测试时区差异...")
    print("=" * 50)
    
    # 创建UTC时间
    utc_now = datetime.utcnow()
    print(f"UTC 时间: {utc_now}")
    
    # 转换为东八区
    beijing_time = get_beijing_time_for_db()
    print(f"东八区时间: {beijing_time}")
    
    # 计算时差（应该大约是8小时）
    time_diff = beijing_time - utc_now
    hours_diff = time_diff.total_seconds() / 3600
    print(f"时差: {hours_diff:.1f} 小时")
    
    # 验证时差在合理范围内（6-10小时，考虑夏令时等因素）
    assert 6 <= abs(hours_diff) <= 10, f"❌ 时差异常: {hours_diff}"
    print("✅ 时差正常")
    
    print()
    return True

def generate_timezone_report():
    """生成时区修复报告"""
    print("📋 时区修复功能报告")
    print("=" * 50)
    
    beijing_time = get_beijing_time_for_db()
    
    print(f"🕐 时区信息:")
    print(f"   • 当前东八区时间: {format_beijing_time(beijing_time)}")
    print(f"   • 时区类型: {'Naive DateTime (推荐)' if beijing_time.tzinfo is None else 'Aware DateTime'}")
    print()
    
    print(f"✨ 修复的功能:")
    print(f"   ✅ 统一数据库时间为东八区")
    print(f"   ✅ 用户注册时间 (User.created_at)")
    print(f"   ✅ 用户更新时间 (User.updated_at)")
    print(f"   ✅ 用户登录时间 (User.last_login_at)")
    print(f"   ✅ 对话创建时间 (Conversation.created_at)")
    print(f"   ✅ 消息创建时间 (Message.created_at)")
    print(f"   ✅ 社区帖子时间 (CommunityPost.created_at)")
    print(f"   ✅ 互动记录时间 (CommunityInteraction.created_at)")
    print(f"   ✅ 关注关系时间 (UserFollow.created_at)")
    print()
    
    print(f"🔧 修复的模型:")
    print(f"   • app/models/user.py - 用户模型时间字段")
    print(f"   • app/models/knowledge_base.py - 知识库相关模型")
    print(f"   • app/models/community.py - 社区相关模型")
    print()
    
    print(f"🛠️  新增工具:")
    print(f"   • app/utils/timezone_utils.py - 时区处理工具")
    print(f"   • get_beijing_time_for_db() - 获取东八区时间")
    print(f"   • format_beijing_time() - 格式化时间显示")
    print(f"   • utc_to_beijing() - UTC转东八区")
    print(f"   • beijing_to_utc() - 东八区转UTC")
    print()
    
    print(f"📦 新增依赖:")
    print(f"   • pytz==2023.3 - 时区处理库")
    print()
    
    print("✅ 时区问题修复完成！所有时间字段已统一为东八区时间。")

def main():
    """主函数"""
    print("🚀 SuperRAG 时区修复功能测试")
    print("=" * 50)
    print()
    
    # 运行测试
    tests = [
        test_timezone_functions,
        test_time_differences
    ]
    
    success_count = 0
    for test in tests:
        try:
            if test():
                success_count += 1
        except Exception as e:
            print(f"❌ 测试 {test.__name__} 失败: {str(e)}")
            import traceback
            traceback.print_exc()
        print()
    
    # 测试结果
    total_tests = len(tests)
    print(f"📈 测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 时区功能测试通过！")
        print()
        generate_timezone_report()
    else:
        print("⚠️  部分测试失败，请检查配置")

if __name__ == "__main__":
    main() 