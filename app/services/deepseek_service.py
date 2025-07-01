"""
DeepSeek API 服务
"""

import logging
from typing import Dict, List, Optional, Any, Iterator
from openai import OpenAI
from config.settings import Config

logger = logging.getLogger(__name__)

class DeepSeekService:
    """DeepSeek API 服务类"""
    
    def __init__(self):
        self.api_key = Config.DEEPSEEK_API_KEY
        self.api_base = Config.DEEPSEEK_API_BASE
        self.model = Config.DEEPSEEK_MODEL
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       model: Optional[str] = None,
                       temperature: float = 0.7,
                       max_tokens: int = 2000,
                       stream: bool = False) -> Dict[str, Any]:
        """
        调用DeepSeek聊天完成API
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "Hello"}]
            model: 模型名称，默认使用配置的模型
            temperature: 温度参数，控制随机性
            max_tokens: 最大token数
            stream: 是否使用流式响应
            
        Returns:
            API响应结果
        """
        try:
            logger.info("\n================ [CHAT][MESSAGES] 发送给大模型的messages ================\n%s\n============================================================", messages)
            logger.info(f"[CHAT][MODEL] 使用模型: {model or self.model}, 流式: {stream}")
            response = self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                logger.info("[CHAT][STREAM] DeepSeek API流式请求启动")
                return {
                    'success': True,
                    'stream': response
                }
            else:
                # 提取模型返回的内容
                ai_content = response.choices[0].message.content
                logger.info("\n================ [CHAT][RESPONSE] 非流式API完整返回内容 ================\n%s\n============================================================", ai_content)
                logger.info("DeepSeek API请求成功")
                
                # 转换为字典格式以保持接口一致性
                result = {
                    "choices": [
                        {
                            "message": {
                                "role": response.choices[0].message.role,
                                "content": ai_content
                            },
                            "finish_reason": response.choices[0].finish_reason
                        }
                    ],
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    } if response.usage else {},
                    "model": response.model,
                    "id": response.id
                }
                
                return {
                    'success': True,
                    'data': result
                }
            
        except Exception as e:
            logger.error(f"DeepSeek API调用异常: {str(e)}")
            return {
                'success': False,
                'error': f"API调用失败: {str(e)}"
            }
    
    def chat_completion_stream(self, 
                              messages: List[Dict[str, str]], 
                              model: Optional[str] = None,
                              temperature: float = 0.7,
                              max_tokens: int = 2000) -> Iterator[str]:
        """
        流式聊天完成API
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            流式响应的文本块
        """
        full_response = ""  # 收集完整响应内容
        
        try:
            logger.info("[CHAT][STREAM_START] 开始流式API调用")
            response = self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # 流式响应完成后，记录完整内容
            logger.info("\n================ [CHAT][STREAM_RESPONSE] 流式API完整返回内容 ================\n%s\n============================================================", full_response)
                    
        except Exception as e:
            logger.error(f"流式API调用异常: {str(e)}")
            yield f"[错误] {str(e)}"
    
    def simple_chat(self, user_message: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        简单的聊天接口
        
        Args:
            user_message: 用户消息
            system_prompt: 系统提示词（可选）
            
        Returns:
            包含成功状态和响应内容的字典
        """
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user", 
            "content": user_message
        })
        
        result = self.chat_completion(messages, stream=False)
        
        if result['success']:
            try:
                response_content = result['data']['choices'][0]['message']['content']
                return {
                    'success': True,
                    'response': response_content,
                    'usage': result['data'].get('usage', {})
                }
            except (KeyError, IndexError) as e:
                logger.error(f"解析API响应内容失败: {str(e)}")
                return {
                    'success': False,
                    'error': f"响应格式错误: {str(e)}"
                }
        else:
            return result
    
    def chat_with_context(self, 
                         user_message: str, 
                         conversation_history: List[Dict[str, str]] = None,
                         knowledge_context: str = None,
                         system_prompt: str = None,
                         stream: bool = True) -> Dict[str, Any]:
        """
        带上下文的聊天接口 - 按照DeepSeek多轮对话文档实现
        
        Args:
            user_message: 用户消息
            conversation_history: 对话历史（完整的历史记录）
            knowledge_context: 知识库上下文
            system_prompt: 系统提示词
            stream: 是否使用流式响应
            
        Returns:
            包含成功状态和响应内容的字典
        """
        # 按照DeepSeek文档要求构建消息列表
        messages = []
        
        # 1. 构建系统提示词（如果有）
        if not system_prompt:
            system_prompt = "你是SuperRAG智能助手，基于DeepSeek-V3模型。你能够回答用户的问题，并基于提供的知识库内容给出准确的答案。请用中文回答。"
        
        if knowledge_context:
            system_prompt += f"\n\n以下是相关的知识库内容，请基于这些内容回答用户问题：\n{knowledge_context}"
        
        logger.info(f"[CHAT][INPUT] 用户输入: {user_message}")
        logger.info(f"[CHAT][PROMPT] 系统提示词: {system_prompt}")
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # 2. 添加完整的对话历史（按照DeepSeek文档要求）
        if conversation_history:
            # 直接添加所有历史消息，保持时间顺序
            messages.extend(conversation_history)
        
        # 3. 添加当前用户消息
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        logger.info("[CHAT][MESSAGES] 完整messages: %s", messages)
        
        return self.chat_completion(messages, stream=stream)
    
    def chat_stream(self, 
                   user_message: str, 
                   conversation_history: List[Dict[str, str]] = None,
                   knowledge_context: str = None,
                   system_prompt: str = None) -> Iterator[str]:
        """
        流式聊天接口 - 按照DeepSeek多轮对话文档实现
        
        Args:
            user_message: 用户消息
            conversation_history: 对话历史（完整的历史记录）
            knowledge_context: 知识库上下文
            system_prompt: 系统提示词
            
        Yields:
            流式响应的文本块
        """
        # 按照DeepSeek文档要求构建消息列表
        messages = []
        
        # 1. 构建系统提示词
        if not system_prompt:
            system_prompt = "你是SuperRAG智能助手，基于DeepSeek-V3模型。你能够回答用户的问题，并基于提供的知识库内容给出准确的答案。请用中文回答。"
        
        if knowledge_context:
            system_prompt += f"\n\n以下是相关的知识库内容，请基于这些内容回答用户问题：\n{knowledge_context}"
        
        logger.info(f"[CHAT][INPUT] 用户输入: {user_message}")
        logger.info(f"[CHAT][PROMPT] 系统提示词: {system_prompt}")
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # 2. 添加完整的对话历史
        if conversation_history:
            messages.extend(conversation_history)
        
        # 3. 添加当前用户消息
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        logger.info("[CHAT][MESSAGES] 完整messages: %s", messages)
        
        # 使用流式API
        yield from self.chat_completion_stream(messages)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试API连接
        
        Returns:
            测试结果
        """
        test_message = "你好，请简单回复确认连接正常。"
        result = self.simple_chat(test_message)
        
        if result['success']:
            return {
                'success': True,
                'message': 'DeepSeek API连接正常',
                'response': result['response']
            }
        else:
            return {
                'success': False,
                'message': 'DeepSeek API连接失败',
                'error': result['error']
            } 