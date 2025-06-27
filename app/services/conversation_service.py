# -*- coding: utf-8 -*-
"""
对话管理服务
包含多轮对话的上下文管理、总结等功能
现已集成 LangChain 提供更强大的上下文管理
"""

import logging
from typing import List, Dict, Optional, Tuple
from app.models import Conversation, Message
from app.services.deepseek_service import DeepSeekService
from app.prompts.conversation_prompts import ConversationPrompts
from app.prompts.system_prompts import SystemPrompts
from config.settings import BaseConfig

logger = logging.getLogger(__name__)

class ConversationService:
    """对话管理服务 - 集成LangChain上下文管理"""
    
    def __init__(self, deepseek_service: DeepSeekService = None):
        self.deepseek_service = deepseek_service or DeepSeekService()
        self.summary_rounds = BaseConfig.CONVERSATION_SUMMARY_ROUNDS
        self.max_context_messages = BaseConfig.MAX_CONTEXT_MESSAGES
        
        # LangChain 集成
        self.langchain_enabled = BaseConfig.LANGCHAIN_ENABLED
        if self.langchain_enabled:
            try:
                from app.services.langchain_service import LangChainContextService
                self.langchain_service = LangChainContextService(self.deepseek_service)
                logger.info("LangChain 上下文管理已启用")
            except ImportError as e:
                logger.warning(f"LangChain 依赖未安装，将使用传统上下文管理: {e}")
                self.langchain_enabled = False
                self.langchain_service = None
        else:
            self.langchain_service = None
            logger.info("LangChain 上下文管理已禁用，使用传统管理方式")
    
    def should_summarize_context(self, conversation: Conversation) -> bool:
        """
        判断是否需要进行上下文总结
        
        Args:
            conversation: 对话对象
            
        Returns:
            是否需要总结
        """
        if not conversation:
            return False
        
        # 计算当前对话的轮数（用户消息数）
        user_message_count = conversation.messages.filter_by(role='user').count()
        
        # 检查是否达到总结轮数
        return user_message_count > 0 and user_message_count % self.summary_rounds == 0
    
    def format_conversation_history(self, messages: List[Message]) -> str:
        """
        格式化对话历史为可读文本
        
        Args:
            messages: 消息列表
            
        Returns:
            格式化后的对话历史
        """
        formatted_history = []
        
        for msg in messages:
            role_name = "用户" if msg.role == "user" else "AI助手"
            formatted_history.append(f"{role_name}: {msg.content}")
        
        return "\n\n".join(formatted_history)
    
    async def summarize_conversation_context(self, conversation: Conversation) -> Optional[str]:
        """
        总结对话上下文
        
        Args:
            conversation: 对话对象
            
        Returns:
            上下文总结，如果失败返回None
        """
        try:
            # 如果启用了 LangChain，优先使用 LangChain 的摘要功能
            if self.langchain_enabled and self.langchain_service:
                summary = self.langchain_service.get_conversation_summary(conversation.id)
                if summary:
                    logger.info(f"使用 LangChain 获取对话 {conversation.id} 的摘要")
                    return summary
            
            # 回退到传统摘要方法
            # 获取需要总结的消息（最近的几轮对话）
            messages_to_summarize = conversation.messages.order_by(
                Message.created_at.asc()
            ).limit(self.summary_rounds * 2).all()  # 每轮包含用户和AI消息
            
            if not messages_to_summarize:
                logger.warning(f"对话 {conversation.id} 没有足够的消息进行总结")
                return None
            
            # 格式化对话历史
            conversation_text = self.format_conversation_history(messages_to_summarize)
            
            # 生成总结提示词
            summary_prompt = ConversationPrompts.get_summarization_prompt(conversation_text)
            logger.info("\n================ [SUMMARY][PROMPT] 总结提示词 ================\n%s\n============================================================", summary_prompt)
            
            # 调用AI进行总结
            result = self.deepseek_service.chat_completion([
                {"role": "user", "content": summary_prompt}
            ], stream=False)
            if result['success']:
                summary = result['data']['choices'][0]['message']['content']
                logger.info("\n================ [SUMMARY][COMPLETE] 总结完整内容 ================\n%s\n============================================================", summary)
                logger.info(f"对话 {conversation.id} 上下文总结完成，长度: {len(summary)}")
                return summary
            else:
                logger.error(f"对话总结API调用失败: {result.get('error', '未知错误')}")
                return None
                
        except Exception as e:
            logger.error(f"总结对话上下文失败: {str(e)}")
            return None
    
    def get_optimized_context(self, conversation: Conversation) -> Tuple[List[Dict], Optional[str]]:
        """
        获取优化后的对话上下文
        支持 LangChain 和传统两种方式
        
        Args:
            conversation: 对话对象
            
        Returns:
            元组 (optimized_messages, context_summary)
            - optimized_messages: 优化后的消息列表
            - context_summary: 上下文总结（如果有）
        """
        if not conversation:
            return [], None
        
        # 如果启用了 LangChain，使用 LangChain 的上下文管理
        if self.langchain_enabled and self.langchain_service:
            try:
                context_info = self.langchain_service.get_conversation_context(conversation.id)
                
                optimized_messages = context_info.get("messages", [])
                context_summary = context_info.get("summary")
                
                logger.info(f"使用 LangChain 获取优化上下文: {len(optimized_messages)} 条消息，"
                           f"摘要: {'有' if context_summary else '无'}")
                
                return optimized_messages, context_summary
                
            except Exception as e:
                logger.warning(f"LangChain 上下文获取失败，回退到传统方式: {str(e)}")
        
        # 传统上下文管理方式
        # 获取所有消息
        all_messages = conversation.messages.order_by(Message.created_at.asc()).all()
        
        # 检查是否需要使用总结
        if len(all_messages) > self.max_context_messages:
            # 获取最新的消息
            recent_messages = all_messages[-self.summary_rounds * 2:]  # 最近几轮的原始消息
            older_messages = all_messages[:-self.summary_rounds * 2]   # 需要总结的较早消息
            
            if older_messages:
                # 生成较早消息的总结
                older_text = self.format_conversation_history(older_messages)
                summary_prompt = ConversationPrompts.get_summarization_prompt(older_text)
                logger.info("\n================ [SUMMARY][PROMPT] 总结提示词 ================\n%s\n============================================================", summary_prompt)
                
                try:
                    result = self.deepseek_service.chat_completion([
                        {"role": "user", "content": summary_prompt}
                    ], stream=False)
                    if result['success']:
                        context_summary = result['data']['choices'][0]['message']['content']
                        logger.info("\n================ [SUMMARY][COMPLETE] 总结完整内容 ================\n%s\n============================================================", context_summary)
                        
                        # 构建优化后的消息列表（总结 + 最近消息）
                        optimized_messages = []
                        for msg in recent_messages:
                            optimized_messages.append({
                                'role': msg.role,
                                'content': msg.content
                            })
                        
                        logger.info(f"使用传统方式上下文总结，原消息数: {len(all_messages)}, 优化后: {len(optimized_messages)}")
                        return optimized_messages, context_summary
                        
                except Exception as e:
                    logger.error(f"生成上下文总结失败: {str(e)}")
        
        # 如果不需要总结或总结失败，返回最近的消息
        recent_messages = all_messages[-self.max_context_messages:]
        optimized_messages = []
        for msg in recent_messages:
            optimized_messages.append({
                'role': msg.role,
                'content': msg.content
            })
        
        return optimized_messages, None
    
    def get_system_prompt(self, context_summary: Optional[str] = None, 
                         knowledge_context: Optional[str] = None) -> str:
        """
        获取系统提示词
        
        Args:
            context_summary: 上下文总结
            knowledge_context: 知识库上下文
            
        Returns:
            系统提示词
        """
        if context_summary:
            # 使用基于总结的系统提示词
            system_prompt = ConversationPrompts.get_summarized_system_prompt(context_summary)
        else:
            # 使用基础系统提示词
            if knowledge_context:
                system_prompt = SystemPrompts.get_prompt('knowledge')
            else:
                system_prompt = SystemPrompts.get_prompt('base')
        
        # 如果有知识库上下文，添加到系统提示词中
        if knowledge_context:
            system_prompt += f"\n\n以下是相关的知识库内容，请基于这些内容回答用户问题：\n{knowledge_context}"
        
        return system_prompt
    
    def count_user_messages(self, conversation: Conversation) -> int:
        """
        计算对话中的用户消息数量
        
        Args:
            conversation: 对话对象
            
        Returns:
            用户消息数量
        """
        if not conversation:
            return 0
        return conversation.messages.filter_by(role='user').count()
    
    def log_context_optimization(self, conversation_id: str, original_count: int, 
                                optimized_count: int, has_summary: bool):
        """
        记录上下文优化信息
        
        Args:
            conversation_id: 对话ID
            original_count: 原始消息数
            optimized_count: 优化后消息数
            has_summary: 是否使用了总结
        """
        method = "LangChain" if self.langchain_enabled else "传统方式"
        logger.info(
            f"对话 {conversation_id} 上下文优化 ({method}): "
            f"原始消息数={original_count}, 优化后={optimized_count}, "
            f"使用总结={'是' if has_summary else '否'}"
        )
    
    def get_context_analysis(self, conversation_id: str) -> Dict:
        """
        获取对话上下文分析
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            上下文分析结果
        """
        if self.langchain_enabled and self.langchain_service:
            try:
                return self.langchain_service.analyze_conversation_context(conversation_id)
            except Exception as e:
                logger.warning(f"LangChain 上下文分析失败: {str(e)}")
        
        # 回退到基础分析
        conversation = Conversation.query.filter_by(id=conversation_id).first()
        if not conversation:
            return {"error": "对话不存在", "conversation_id": conversation_id}
        
        messages = conversation.messages.all()
        user_msg_count = len([m for m in messages if m.role == 'user'])
        ai_msg_count = len([m for m in messages if m.role == 'assistant'])
        
        return {
            "conversation_id": conversation_id,
            "total_messages": len(messages),
            "user_messages": user_msg_count,
            "ai_messages": ai_msg_count,
            "langchain_enabled": self.langchain_enabled,
            "analysis_method": "基础分析"
        } 