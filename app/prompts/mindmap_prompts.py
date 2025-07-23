"""
AI思维导图提示词模板
包含各种场景和模式的专业提示词模板
"""

# 节点扩展提示词模板
EXPAND_NODE_PROMPTS = {
    "creative": """你是一个创意思维专家。请基于给定的节点内容，进行创意性扩展。

当前节点: "{node_text}"
{context_info}

创意扩展要求:
1. 突破传统思维限制，提供新颖独特的角度
2. 鼓励跨领域联想和类比
3. 注重可操作性和实用价值
4. 生成{count}个富有创意的子节点
5. 每个节点都要有明确的价值和意义

请以JSON格式返回结果:
{{
    "success": true,
    "nodes": [
        {{
            "text": "子节点文本",
            "type": "concept|action|detail|question",
            "priority": "high|medium|low",
            "description": "简要说明"
        }}
    ],
    "layout_suggestion": "radial|vertical|horizontal"
}}

请直接返回JSON，不要包含其他解释。""",

    "deep_analysis": """你是一个深度分析专家。请基于给定的节点内容，进行系统性深度分析。

当前节点: "{node_text}"
{context_info}

深度分析要求:
1. 从多个维度进行系统性分解
2. 注重逻辑层次和因果关系
3. 提供理论支撑和数据依据
4. 生成{count}个具有分析价值的子节点
5. 确保内容的准确性和专业性

分析维度参考:
- 定义和本质
- 组成要素和结构
- 功能和作用机制
- 影响因素和变量
- 优势和局限性
- 发展趋势和前景

请以JSON格式返回结果:
{{
    "success": true,
    "nodes": [
        {{
            "text": "子节点文本",
            "type": "concept|action|detail|question",
            "priority": "high|medium|low",
            "description": "简要说明"
        }}
    ],
    "layout_suggestion": "radial|vertical|horizontal"
}}

请直接返回JSON，不要包含其他解释。""",

    "practical": """你是一个实用主义专家。请基于给定的节点内容，提供实用性导向的扩展。

当前节点: "{node_text}"
{context_info}

实用导向要求:
1. 注重可操作性和可执行性
2. 提供具体的方法、工具和步骤
3. 考虑资源限制和现实条件
4. 生成{count}个具有实用价值的子节点
5. 优先考虑成本效益和可行性

实用维度参考:
- 具体操作步骤
- 所需工具和资源
- 时间和成本预算
- 风险和应对措施
- 成功指标和验证方法
- 最佳实践和经验总结

请以JSON格式返回结果:
{{
    "success": true,
    "nodes": [
        {{
            "text": "子节点文本",
            "type": "concept|action|detail|question",
            "priority": "high|medium|low",
            "description": "简要说明"
        }}
    ],
    "layout_suggestion": "radial|vertical|horizontal"
}}

请直接返回JSON，不要包含其他解释。""",

    "academic": """你是一个学术研究专家。请基于给定的节点内容，进行学术性研究展开。

当前节点: "{node_text}"
{context_info}

学术研究要求:
1. 基于严谨的理论框架进行分析
2. 引用相关学术观点和研究成果
3. 注重概念的准确性和理论深度
4. 生成{count}个具有学术价值的子节点
5. 体现批判性思维和研究方法

学术维度参考:
- 理论基础和概念框架
- 相关研究和文献综述
- 研究方法和分析工具
- 实证研究和案例分析
- 学术争议和不同观点
- 研究空白和未来方向

请以JSON格式返回结果:
{{
    "success": true,
    "nodes": [
        {{
            "text": "子节点文本",
            "type": "concept|action|detail|question",
            "priority": "high|medium|low",
            "description": "简要说明"
        }}
    ],
    "layout_suggestion": "radial|vertical|horizontal"
}}

请直接返回JSON，不要包含其他解释。"""
}

# 节点说明提示词模板
EXPLAIN_NODE_PROMPTS = {
    "summary": """你是一个简洁表达专家。请为思维导图节点提供简要说明。

节点内容: "{node_text}"
{context_info}

简要说明要求:
1. 用1-2句话准确概括核心要点
2. 语言简洁明了，避免冗余
3. 突出最关键的信息和价值
4. 适合快速理解和记忆

请以JSON格式返回结果:
{{
    "success": true,
    "explanation": {{
        "summary": "简要说明",
        "content": "核心要点",
        "examples": [],
        "related_concepts": []
    }},
    "style": "info"
}}

请直接返回JSON，不要包含其他解释。""",

    "detailed": """你是一个知识解释专家。请为思维导图节点提供详细说明。

节点内容: "{node_text}"
{context_info}

详细说明要求:
1. 提供完整的定义和背景信息
2. 说明主要特点、功能和作用
3. 解释相关原理和机制
4. 包含适当的例子和应用场景
5. 语言准确专业，逻辑清晰

说明结构建议:
- 基本定义和概念
- 主要特征和要素
- 工作原理和机制
- 应用场景和实例
- 相关概念和延伸

请以JSON格式返回结果:
{{
    "success": true,
    "explanation": {{
        "summary": "简要说明",
        "content": "详细内容",
        "examples": ["具体例子1", "具体例子2"],
        "related_concepts": ["相关概念1", "相关概念2"]
    }},
    "style": "info"
}}

请直接返回JSON，不要包含其他解释。""",

    "examples": """你是一个案例教学专家。请通过具体例子来说明思维导图节点。

节点内容: "{node_text}"
{context_info}

案例说明要求:
1. 提供2-3个具体、真实的例子
2. 例子要具有代表性和说服力
3. 通过例子阐释概念的实际应用
4. 例子要易于理解和记忆
5. 涵盖不同场景和角度

例子类型参考:
- 经典案例和成功实践
- 日常生活中的应用
- 行业或领域的具体应用
- 历史事件和现实案例
- 对比案例和反面教材

请以JSON格式返回结果:
{{
    "success": true,
    "explanation": {{
        "summary": "简要说明",
        "content": "通过例子说明",
        "examples": ["详细例子1", "详细例子2", "详细例子3"],
        "related_concepts": ["相关概念"]
    }},
    "style": "tip"
}}

请直接返回JSON，不要包含其他解释。""",

    "academic": """你是一个学术解释专家。请从学术角度详细说明思维导图节点。

节点内容: "{node_text}"
{context_info}

学术说明要求:
1. 提供严谨的学术定义和理论背景
2. 引用相关理论框架和研究成果
3. 分析学术争议和不同观点
4. 说明研究方法和分析工具
5. 体现学术的深度和广度

学术维度参考:
- 概念的学术定义和演进
- 相关理论和研究框架
- 主要学者和代表性观点
- 研究方法和分析工具
- 当前研究状况和争议
- 未来研究方向和趋势

请以JSON格式返回结果:
{{
    "success": true,
    "explanation": {{
        "summary": "学术定义",
        "content": "学术详细说明",
        "examples": ["学术案例或研究"],
        "related_concepts": ["相关学术概念"]
    }},
    "style": "note"
}}

请直接返回JSON，不要包含其他解释。"""
}

# 主题生成提示词模板
THEME_GENERATION_PROMPTS = {
    "default": """你是一个专业的思维导图设计师。请基于给定主题创建完整的思维导图结构。

主题: "{theme}"
深度: {depth}层

通用结构要求:
1. 创建清晰的中心主题节点
2. 设计{depth}层的层次结构
3. 每个主分支都要有实质性内容
4. 确保逻辑关系清晰合理
5. 涵盖主题的主要方面

结构设计原则:
- 第一层：主要维度和核心分支
- 第二层：具体方面和关键要素
- 第三层：详细内容和具体实例
- 更深层：细节和实施要点

请以JSON格式返回完整的思维导图结构。""",

    "swot": """你是一个战略分析专家。请使用SWOT分析框架为给定主题创建思维导图。

主题: "{theme}"
深度: {depth}层

SWOT分析框架:
1. Strengths (优势) - 内部积极因素
2. Weaknesses (劣势) - 内部消极因素  
3. Opportunities (机会) - 外部积极因素
4. Threats (威胁) - 外部消极因素

分析维度:
- 资源和能力优势
- 存在的问题和不足
- 市场机会和发展空间
- 风险因素和威胁挑战

请以JSON格式返回SWOT分析思维导图结构。""",

    "5w1h": """你是一个系统思维专家。请使用5W1H框架为给定主题创建思维导图。

主题: "{theme}"
深度: {depth}层

5W1H分析框架:
1. What (什么) - 事物的定义和内容
2. Why (为什么) - 原因、目的和意义
3. When (何时) - 时间、阶段和时机
4. Where (何地) - 地点、范围和环境
5. Who (谁) - 相关人员和利益方
6. How (如何) - 方法、过程和实施

分析维度要全面覆盖主题的各个方面，确保信息完整性。

请以JSON格式返回5W1H分析思维导图结构。""",

    "pyramid": """你是一个逻辑结构专家。请使用金字塔原理为给定主题创建思维导图。

主题: "{theme}"
深度: {depth}层

金字塔原理结构:
1. 结论先行 - 核心观点和主要结论
2. 以上统下 - 上层统领下层内容
3. 归类分组 - 同类信息归为一组
4. 逻辑递进 - 符合逻辑顺序排列

层次设计:
- 顶层：核心结论和主要观点
- 第二层：支撑论据和关键论点
- 第三层：具体证据和详细分析
- 更深层：事实数据和实例支撑

请以JSON格式返回金字塔结构思维导图。"""
}

# 优化建议提示词模板
OPTIMIZATION_PROMPTS = {
    "structure": """你是一个思维导图结构优化专家。请分析给定的思维导图结构并提供优化建议。

当前思维导图结构:
{mindmap_structure}

结构优化分析:
1. 层次是否清晰合理
2. 分支是否平衡
3. 逻辑关系是否正确
4. 是否存在冗余或遗漏
5. 布局是否美观实用

请提供具体的优化建议和改进方案。""",

    "content": """你是一个内容质量专家。请分析思维导图的内容质量并提供改进建议。

思维导图内容:
{mindmap_content}

内容质量评估:
1. 信息的准确性和专业性
2. 内容的完整性和深度
3. 表达的清晰性和简洁性
4. 价值的实用性和可操作性
5. 逻辑的连贯性和合理性

请提供内容改进的具体建议。""",

    "connections": """你是一个关系分析专家。请分析思维导图中节点间的潜在关联性。

节点列表:
{node_list}

关联性分析:
1. 识别节点间的逻辑关系
2. 发现潜在的连接机会
3. 分析因果关系和依赖关系
4. 找出互补和协同关系
5. 识别重要的关键节点

请推荐应该建立连接的节点对。"""
}

def get_expand_prompt(mode, node_text, context_info, count):
    """获取节点扩展提示词"""
    template = EXPAND_NODE_PROMPTS.get(mode, EXPAND_NODE_PROMPTS["creative"])
    return template.format(
        node_text=node_text,
        context_info=context_info,
        count=count
    )

def get_explain_prompt(explanation_type, node_text, context_info):
    """获取节点说明提示词"""
    template = EXPLAIN_NODE_PROMPTS.get(explanation_type, EXPLAIN_NODE_PROMPTS["detailed"])
    return template.format(
        node_text=node_text,
        context_info=context_info
    )

def get_theme_prompt(framework, theme, depth):
    """获取主题生成提示词"""
    template = THEME_GENERATION_PROMPTS.get(framework, THEME_GENERATION_PROMPTS["default"])
    return template.format(
        theme=theme,
        depth=depth
    )

def format_context_info(context, include_parent=True, include_siblings=False):
    """格式化上下文信息"""
    context_parts = []
    
    if context and include_parent and context.get('parent'):
        context_parts.append(f"父节点: \"{context['parent']}\"")
    
    if context and include_siblings and context.get('siblings'):
        siblings_text = "、".join(context['siblings'])
        context_parts.append(f"同级节点: {siblings_text}")
    
    return "\n".join(context_parts) if context_parts else "无额外上下文信息" 