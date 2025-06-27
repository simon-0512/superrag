#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain 集成安装脚本
自动安装 LangChain 相关依赖并进行配置检查
"""

import subprocess
import sys
import os
import importlib

def run_command(command):
    """运行系统命令"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 版本过低，需要 Python 3.8 或更高版本")
        return False
    print(f"✅ Python 版本: {version.major}.{version.minor}.{version.micro}")
    return True

def install_packages():
    """安装 LangChain 相关包"""
    packages = [
        "langchain==0.1.0",
        "langchain-core==0.1.0", 
        "langchain-community==0.0.10",
        "langchain-openai==0.0.2",
        "langchain-experimental==0.0.47",
        "chroma-hnswlib==0.7.0",
        "langsmith==0.0.75"
    ]
    
    print("🔧 开始安装 LangChain 相关包...")
    
    for package in packages:
        print(f"   正在安装 {package}...")
        success, output = run_command(f"pip install {package}")
        if success:
            print(f"   ✅ {package} 安装成功")
        else:
            print(f"   ❌ {package} 安装失败: {output}")
            return False
    
    print("✅ 所有 LangChain 包安装完成")
    return True

def check_imports():
    """检查导入是否正常"""
    packages_to_check = [
        ("langchain", "LangChain 核心"),
        ("langchain.memory", "LangChain 记忆模块"),
        ("langchain.chains", "LangChain 链模块"),
        ("langchain_openai", "LangChain OpenAI"),
    ]
    
    print("🔍 检查包导入...")
    
    for package, description in packages_to_check:
        try:
            importlib.import_module(package)
            print(f"   ✅ {description} 导入成功")
        except ImportError as e:
            print(f"   ❌ {description} 导入失败: {e}")
            return False
    
    print("✅ 所有包导入检查通过")
    return True

def create_config_example():
    """创建配置示例文件"""
    config_example = """# LangChain 配置示例
# 添加到你的 .env 文件中

# 启用 LangChain 功能
LANGCHAIN_ENABLE=true

# 记忆类型: summary_buffer, window, summary
LANGCHAIN_MEMORY_TYPE=summary_buffer

# 摘要触发的token阈值
CONVERSATION_SUMMARY_TOKEN_LIMIT=2000

# 是否启用详细日志
LANGCHAIN_VERBOSE=false

# 窗口记忆保留的消息数
LANGCHAIN_WINDOW_SIZE=10

# 摘要最大长度
LANGCHAIN_SUMMARY_MAX_LENGTH=500
"""
    
    try:
        with open('.env.langchain.example', 'w', encoding='utf-8') as f:
            f.write(config_example)
        print("✅ 已创建配置示例文件: .env.langchain.example")
        return True
    except Exception as e:
        print(f"❌ 创建配置示例文件失败: {e}")
        return False

def test_langchain_service():
    """测试 LangChain 服务"""
    try:
        # 尝试导入并创建服务
        sys.path.append('.')
        from app.services.langchain_service import LangChainContextService
        
        print("🧪 测试 LangChain 服务...")
        
        # 创建服务实例（不依赖具体的 DeepSeek 服务）
        # service = LangChainContextService()
        print("   ✅ LangChain 服务类导入成功")
        
        return True
    except Exception as e:
        print(f"   ❌ LangChain 服务测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 SuperRAG LangChain 集成安装程序")
    print("=" * 50)
    
    # 检查 Python 版本
    if not check_python_version():
        sys.exit(1)
    
    # 安装包
    if not install_packages():
        print("❌ 包安装失败，请检查网络连接和 pip 配置")
        sys.exit(1)
    
    # 检查导入
    if not check_imports():
        print("❌ 包导入检查失败，可能存在版本冲突")
        sys.exit(1)
    
    # 创建配置示例
    create_config_example()
    
    # 测试服务
    test_langchain_service()
    
    print("\n🎉 LangChain 集成安装完成！")
    print("\n📋 下一步操作:")
    print("1. 复制 .env.langchain.example 中的配置到你的 .env 文件")
    print("2. 根据需要调整配置参数")
    print("3. 重启应用以启用 LangChain 功能")
    print("4. 访问 /langchain 页面测试功能")
    
    print("\n💡 提示:")
    print("- 如果遇到版本冲突，请尝试在虚拟环境中运行")
    print("- 详细配置说明请参考 README.md")
    print("- 如有问题，请检查日志输出")

if __name__ == "__main__":
    main() 