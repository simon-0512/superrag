#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain 集成测试脚本
验证 LangChain 功能是否正常工作
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath('.'))

def test_imports():
    """测试所需模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        # 使用新版本的导入路径
        from langchain_community.chat_message_histories import ChatMessageHistory
        from langchain.memory import ConversationSummaryBufferMemory, ConversationBufferWindowMemory
        from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
        from langchain_core.language_models.llms import LLM
        print("   ✅ 模块导入成功")
        modules_imported = True
        
        # 测试项目模块导入
        from app.services.langchain_service import LangChainContextService, DatabaseChatMessageHistory, CustomDeepSeekLLM
        print("   ✅ 项目 LangChain 服务导入成功")
        
        from app.services.conversation_service import ConversationService
        print("   ✅ 对话服务导入成功")
        
        from config.settings import BaseConfig
        print("   ✅ 配置模块导入成功")
        
        return True
    except ImportError as e:
        print(f"   ❌ 模块导入失败: {e}")
        return False

def test_config():
    """测试配置"""
    print("\n🔧 测试配置...")
    
    try:
        from config.settings import BaseConfig
        
        config_items = [
            ("LANGCHAIN_ENABLE", getattr(BaseConfig, 'LANGCHAIN_ENABLE', None)),
            ("LANGCHAIN_MEMORY_TYPE", getattr(BaseConfig, 'LANGCHAIN_MEMORY_TYPE', None)),
            ("CONVERSATION_SUMMARY_TOKEN_LIMIT", getattr(BaseConfig, 'CONVERSATION_SUMMARY_TOKEN_LIMIT', None)),
            ("LANGCHAIN_WINDOW_SIZE", getattr(BaseConfig, 'LANGCHAIN_WINDOW_SIZE', None)),
        ]
        
        for name, value in config_items:
            if value is not None:
                print(f"   ✅ {name}: {value}")
            else:
                print(f"   ⚠️ {name}: 未配置（将使用默认值）")
        
        return True
    except Exception as e:
        print(f"   ❌ 配置测试失败: {e}")
        return False

def test_memory_creation():
    """测试记忆对象创建"""
    print("\n🧠 测试记忆对象创建...")
    
    try:
        from langchain.memory import ConversationSummaryBufferMemory, ConversationBufferWindowMemory
        from langchain.memory.chat_message_histories import BaseChatMessageHistory
        from langchain.schema import HumanMessage, AIMessage
        
        # 创建简单的内存记忆历史
        class SimpleMemory(BaseChatMessageHistory):
            def __init__(self):
                self._messages = []
            
            @property
            def messages(self):
                return self._messages
            
            def add_message(self, message):
                self._messages.append(message)
            
            def clear(self):
                self._messages = []
        
        # 测试滑动窗口记忆
        simple_memory = SimpleMemory()
        window_memory = ConversationBufferWindowMemory(
            chat_memory=simple_memory,
            k=5,
            return_messages=True
        )
        print("   ✅ 滑动窗口记忆创建成功")
        
        # 添加测试消息
        simple_memory.add_message(HumanMessage(content="你好"))
        simple_memory.add_message(AIMessage(content="你好！我是AI助手"))
        simple_memory.add_message(HumanMessage(content="今天天气怎么样？"))
        
        # 获取记忆变量
        memory_vars = window_memory.load_memory_variables({})
        print(f"   ✅ 记忆变量获取成功，消息数: {len(memory_vars.get('chat_history', []))}")
        
        return True
    except Exception as e:
        print(f"   ❌ 记忆对象创建失败: {e}")
        return False

def test_custom_llm():
    """测试自定义LLM包装器"""
    print("\n🤖 测试自定义LLM包装器...")
    
    try:
        from app.services.langchain_service import CustomDeepSeekLLM
        
        # 创建模拟的 DeepSeek 服务
        class MockDeepSeekService:
            def chat_completion(self, messages, stream=False):
                return {
                    'success': True,
                    'data': {
                        'choices': [{
                            'message': {
                                'content': "这是一个测试响应"
                            }
                        }]
                    }
                }
        
        mock_service = MockDeepSeekService()
        custom_llm = CustomDeepSeekLLM(mock_service)
        
        # 测试LLM调用
        response = custom_llm._call("测试提示")
        print(f"   ✅ 自定义LLM调用成功: {response}")
        
        return True
    except Exception as e:
        print(f"   ❌ 自定义LLM测试失败: {e}")
        return False

def test_conversation_service():
    """测试对话服务"""
    print("\n💬 测试对话服务...")
    
    try:
        from app.services.conversation_service import ConversationService
        
        # 创建对话服务（不依赖数据库）
        service = ConversationService()
        
        print(f"   ✅ 对话服务创建成功")
        print(f"   📊 LangChain 启用状态: {service.langchain_enabled}")
        print(f"   📊 总结轮数: {service.summary_rounds}")
        print(f"   📊 最大上下文消息: {service.max_context_messages}")
        
        return True
    except Exception as e:
        print(f"   ❌ 对话服务测试失败: {e}")
        return False

def test_langchain_service():
    """测试LangChain服务"""
    print("\n🔗 测试LangChain服务...")
    
    try:
        from app.services.langchain_service import LangChainContextService
        
        # 创建模拟的 DeepSeek 服务
        class MockDeepSeekService:
            def chat_completion(self, messages, stream=False):
                return {
                    'success': True,
                    'data': {
                        'choices': [{
                            'message': {
                                'content': "测试摘要内容"
                            }
                        }]
                    }
                }
        
        mock_service = MockDeepSeekService()
        langchain_service = LangChainContextService(mock_service)
        
        print("   ✅ LangChain服务创建成功")
        print(f"   📊 Token限制: {langchain_service.max_token_limit}")
        print(f"   📊 总结轮数: {langchain_service.summary_rounds}")
        
        return True
    except Exception as e:
        print(f"   ❌ LangChain服务测试失败: {e}")
        return False

def generate_test_report():
    """生成测试报告"""
    print("\n📊 生成测试报告...")
    
    test_results = {
        "test_time": datetime.now().isoformat(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "test_results": {}
    }
    
    try:
        # 收集版本信息
        import langchain
        test_results["langchain_version"] = getattr(langchain, '__version__', 'unknown')
    except:
        test_results["langchain_version"] = 'not_installed'
    
    return test_results

def main():
    """主测试函数"""
    print("🧪 SuperRAG LangChain 集成测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行所有测试
    tests = [
        ("模块导入", test_imports),
        ("配置检查", test_config),
        ("记忆对象创建", test_memory_creation),
        ("自定义LLM", test_custom_llm),
        ("对话服务", test_conversation_service),
        ("LangChain服务", test_langchain_service),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ {test_name} 测试异常: {e}")
            test_results.append((test_name, False))
    
    # 输出测试总结
    print("\n📋 测试总结:")
    print("-" * 30)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 测试结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！LangChain 集成准备就绪")
        print("\n💡 下一步:")
        print("1. 启动应用: python run.py")
        print("2. 访问 http://localhost:5000/langchain 测试功能")
        return True
    else:
        print(f"\n⚠️ 有 {total - passed} 项测试失败，请检查配置和依赖")
        print("\n🔧 建议:")
        print("1. 运行 python install_langchain.py 重新安装依赖")
        print("2. 检查 .env 文件中的 LangChain 配置")
        print("3. 确保在虚拟环境中运行")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 