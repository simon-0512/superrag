"""
AI思维导图服务模块
处理思维导图的AI扩展、说明、优化等功能
"""

import json
import logging
from typing import Dict, List, Optional, Any
from app.services.deepseek_service import DeepSeekService
from app.prompts.mindmap_prompts import (
    get_expand_prompt, 
    get_explain_prompt, 
    get_theme_prompt,
    format_context_info
)

logger = logging.getLogger(__name__)


class AIMindmapService:
    """AI思维导图服务类"""
    
    def __init__(self):
        self.deepseek_service = DeepSeekService()
    
    def expand_node(
        self,
        node_text: str,
        context: Optional[Dict] = None,
        mode: str = "creative",
        count: int = 4,
        include_parent: bool = True,
        include_siblings: bool = False
    ) -> Dict[str, Any]:
        """
        AI智能扩展节点
        
        Args:
            node_text: 当前节点文本
            context: 上下文信息 (父节点、同级节点等)
            mode: 扩展模式 (creative, deep_analysis, practical, academic)
            count: 生成节点数量
            include_parent: 是否包含父节点上下文
            include_siblings: 是否包含同级节点上下文
            
        Returns:
            包含扩展节点的字典
        """
        try:
            # 格式化上下文信息
            context_info = format_context_info(context, include_parent, include_siblings)
            
            # 构建提示词
            prompt = get_expand_prompt(mode, node_text, context_info, count)
            
            # 📝 调试信息：记录发送给AI的完整提示词
            logger.info("\n" + "="*80)
            logger.info("🧠 [AI扩展调试] 开始节点扩展")
            logger.info("="*80)
            logger.info(f"📄 节点文本: {node_text}")
            logger.info(f"🎯 扩展模式: {mode}")
            logger.info(f"🔢 生成数量: {count}")
            logger.info(f"📋 上下文信息: {context}")
            logger.info("📝 发送给DeepSeek的完整提示词:")
            logger.info("-" * 60)
            logger.info(prompt)
            logger.info("-" * 60)
            
            # 调用AI服务 - 确保使用deepseek-v3模型，要求JSON格式输出
            response = self.deepseek_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你需要返回标准的JSON格式响应。"},
                    {"role": "user", "content": prompt}
                ],
                model="deepseek-chat",  # 明确指定使用deepseek-v3
                temperature=0.7,
                max_tokens=1000,
                stream=False
            )
            
            # 📝 调试信息：记录AI的完整响应
            logger.info("🤖 DeepSeek API 完整响应:")
            logger.info(f"✅ 请求状态: {response.get('success')}")
            if response.get('success'):
                ai_content = response['data']['choices'][0]['message']['content']
                model_used = response['data'].get('model', '未知模型')
                usage_info = response['data'].get('usage', {})
                
                logger.info(f"🔧 使用模型: {model_used}")
                logger.info(f"📊 Token使用: {usage_info}")
                logger.info("📄 AI原始回复内容:")
                logger.info("-" * 60)
                logger.info(ai_content)
                logger.info("-" * 60)
                
                # 解析AI响应
                result = self._parse_expand_response(ai_content)
                logger.info(f"📋 解析结果: 成功={result.get('success')}, 节点数={len(result.get('nodes', []))}")
                
                # 添加调试信息到返回结果
                result['debug_info'] = {
                    'prompt': prompt,
                    'raw_response': ai_content,
                    'model_used': model_used,
                    'usage': usage_info,
                    'parse_success': result.get('success', False)
                }
            else:
                logger.error(f"❌ API调用失败: {response.get('error')}")
                result = {
                    "success": False,
                    "error": response.get('error', '未知错误'),
                    "nodes": [],
                    'debug_info': {
                        'prompt': prompt,
                        'api_error': response.get('error'),
                        'raw_response': str(response)
                    }
                }
            
            logger.info("="*80)
            logger.info(f"🎯 AI节点扩展完成: {node_text} -> {len(result.get('nodes', []))} 个节点")
            logger.info("="*80 + "\n")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ AI节点扩展异常: {str(e)}")
            return {
                "success": False,
                "error": f"AI扩展失败: {str(e)}",
                "nodes": [],
                'debug_info': {
                    'exception': str(e)
                }
            }
    
    def explain_node(
        self,
        node_text: str,
        context: Optional[Dict] = None,
        explanation_type: str = "detailed"
    ) -> Dict[str, Any]:
        """
        AI智能说明节点
        
        Args:
            node_text: 节点文本
            context: 上下文信息
            explanation_type: 说明类型 (summary, detailed, examples, academic)
            
        Returns:
            包含说明内容的字典
        """
        try:
            # 格式化上下文信息
            context_info = format_context_info(context, True, False)
            
            # 构建提示词
            prompt = get_explain_prompt(explanation_type, node_text, context_info)
            
            # 📝 调试信息：记录发送给AI的完整提示词
            logger.info("\n" + "="*80)
            logger.info("💡 [AI说明调试] 开始节点说明")
            logger.info("="*80)
            logger.info(f"📄 节点文本: {node_text}")
            logger.info(f"🎯 说明类型: {explanation_type}")
            logger.info(f"📋 上下文信息: {context}")
            logger.info("📝 发送给DeepSeek的完整提示词:")
            logger.info("-" * 60)
            logger.info(prompt)
            logger.info("-" * 60)
            
            # 调用AI服务 - 确保使用deepseek-v3模型，要求JSON格式输出
            response = self.deepseek_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你需要返回标准的JSON格式响应。"},
                    {"role": "user", "content": prompt}
                ],
                model="deepseek-chat",  # 明确指定使用deepseek-v3
                temperature=0.5,
                max_tokens=800,
                stream=False
            )
            
            # 📝 调试信息：记录AI的完整响应
            logger.info("🤖 DeepSeek API 完整响应:")
            logger.info(f"✅ 请求状态: {response.get('success')}")
            
            # 解析AI响应
            if response.get('success'):
                ai_content = response['data']['choices'][0]['message']['content']
                model_used = response['data'].get('model', '未知模型')
                usage_info = response['data'].get('usage', {})
                
                logger.info(f"🔧 使用模型: {model_used}")
                logger.info(f"📊 Token使用: {usage_info}")
                logger.info("📄 AI原始回复内容:")
                logger.info("-" * 60)
                logger.info(ai_content)
                logger.info("-" * 60)
                
                result = self._parse_explain_response(ai_content)
                logger.info(f"📋 解析结果: 成功={result.get('success')}")
                
                # 添加调试信息到返回结果
                result['debug_info'] = {
                    'prompt': prompt,
                    'raw_response': ai_content,
                    'model_used': model_used,
                    'usage': usage_info,
                    'parse_success': result.get('success', False)
                }
            else:
                logger.error(f"❌ API调用失败: {response.get('error')}")
                result = {
                    "success": False,
                    "error": response.get('error', '未知错误'),
                    "explanation": "",
                    'debug_info': {
                        'prompt': prompt,
                        'api_error': response.get('error'),
                        'raw_response': str(response)
                    }
                }
            
            logger.info("="*80)
            logger.info(f"🎯 AI节点说明完成: {node_text}")
            logger.info("="*80 + "\n")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ AI节点说明异常: {str(e)}")
            return {
                "success": False,
                "error": f"AI说明失败: {str(e)}",
                "explanation": "",
                'debug_info': {
                    'exception': str(e)
                }
            }
    
    def generate_theme_mindmap(
        self,
        theme: str,
        framework: str = "default",
        depth: int = 3
    ) -> Dict[str, Any]:
        """
        AI生成主题思维导图
        
        Args:
            theme: 主题关键词
            framework: 思维框架 (default, swot, 5w1h, pyramid)
            depth: 思维导图深度
            
        Returns:
            包含完整思维导图结构的字典
        """
        try:
            # 构建提示词
            prompt = get_theme_prompt(framework, theme, depth)
            
            # 调用AI服务 - 要求JSON格式输出
            response = self.deepseek_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你需要返回标准的JSON格式响应。"},
                    {"role": "user", "content": prompt}
                ],
                model="deepseek-chat",  # 明确指定使用deepseek-v3
                temperature=0.6,
                max_tokens=1500,
                stream=False
            )
            
            # 解析AI响应
            if response.get('success'):
                ai_content = response['data']['choices'][0]['message']['content']
                result = self._parse_theme_response(ai_content)
            else:
                result = {
                    "success": False,
                    "error": response.get('error', '未知错误'),
                    "mindmap": {}
                }
            
            logger.info(f"AI主题生成成功: {theme}")
            return result
            
        except Exception as e:
            logger.error(f"AI主题生成失败: {str(e)}")
            return {
                "success": False,
                "error": f"AI主题生成失败: {str(e)}",
                "mindmap": {}
            }
    

    
    def _parse_expand_response(self, response: str) -> Dict[str, Any]:
        """解析扩展响应"""
        logger.info(f"🔍 [解析调试] 开始解析AI响应，原始长度: {len(response)}")
        
        try:
            # 尝试直接解析JSON
            result = json.loads(response)
            logger.info(f"✅ [解析调试] 直接JSON解析成功，类型: {type(result)}")
            
            if isinstance(result, dict):
                # 检查是否有nodes字段
                if "nodes" in result:
                    logger.info(f"✅ [解析调试] 找到nodes字段，包含 {len(result['nodes'])} 个节点")
                    return {
                        "success": True,
                        "nodes": result["nodes"],
                        "layout_suggestion": result.get("layout_suggestion", "radial")
                    }
                # 如果有success字段但为False
                elif result.get("success") == False:
                    logger.warning(f"⚠️ [解析调试] AI返回失败状态: {result.get('error', '未知错误')}")
                    return result
                else:
                    logger.warning(f"⚠️ [解析调试] JSON解析成功但缺少nodes字段，键: {list(result.keys())}")
            else:
                logger.warning(f"⚠️ [解析调试] JSON解析结果不是字典类型: {type(result)}")
                
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ [解析调试] 直接JSON解析失败: {str(e)}")
        
        # 如果直接解析失败，尝试提取JSON部分
        try:
            # 查找JSON块
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                logger.info(f"🔍 [解析调试] 提取JSON片段，长度: {len(json_str)}")
                logger.info(f"📄 [解析调试] JSON片段内容: {json_str[:200]}...")
                
                result = json.loads(json_str)
                logger.info(f"✅ [解析调试] JSON片段解析成功")
                
                if isinstance(result, dict) and "nodes" in result:
                    logger.info(f"✅ [解析调试] 片段包含nodes字段，节点数: {len(result['nodes'])}")
                    return {
                        "success": True,
                        "nodes": result["nodes"],
                        "layout_suggestion": result.get("layout_suggestion", "radial")
                    }
                    
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ [解析调试] JSON片段解析也失败: {str(e)}")
        
        # 如果还是解析失败，尝试智能提取节点信息
        try:
            # 查找类似节点的文本模式
            import re
            
            # 尝试匹配"节点:"或"- "开头的行
            node_patterns = [
                r"(?:节点\d*[:：]\s*|[\-\*]\s+)(.+)",
                r"^\d+\.\s*(.+)",
                r"^[\-\*•]\s*(.+)"
            ]
            
            extracted_nodes = []
            for pattern in node_patterns:
                matches = re.findall(pattern, response, re.MULTILINE)
                if matches:
                    extracted_nodes = [match.strip() for match in matches if match.strip()]
                    break
            
            if extracted_nodes:
                logger.info(f"🛠️ [解析调试] 智能提取成功，找到 {len(extracted_nodes)} 个节点")
                result_nodes = []
                for i, text in enumerate(extracted_nodes[:6]):  # 最多6个节点
                    result_nodes.append({
                        "text": text,
                        "type": "concept",
                        "priority": "medium",
                        "description": ""
                    })
                
                return {
                    "success": True,
                    "nodes": result_nodes,
                    "layout_suggestion": "radial",
                    "extraction_method": "pattern_matching"
                }
            
        except Exception as e:
            logger.error(f"❌ [解析调试] 智能提取也失败: {str(e)}")
        
        # 最终失败，返回默认结构
        logger.error(f"❌ [解析调试] 所有解析方法都失败")
        logger.error(f"📄 [解析调试] 原始响应内容: {response[:500]}...")
        
        return {
            "success": False,
            "error": "AI响应格式错误，无法解析节点信息",
            "nodes": [],
            "raw_response": response[:200]  # 保留部分原始响应用于调试
        }
    
    def _parse_explain_response(self, response: str) -> Dict[str, Any]:
        """解析说明响应"""
        try:
            # 尝试直接解析JSON
            result = json.loads(response)
            if result.get("success") and "explanation" in result:
                return result
        except json.JSONDecodeError:
            pass
        
        # 如果直接解析失败，尝试提取JSON部分
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                result = json.loads(json_str)
                if "explanation" in result:
                    return result
        except json.JSONDecodeError:
            pass
        
        # 解析失败，返回默认结构
        logger.warning(f"AI响应解析失败: {response}")
        return {
            "success": False,
            "error": "AI响应格式错误",
            "explanation": {"summary": "解析失败", "content": response[:200]}
        }
    
    def _parse_theme_response(self, response: str) -> Dict[str, Any]:
        """解析主题生成响应"""
        try:
            # 尝试直接解析JSON
            result = json.loads(response)
            if result.get("success") and "mindmap" in result:
                return result
        except json.JSONDecodeError:
            pass
        
        # 如果直接解析失败，尝试提取JSON部分
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                result = json.loads(json_str)
                if "mindmap" in result:
                    return result
        except json.JSONDecodeError:
            pass
        
        # 解析失败，返回默认结构
        logger.warning(f"AI响应解析失败: {response}")
        return {
            "success": False,
            "error": "AI响应格式错误",
            "mindmap": {}
        } 