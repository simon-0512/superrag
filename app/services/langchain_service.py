# -*- coding: utf-8 -*-
"""
LangChain 上下文管理服务
提供基于 LangChain 的智能对话上下文管理功能
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from sqlalchemy.orm import Session

# LangChain相关导入 - 适配新版本0.3.26
try:
    from langchain_community.chat_message_histories import ChatMessageHistory
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain_core.language_models.llms import LLM
    from langchain_core.callbacks.manager import CallbackManagerForLLMRun
    from langchain_core.prompts import PromptTemplate
    from langchain_core.chat_history import BaseChatMessageHistory
    from langchain_core.runnables.history import RunnableWithMessageHistory
    from langchain_core.runnables import Runnable
    from langchain.chains import LLMChain
    from pydantic import Field, BaseModel
    langchain_available = True
except ImportError as e:
    logging.warning(f"LangChain 导入失败: {e}")
    langchain_available = False
    # 定义空类避免导入错误
    class ChatMessageHistory:
        pass
    class BaseMessage:
        pass
    class HumanMessage:
        pass
    class AIMessage:
        pass
    class SystemMessage:
        pass
    class LLM:
        pass
    class PromptTemplate:
        pass
    class BaseChatMessageHistory:
        pass

from app.models import Conversation, Message
from app.database import db
from app.services.deepseek_service import DeepSeekService
from config.settings import BaseConfig

logger = logging.getLogger(__name__)

class DatabaseChatMessageHistory(BaseChatMessageHistory):
    """基于数据库的对话历史管理器，兼容 LangChain 0.3.26"""
    
    def __init__(self, conversation_id: str):
        super().__init__()
        self.conversation_id = conversation_id
        self._messages: List[BaseMessage] = []
        self._load_messages()
    
    @property
    def messages(self) -> List[BaseMessage]:
        """获取消息列表"""
        return self._messages
    
    def add_message(self, message: BaseMessage) -> None:
        """添加消息"""
        self._messages.append(message)
    
    def clear(self) -> None:
        """清空消息"""
        self._messages.clear()
    
    def _load_messages(self):
        """从数据库加载消息历史"""
        try:
            conversation = Conversation.query.filter_by(id=self.conversation_id).first()
            if conversation:
                messages = conversation.messages.order_by(Message.created_at.asc()).all()
                
                # 清空现有消息
                self.clear()
                
                for msg in messages:
                    if msg.role == 'user':
                        self.add_message(HumanMessage(content=msg.content))
                    elif msg.role == 'assistant':
                        self.add_message(AIMessage(content=msg.content))
                    elif msg.role == 'system':
                        self.add_message(SystemMessage(content=msg.content))
                        
                logger.info(f"从数据库加载了 {len(self._messages)} 条消息到 LangChain 历史")
        except Exception as e:
            logger.error(f"加载消息历史失败: {str(e)}")
            self.clear()
    
    def reload_from_database(self):
        """重新从数据库加载消息"""
        self._load_messages()

class CustomDeepSeekLLM(LLM):
    """自定义的 DeepSeek LLM 包装器，兼容 LangChain 0.3.26"""
    
    # 使用Pydantic字段定义
    model_name: str = Field(default="deepseek-chat", description="模型名称")
    temperature: float = Field(default=0.7, description="温度参数")
    
    def __init__(self, deepseek_service=None, **kwargs):
        super().__init__(**kwargs)
        # 使用私有属性存储服务实例
        self._deepseek_service = deepseek_service
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """调用 DeepSeek API"""
        try:
            if not self._deepseek_service:
                return "DeepSeek服务未初始化"
                
            messages = [{"role": "user", "content": prompt}]
            result = self._deepseek_service.chat_completion(messages, stream=False)
            
            if result['success']:
                return result['data']['choices'][0]['message']['content']
            else:
                logger.error(f"DeepSeek API 调用失败: {result.get('error')}")
                return "抱歉，AI 服务暂时不可用。"
        except Exception as e:
            logger.error(f"CustomDeepSeekLLM 调用异常: {str(e)}")
            return f"调用失败: {str(e)}"
    
    @property
    def _llm_type(self) -> str:
        """LLM类型标识"""
        return "deepseek"
    
    @property 
    def _identifying_params(self) -> Dict[str, Any]:
        """标识参数"""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
        }

class LangChainContextService:
    """LangChain 上下文管理服务"""
    
    def __init__(self, deepseek_service=None):
        from app.services.deepseek_service import DeepSeekService
        self.deepseek_service = deepseek_service or DeepSeekService()
        
        # 创建自定义 LLM
        self.llm = CustomDeepSeekLLM(deepseek_service=self.deepseek_service)
        
        # 配置参数
        self.max_token_limit = getattr(BaseConfig, 'LANGCHAIN_MAX_TOKEN_LIMIT', 8000)
        self.summary_rounds = getattr(BaseConfig, 'CONVERSATION_SUMMARY_ROUNDS', 10)
        
        # 消息历史存储
        self._session_histories: Dict[str, DatabaseChatMessageHistory] = {}
        
        logger.info("LangChain 上下文服务已初始化")
    
    def get_session_history(self, conversation_id: str) -> DatabaseChatMessageHistory:
        """获取会话历史（用于新版本API）"""
        if conversation_id not in self._session_histories:
            self._session_histories[conversation_id] = DatabaseChatMessageHistory(conversation_id)
        else:
            # 重新加载数据库中的消息
            self._session_histories[conversation_id].reload_from_database()
        return self._session_histories[conversation_id]
    
    def create_conversation_chain(self, conversation_id: str, 
                                 system_prompt: Optional[str] = None):
        """
        创建对话链（使用新版本API）
        
        Args:
            conversation_id: 对话ID
            system_prompt: 系统提示词
            
        Returns:
            LangChain 对话链
        """
        try:
            # 创建提示模板
            if system_prompt:
                template = f"""{system_prompt}

当前对话历史：
{{chat_history}}

用户: {{input}}
AI助手:"""
            else:
                template = """你是Agorix智能助手，来自现代雅典集市，基于DeepSeek-V3模型。你能够回答用户的问题，并基于提供的知识库内容给出准确的答案。请用中文回答。

当前对话历史：
{chat_history}

用户: {input}
AI助手:"""
            
            prompt = PromptTemplate(
                input_variables=["chat_history", "input"],
                template=template
            )
            
            # 使用新的Runnable语法替代已弃用的LLMChain
            chain = prompt | self.llm
            
            # 包装为支持消息历史的链
            chain_with_history = RunnableWithMessageHistory(
                chain,
                self.get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            
            logger.info(f"为对话 {conversation_id} 创建了 LangChain 对话链")
            return chain_with_history
            
        except Exception as e:
            logger.error(f"创建对话链失败: {str(e)}")
            raise
    
    def chat_with_langchain(self, conversation_id: str, user_message: str,
                           system_prompt: Optional[str] = None,
                           knowledge_context: Optional[str] = None) -> Dict[str, Any]:
        """
        使用 LangChain 进行对话
        
        Args:
            conversation_id: 对话ID
            user_message: 用户消息
            system_prompt: 系统提示词
            knowledge_context: 知识库上下文
            
        Returns:
            对话结果
        """
        try:
            # 如果有知识库上下文，将其加入系统提示词
            if knowledge_context and system_prompt:
                enhanced_prompt = f"{system_prompt}\n\n以下是相关的知识库内容，请基于这些内容回答用户问题：\n{knowledge_context}"
            elif knowledge_context:
                enhanced_prompt = f"你是Agorix智能助手。以下是相关的知识库内容，请基于这些内容回答用户问题：\n{knowledge_context}"
            else:
                enhanced_prompt = system_prompt
            
            # 创建对话链
            conversation_chain = self.create_conversation_chain(conversation_id, enhanced_prompt)
            
            # 执行对话 - 使用新版本API
            # RunnableWithMessageHistory会自动管理消息历史，无需手动添加
            config = {"configurable": {"session_id": conversation_id}}
            response = conversation_chain.invoke(
                {"input": user_message},
                config=config
            )
            
            # 提取响应文本
            ai_response = str(response)
            
            logger.info(f"LangChain 对话完成，对话ID: {conversation_id}, 响应长度: {len(ai_response)}")
            
            # 获取更新后的上下文信息
            context_info = self.get_conversation_context(conversation_id)
            
            result = {
                "success": True,
                "response": ai_response,
                "context_info": context_info,
                "conversation_id": conversation_id
            }
            
            logger.info(f"LangChain 对话完成，对话ID: {conversation_id}, 响应长度: {len(ai_response)}")
            return result
            
        except Exception as e:
            logger.error(f"LangChain 对话失败: {str(e)}")
            import traceback
            logger.error(f"LangChain 对话错误详情: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "conversation_id": conversation_id
            }
    
    def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        获取对话的上下文信息
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            包含上下文信息的字典
        """
        try:
            # 获取消息历史
            history = self.get_session_history(conversation_id)
            chat_history = history.messages
            
            # 格式化消息为字典列表
            formatted_messages = []
            for msg in chat_history:
                if isinstance(msg, HumanMessage):
                    formatted_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    formatted_messages.append({"role": "assistant", "content": msg.content})
                elif isinstance(msg, SystemMessage):
                    formatted_messages.append({"role": "system", "content": msg.content})
            
            context_info = {
                "conversation_id": conversation_id,
                "messages": formatted_messages,
                "message_count": len(formatted_messages),
                "summary": None,  # 新版本API中摘要处理方式不同
                "has_summary": False,
                "memory_type": "RunnableWithMessageHistory"
            }
            
            logger.info(f"获取对话 {conversation_id} 上下文: {len(formatted_messages)} 条消息")
            
            return context_info
            
        except Exception as e:
            logger.error(f"获取对话上下文失败: {str(e)}")
            return {
                "conversation_id": conversation_id,
                "messages": [],
                "message_count": 0,
                "summary": None,
                "has_summary": False,
                "error": str(e)
            }
    
    def get_conversation_summary(self, conversation_id: str) -> Optional[str]:
        """
        获取对话摘要
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话摘要，如果没有则返回None
        """
        try:
            history = self.get_session_history(conversation_id)
            messages = history.messages
            
            if len(messages) > 4:  # 至少2轮对话才生成摘要
                # 构建对话文本
                conversation_text = ""
                for msg in messages:
                    role = "用户" if isinstance(msg, HumanMessage) else "AI助手"
                    conversation_text += f"{role}: {msg.content}\n\n"
                
                # 生成摘要
                summary_prompt = f"""请对以下对话进行简洁的总结，突出关键信息和讨论要点：

{conversation_text}

总结（100-200字）："""

                result = self.deepseek_service.chat_completion([
                    {"role": "user", "content": summary_prompt}
                ], stream=False)
                
                if result['success']:
                    summary = result['data']['choices'][0]['message']['content']
                    logger.info(f"为对话 {conversation_id} 生成了手动摘要")
                    return summary
            
            return None
            
        except Exception as e:
            logger.error(f"获取对话摘要失败: {str(e)}")
            return None
    
    def analyze_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        分析对话上下文
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            上下文分析结果
        """
        try:
            context_info = self.get_conversation_context(conversation_id)
            messages = context_info.get("messages", [])
            
            # 统计信息
            user_msg_count = len([m for m in messages if m["role"] == "user"])
            ai_msg_count = len([m for m in messages if m["role"] == "assistant"])
            
            # 计算平均消息长度
            total_length = sum(len(m["content"]) for m in messages)
            avg_length = total_length / len(messages) if messages else 0
            
            # 获取最近的话题
            recent_topics = []
            if len(messages) >= 2:
                recent_messages = messages[-4:]  # 最近2轮对话
                for msg in recent_messages:
                    if msg["role"] == "user" and len(msg["content"]) > 10:
                        # 提取关键词作为话题
                        content = msg["content"][:100]
                        recent_topics.append(content)
            
            analysis = {
                "conversation_id": conversation_id,
                "total_messages": len(messages),
                "user_messages": user_msg_count,
                "ai_messages": ai_msg_count,
                "avg_message_length": round(avg_length, 2),
                "has_summary": context_info.get("has_summary", False),
                "summary": context_info.get("summary"),
                "recent_topics": recent_topics,
                "memory_efficiency": self._calculate_memory_efficiency(context_info),
                "analysis_time": datetime.now().isoformat()
            }
            
            logger.info(f"完成对话 {conversation_id} 的上下文分析")
            return analysis
            
        except Exception as e:
            logger.error(f"分析对话上下文失败: {str(e)}")
            return {"error": str(e), "conversation_id": conversation_id}
    
    def _calculate_memory_efficiency(self, context_info: Dict) -> Dict[str, Any]:
        """计算记忆效率指标"""
        try:
            message_count = context_info.get("message_count", 0)
            has_summary = context_info.get("has_summary", False)
            
            # 简单的效率评估
            if has_summary and message_count > 10:
                efficiency = "高效"
                reason = "使用了摘要机制，节省了上下文空间"
            elif message_count <= 10:
                efficiency = "正常"
                reason = "消息数量适中，无需优化"
            else:
                efficiency = "待优化"
                reason = "消息过多且无摘要，建议开启摘要机制"
            
            return {
                "level": efficiency,
                "reason": reason,
                "message_count": message_count,
                "has_summary": has_summary
            }
        except Exception:
            return {"level": "未知", "reason": "计算失败"} 