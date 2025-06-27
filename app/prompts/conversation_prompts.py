# -*- coding: utf-8 -*-
"""
对话相关提示词管理
包含多轮对话、上下文总结等功能的提示词
"""

class ConversationPrompts:
    """对话提示词集合"""
    
    # 上下文总结提示词
    CONTEXT_SUMMARIZATION = """你是SuperRAG智能助手的对话分析专家。请对以下多轮对话进行智能总结，提炼出关键信息以便后续对话使用。

总结要求：
1. **核心主题**：识别对话的主要话题和讨论焦点
2. **提问意图**：分析用户的核心需求和问题导向
3. **关键数据**：提取对话中提到的重要事实、数字、概念
4. **用户疑问**：总结用户提出的关键问题和关注点
5. **问题核心**：识别问题的本质和深层逻辑
6. **知识脉络**：梳理讨论的知识结构和逻辑关系
7. **未解决问题**：标记尚未充分回答的疑问

总结格式：
```
【核心主题】：...
【提问意图】：...
【关键数据】：...
【用户疑问】：...
【问题核心】：...
【知识脉络】：...
【未解决问题】：...
```

注意事项：
- 保持总结的准确性和完整性
- 突出重点，去除冗余信息
- 保留对后续对话有价值的上下文
- 总结长度控制在原对话的1/3左右

请基于以下对话历史进行总结：

{conversation_history}"""

    # 基于总结的系统提示词
    SUMMARIZED_CONTEXT_SYSTEM = """你是SuperRAG智能助手，基于DeepSeek-V3模型。

当前对话基于以下总结的上下文继续：

{context_summary}

请基于上述上下文总结继续对话，保持话题的连贯性和深度。如果用户的问题与之前的讨论相关，请充分利用已有的上下文信息。

请用中文回答，保持专业且友好的语气。"""

    # 对话连贯性检查提示词
    CONTINUITY_CHECK = """请分析以下用户问题是否与之前的对话上下文相关：

上下文总结：{context_summary}
用户当前问题：{current_question}

如果相关，请说明关联性；如果不相关，请说明这是一个新话题。

分析结果（请只回答"相关"或"不相关"，并简要说明原因）："""

    # 对话质量评估提示词
    CONVERSATION_QUALITY = """请评估以下对话的质量和深度：

评估维度：
1. 问题质量：用户提问的清晰度和深度
2. 回答质量：AI回复的准确性和有用性
3. 对话深度：讨论的深入程度和专业性
4. 知识价值：对话产生的知识价值

对话内容：{conversation_content}

请给出评估结果和改进建议。"""

    @classmethod
    def get_summarization_prompt(cls, conversation_history: str) -> str:
        """
        获取上下文总结提示词
        
        Args:
            conversation_history: 对话历史字符串
            
        Returns:
            格式化后的总结提示词
        """
        return cls.CONTEXT_SUMMARIZATION.format(conversation_history=conversation_history)
    
    @classmethod
    def get_summarized_system_prompt(cls, context_summary: str) -> str:
        """
        获取基于总结的系统提示词
        
        Args:
            context_summary: 上下文总结
            
        Returns:
            格式化后的系统提示词
        """
        return cls.SUMMARIZED_CONTEXT_SYSTEM.format(context_summary=context_summary)
    
    @classmethod
    def get_continuity_check_prompt(cls, context_summary: str, current_question: str) -> str:
        """
        获取对话连贯性检查提示词
        
        Args:
            context_summary: 上下文总结
            current_question: 当前用户问题
            
        Returns:
            格式化后的连贯性检查提示词
        """
        return cls.CONTINUITY_CHECK.format(
            context_summary=context_summary,
            current_question=current_question
        ) 