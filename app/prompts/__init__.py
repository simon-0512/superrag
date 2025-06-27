# -*- coding: utf-8 -*-
"""
提示词管理模块
统一管理系统中使用的所有提示词
"""

from .system_prompts import SystemPrompts
from .conversation_prompts import ConversationPrompts

__all__ = ['SystemPrompts', 'ConversationPrompts'] 