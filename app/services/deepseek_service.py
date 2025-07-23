"""
DeepSeek API 服务
"""

import logging
from typing import Dict, List, Optional, Any, Iterator
from openai import OpenAI
from config.settings import BaseConfig

logger = logging.getLogger(__name__)

class DeepSeekService:
    """DeepSeek API 服务类"""
    
    def __init__(self):
        self.api_key = BaseConfig.DEEPSEEK_API_KEY
        self.api_base = BaseConfig.DEEPSEEK_API_BASE
        self.model = BaseConfig.DEEPSEEK_MODEL
        
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
                stream=stream,
                response_format={'type': 'json_object'} if not stream else None
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
            system_prompt = "你是Agorix智能助手，来自现代雅典集市，基于DeepSeek-V3模型。你能够回答用户的问题，并基于提供的知识库内容给出准确的答案。请用中文回答。"
        
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
            system_prompt = "你是Agorix智能助手，来自现代雅典集市，基于DeepSeek-V3模型。你能够回答用户的问题，并基于提供的知识库内容给出准确的答案。请用中文回答。"
        
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
    
    def chat_with_conversation_config(self,
                                     user_message: str,
                                     conversation_config: Dict[str, Any],
                                     conversation_history: List[Dict[str, str]] = None,
                                     knowledge_context: str = None,
                                     stream: bool = True) -> Dict[str, Any]:
        """
        使用对话配置参数进行聊天 - V0.3.0 新功能
        
        Args:
            user_message: 用户消息
            conversation_config: 对话配置 (model_name, temperature, max_tokens, system_prompt)
            conversation_history: 对话历史
            knowledge_context: 知识库上下文
            stream: 是否使用流式响应
            
        Returns:
            包含成功状态和响应内容的字典
        """
        try:
            # 从配置中获取参数
            model_name = conversation_config.get('model_name', 'deepseek-chat')
            temperature = conversation_config.get('temperature', 1.0)
            max_tokens = conversation_config.get('max_tokens', 4000)
            system_prompt = conversation_config.get('system_prompt', '')
            
            # 构建消息列表
            messages = []
            
            # 1. 构建系统提示词
            if not system_prompt:
                if model_name == 'deepseek-reasoner':
                    system_prompt = "你是Agorix智能助手，来自现代雅典集市，基于DeepSeek-R1模型。你具有深度思考能力，能够进行复杂推理和问题分析。请用中文回答。"
                else:
                    system_prompt = "你是Agorix智能助手，来自现代雅典集市，基于DeepSeek-V3模型。你能够回答用户的问题，并基于提供的知识库内容给出准确的答案。请用中文回答。"
            
            if knowledge_context:
                system_prompt += f"\n\n以下是相关的知识库内容，请基于这些内容回答用户问题：\n{knowledge_context}"
            
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
            # 2. 添加对话历史
            if conversation_history:
                messages.extend(conversation_history)
            
            # 3. 添加当前用户消息
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            logger.info(f"[CHAT][CONFIG] 使用配置 - 模型: {model_name}, 温度: {temperature}, 最大Token: {max_tokens}")
            
            # 调用API
            result = self.chat_completion(
                messages=messages,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            # 针对 DeepSeek-R1 模型处理思考链
            if result['success'] and model_name == 'deepseek-reasoner':
                result = self._process_deepseek_r1_response(result)
            
            return result
            
        except Exception as e:
            logger.error(f"使用对话配置聊天异常: {str(e)}")
            return {
                'success': False,
                'error': f"配置聊天失败: {str(e)}"
            }
    
    def _process_deepseek_r1_response(self, api_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 DeepSeek-R1 模型的响应，分离思考链和最终答案
        
        Args:
            api_result: 原始API结果
            
        Returns:
            处理后的结果，包含 thinking_process 和 final_answer
        """
        try:
            if not api_result.get('success'):
                return api_result
            
            # V0.3.0 修复：支持流式响应的思考链处理
            if 'stream' in api_result:
                # 流式响应，直接返回，由调用方处理完整内容后再分离
                return api_result
            
            # V0.3.1 修复：正确处理DeepSeek-R1的reasoning_content字段
            choice = api_result['data']['choices'][0]
            message = choice['message']
            content = message['content']
            
            # 检查是否有reasoning_content字段（DeepSeek-R1特有）
            reasoning_content = message.get('reasoning_content', '')
            
            if reasoning_content and reasoning_content.strip():
                # DeepSeek-R1 有思考过程
                api_result['thinking_process'] = reasoning_content
                api_result['has_thinking'] = True
                
                logger.info(f"[R1][THINKING] 发现思考过程: {len(reasoning_content)} 字符")
                logger.info(f"[R1][ANSWER] 最终答案: {len(content)} 字符")
            else:
                # 检查是否包含思考标记（备用方案）
                thinking_markers = ['<think>', '</think>', '<thinking>', '</thinking>']
                has_thinking_markers = any(marker in content for marker in thinking_markers)
                
                if has_thinking_markers:
                    # 使用标记分离的备用方案
                    import re
                    
                    # 提取 <think>...</think> 或 <thinking>...</thinking> 内容
                    think_pattern = r'<think>(.*?)</think>|<thinking>(.*?)</thinking>'
                    think_matches = re.findall(think_pattern, content, re.DOTALL)
                    
                    if think_matches:
                        # 合并所有思考内容
                        thinking_parts = []
                        for match in think_matches:
                            thinking_parts.extend([part for part in match if part.strip()])
                        thinking_process = '\n\n'.join(thinking_parts).strip()
                        
                        # 移除思考标记，保留最终答案
                        final_answer = re.sub(r'<think>.*?</think>|<thinking>.*?</thinking>', '', content, flags=re.DOTALL).strip()
                        
                        # 更新API结果
                        api_result['data']['choices'][0]['message']['content'] = final_answer
                        api_result['thinking_process'] = thinking_process
                        api_result['has_thinking'] = True
                        
                        logger.info(f"[R1][THINKING] 备用方案提取思考过程: {len(thinking_process)} 字符")
                        logger.info(f"[R1][ANSWER] 备用方案最终答案: {len(final_answer)} 字符")
                    else:
                        api_result['has_thinking'] = False
                else:
                    api_result['has_thinking'] = False
            
            return api_result
            
        except Exception as e:
            logger.error(f"处理 DeepSeek-R1 响应异常: {str(e)}")
            # 返回原始结果，不影响正常功能
            return api_result
    
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