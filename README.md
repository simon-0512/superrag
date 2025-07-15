# Agorix - 现代雅典集市 · 智能对话交流分享平台

[![GitHub Repo](https://img.shields.io/badge/GitHub-superrag-blue?logo=github)](https://github.com/simon-0512/superrag)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-red.svg)](https://flask.palletsprojects.com)

**Version 0.2.0** - 智能对话，深度学习，知识留存，用户角色管理

## 🌟 项目简介

Agorix 是一个现代雅典集市式的智能平台，融合智能对话、交流分享与知识管理于一体。就像古雅典集市是智慧交汇的中心，Agorix 致力于成为现代人智慧流动的数字空间。

## ✨ 核心功能

### 🤖 智能对话系统
- **多轮对话**：支持连续深入讨论，保持上下文语境
- **流式响应**：实时显示AI回复内容，提升交互体验
- **智能总结**：每5轮对话自动提炼关键信息，节省Token消耗
- **对话管理**：支持新建、切换、删除对话，智能标题生成
- **历史搜索**：快速搜索和回顾历史对话

### 🧠 LangChain 上下文管理
- **智能记忆**：支持摘要缓冲记忆和滑动窗口记忆
- **上下文分析**：实时分析对话状态，提供记忆效率评估
- **自动摘要**：长对话智能生成摘要，优化token使用
- **配置管理**：支持多种记忆类型和参数自定义

### 📚 知识库管理
- **文档上传**：支持PDF、Word、TXT等多种格式
- **智能检索**：基于RAG技术的知识检索与增强
- **分类管理**：个人知识库的结构化组织

### 🖊️ 智能划线功能
- **刨根问底**：对选中文本进行深度提问
- **质疑验证**：AI核查内容真实性
- **即选即问**：实时响应用户选择

### 💾 知识留存系统
- **对话总结**：智能提炼对话主题和要点
- **PDF导出**：生成结构化报告，便于归档
- **知识归档**：个人知识库持久化存储

### 👥 用户角色管理 (0.2.0 新增)
- **多角色体系**：支持管理员、测试人员、VIP用户、普通用户四种角色
- **权限控制**：基于角色的功能权限管理
- **测试功能**：测试人员可访问系统测试按钮和调试功能
- **角色管理**：管理员可设置和修改用户角色
- **用户注册**：新用户默认为普通用户角色

### 🛡️ 管理员后台系统 (0.2.0 新增)
- **数据可视化仪表板**：统计图表展示用户、对话、社区数据
- **用户管理**：增删改查用户信息，角色设置，状态管理
- **对话系统管理**：查看和管理所有用户对话记录
- **论坛内容管理**：社区帖子和互动内容的审核管理
- **SQL查询工具**：安全的数据库查询功能，支持数据导出
- **权限控制**：仅限管理员访问，多重安全验证

### ⏰ 时区统一处理 (0.2.0 新增)
- **东八区标准化**：所有时间字段统一为东八区时间
- **注册时间修复**：用户注册时间正确显示为本地时间
- **登录时间修复**：用户登录时间统一为东八区时间
- **对话时间修复**：对话和消息的创建时间本地化
- **时区工具函数**：提供时区转换和格式化工具

## 🎨 设计风格指导 (GitHub精致化风格)

### 界面设计原则

**Agorix采用GitHub风格的精致化设计语言，追求简洁、优雅、高效的用户体验。**

#### 🔸 核心设计理念
- **微圆角设计**: 统一使用6px圆角，避免过大的弧度
- **精致间距**: 合理的12-16px间距，不追求空旷感
- **克制的字体**: 14px字体大小，500字重，谨慎使用粗体
- **功能导向**: 每个元素都有明确的功能性，拒绝装饰性设计

#### 🔸 颜色系统
```css
/* 主色调 - GitHub风格 */
--bg-primary: #ffffff          /* 主背景色 */
--bg-secondary: #f6f8fa        /* 次要背景色 */
--border-primary: #d1d9e0      /* 主边框色 */
--border-secondary: #eaeef2    /* 次要边框色 */
--text-primary: #24292f        /* 主文本色 */
--text-secondary: #656d76      /* 次要文本色 */
--text-muted: #8c959f          /* 弱化文本色 */

/* 功能色 */
--success: #1f883d            /* 成功/确认 */
--danger: #da3633             /* 危险/删除 */
--warning: #bf8700            /* 警告 */
--info: #0969da               /* 信息/链接 */
```

#### 🔸 组件规范

**模态框 (Modal)**
```css
.modal-content {
    border: 1px solid #d1d9e0;
    border-radius: 6px;
    box-shadow: 0 8px 24px rgba(140, 149, 159, 0.2);
}

.modal-header, .modal-footer {
    background: #f6f8fa;
    padding: 12px 16px;
}

.modal-body {
    padding: 16px;
    font-size: 14px;
    line-height: 1.5;
}
```

**按钮 (Button)**
```css
.btn {
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    padding: 6px 12px;
    line-height: 1.45;
}
```

**表单控件 (Form)**
```css
.form-control, .form-select {
    border: 1px solid #d1d9e0;
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 14px;
}
```

**表格 (Table)**
```css
.table th {
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 8px 12px;
}

.table td {
    padding: 8px 12px;
    font-size: 14px;
}
```

#### 🔸 交互设计
- **悬停状态**: 柔和的颜色变化和轻微的transform效果
- **焦点状态**: 蓝色边框 + 柔和阴影，避免突兀的outline
- **加载状态**: 简洁的spinner或skeleton屏幕
- **反馈系统**: Toast通知优于Alert弹窗

#### 🔸 响应式设计
- **断点设置**: 576px, 768px, 992px, 1200px
- **移动优先**: 先设计移动端，再适配桌面端
- **触摸友好**: 最小44px的可点击区域

#### 🔸 无障碍设计
- **语义化HTML**: 正确使用标签和ARIA属性
- **键盘导航**: 支持Tab键导航
- **对比度**: 确保文本对比度符合WCAG 2.1标准
- **屏幕阅读器**: 提供必要的alt文本和label

#### 🔸 性能优化
- **CSS优化**: 避免深层嵌套，使用CSS变量
- **JavaScript优化**: 事件委托，防抖节流
- **图像优化**: WebP格式，适当压缩
- **字体优化**: font-display: swap

### 实施检查清单

开发新功能或优化现有页面时，请确保：

- [ ] 使用6px微圆角设计
- [ ] 遵循14px字体，500字重规范
- [ ] 应用GitHub风格的颜色系统
- [ ] 实现精致的12-16px间距
- [ ] 添加柔和的悬停和焦点效果
- [ ] 确保移动端响应式体验
- [ ] 提供合适的加载和错误状态
- [ ] 测试键盘导航和无障碍访问

**记住：精致不是复杂，而是每个细节都恰到好处。**

---

## 🏗️ 技术架构

### 后端技术栈
- **框架**: Flask + SQLAlchemy
- **AI模型**: DeepSeek-V3 API
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **上下文管理**: LangChain 框架
- **文档处理**: PyPDF2, python-docx
- **向量存储**: FAISS, ChromaDB

### 前端技术栈
- **基础**: HTML5, CSS3, JavaScript
- **UI框架**: Bootstrap 5 + 自定义样式
- **实时通信**: WebSocket (Flask-SocketIO)
- **文本选择**: Rangy.js

### 系统架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面      │───→│   Flask后端     │───→│  DeepSeek-V3   │
│  (Web UI)      │    │                 │    │     API        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  智能划线组件   │    │  LangChain     │
│   (实时问答)    │    │  (上下文管理)   │
└─────────────────┘    └─────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   知识库管理    │    │   PDF生成       │
│   (RAG检索)    │    │   (知识留存)    │
└─────────────────┘    └─────────────────┘
```

## 📁 项目结构

```
SuperRAG/
├── app/                         # 应用主目录
│   ├── __init__.py             # Flask应用工厂
│   ├── database.py             # 数据库初始化
│   ├── models/                 # 数据模型
│   │   ├── user.py            # 用户模型（含角色管理）
│   │   └── knowledge_base.py  # 知识库、对话、消息模型
│   ├── routes/                 # 路由控制器
│   │   ├── main.py            # 主要页面路由
│   │   ├── api.py             # API接口
│   │   ├── role_api.py        # 角色管理API
│   │   └── admin.py           # 管理员后台路由
│   ├── services/               # 业务服务层
│   │   ├── deepseek_service.py    # DeepSeek API服务
│   │   ├── conversation_service.py # 对话管理服务
│   │   ├── langchain_service.py   # LangChain上下文服务
│   │   └── role_service.py        # 角色管理服务
│   ├── utils/                  # 工具函数
│   │   └── timezone_utils.py   # 时区处理工具
│   ├── prompts/                # 提示词管理
│   ├── auth/                   # 用户认证
│   ├── static/                 # 静态资源
│   │   ├── css/style.css      # 样式文件
│   │   └── js/               # JavaScript文件
│   └── templates/              # HTML模板
│       ├── index.html         # 首页
│       ├── chat.html          # 对话页面
│       ├── dashboard.html     # 用户仪表板
│       └── admin/             # 管理员后台模板
│           ├── base.html      # 后台基础模板
│           ├── dashboard.html # 管理员仪表板
│           ├── users.html     # 用户管理页面
│           └── database_tools.html # 数据库工具页面
├── config/                     # 配置文件
│   ├── settings.py            # 应用配置
│   └── database.py            # 数据库配置
├── migrations/                 # 数据库迁移文件
├── tests/                      # 测试文件
├── requirements.txt            # Python依赖包
├── run.py                     # 应用启动文件
└── manage.py                  # 管理命令工具
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/simon-0512/superrag.git
cd SuperRAG

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库初始化

```bash
# 初始化数据库
python manage.py init_db

# 检查系统状态
python manage.py health_check
```

### 3. 启动应用

```bash
# 开发环境启动
python run.py

# 应用将运行在 http://localhost:2727
```

### 4. 用户账号

**系统管理员**（拥有所有权限）：
- 用户名：`admin`
- 密码：`admin123`

**测试人员**（可访问测试功能）：
- 用户名：`tester`
- 密码：`tester123`

**VIP用户**（高级功能权限）：
- 用户名：`vipuser`
- 密码：`vip123`

**普通用户**（基础功能）：
- 用户名：`testuser`  
- 密码：`test123`

## ⚙️ 配置说明

### 核心配置参数

在 `config/settings.py` 中可以配置以下参数：

**DeepSeek API 配置**:
```python
DEEPSEEK_API_KEY = "your-api-key"
DEEPSEEK_API_BASE = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"
```

**对话管理配置**:
```python
CONVERSATION_SUMMARY_ROUNDS = 5      # 每几轮对话进行总结
MAX_CONTEXT_MESSAGES = 20           # 最大上下文消息数
CONTEXT_WINDOW_SIZE = 4000          # 上下文窗口大小(tokens)
```

**LangChain 配置**:
```python
LANGCHAIN_ENABLED = True            # 是否启用LangChain
LANGCHAIN_MEMORY_TYPE = 'summary_buffer'  # 记忆类型
LANGCHAIN_MAX_TOKEN_LIMIT = 2000    # 摘要触发阈值
LANGCHAIN_WINDOW_SIZE = 10          # 窗口记忆大小
```

**用户角色配置**:
```python
# 默认用户角色
DEFAULT_USER_ROLE = 'user'          # 新注册用户的默认角色

# 角色权限定义
ROLE_PERMISSIONS = {
    'admin': ['*'],                 # 管理员拥有所有权限
    'tester': ['test_access', 'knowledge_manage', 'data_export'],
    'vip': ['knowledge_manage', 'advanced_features'],
    'user': ['basic_usage', 'knowledge_view']
}
```

### 环境变量

可通过环境变量覆盖配置：

```bash
export FLASK_ENV=production
export SECRET_KEY=your-secret-key
export DEEPSEEK_API_KEY=your-api-key
export PORT=2727
```

## 🛠️ 数据库管理

系统提供了完整的数据库管理命令：

```bash
# 查看所有可用命令
python manage.py help

# 用户管理
python manage.py create_user          # 创建新用户
python manage.py list_users           # 列出所有用户

# 数据库操作
python manage.py db_info              # 查看数据库信息
python manage.py reset_db             # 重置数据库(谨慎使用)

# 系统监控
python manage.py health_check         # 系统健康检查
```

## 📊 功能说明

### 对话页面功能

1. **左侧对话列表**
   - 显示历史对话，按时间排序
   - 支持搜索对话内容
   - 新建、切换、删除对话

2. **中间对话区域**
   - 流式显示AI回复
   - 支持代码高亮
   - 智能划线功能

3. **右侧调试面板**（开发模式）
   - 实时显示系统状态
   - 上下文管理信息
   - 消息保存监控

### 智能划线使用

1. 在AI回复中选中任意文本
2. 选择"刨根问底"进行深度提问
3. 选择"质疑验证"核查内容真实性
4. 系统自动发起新的对话轮次

### 知识库管理

1. 访问 `/knowledge` 页面
2. 上传PDF、Word、TXT等文档
3. 系统自动处理和向量化
4. 在对话中可以检索相关知识

## 🔧 开发指南

### 代码结构说明

- **Models**: 定义数据结构和数据库关系
- **Services**: 实现业务逻辑，与外部API交互
- **Routes**: 处理HTTP请求和响应
- **Templates**: 前端页面模板
- **Static**: CSS、JavaScript等静态资源

### 扩展功能

系统采用模块化设计，便于扩展：

- 新增AI模型：在`services/`下创建新的服务类
- 添加文档类型：扩展`document_service.py`
- 自定义提示词：修改`prompts/`下的提示词文件

## 📄 API 文档

### 主要API接口

- `POST /api/chat` - 发送消息
- `GET /api/conversations` - 获取对话列表
- `POST /api/conversations` - 创建新对话
- `DELETE /api/conversations/<id>` - 删除对话
- `POST /api/upload` - 上传文档
- `GET /api/database_search` - 数据库搜索

### 消息格式

```json
{
  "conversation_id": "string",
  "message": "string",
  "message_type": "user|assistant",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🐛 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库配置
   - 运行`python manage.py health_check`

2. **API调用失败**
   - 验证DeepSeek API密钥
   - 检查网络连接

3. **文档上传失败**
   - 检查文件格式是否支持
   - 确认文件大小未超过限制

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log
```

## 📝 更新日志

### Version 0.1.0 (2024-12-XX)

**核心功能**:
- ✅ 智能对话系统，支持多轮对话
- ✅ LangChain上下文管理集成
- ✅ 智能划线功能
- ✅ 知识库管理系统
- ✅ 用户认证和权限管理
- ✅ PDF导出和知识留存

**技术特性**:
- ✅ Flask + SQLAlchemy 架构
- ✅ DeepSeek-V3 API集成
- ✅ WebSocket实时通信
- ✅ 响应式UI设计
- ✅ 完整的数据库管理工具

v2.0.0 开发计划：
一、设计用户系统、开发用户注册功能以及与用户系统相应的数据表结构，用户角色四类：1. 管理员，具有增删改查测试全部权限 2. 测试人员 可以看到页面中的测试按钮 3. VIP用户 4. 普通用户 VIP与普通用户暂时只做后台区分，不做功能上区别，以便未来增加功能上的区别   二、梳理当前数据表的结构，主要是 1. 用户系统 2. 对话系统 3. 论坛系统 把这三部分数据表结构梳理出来，形成文档，后续开发严格按照文档进行  三、梳理用户系统、对话系统、论坛系统的主要工作流、重要函数调用关系，形成文档，检查与清理不必要的函数调用，优化逻辑提高页面访问效率。

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目：

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/新功能`)
3. 提交更改 (`git commit -am '添加新功能'`)
4. 推送分支 (`git push origin feature/新功能`)
5. 创建Pull Request

## 📞 技术支持

如有问题或建议，请通过以下方式联系：

- 提交GitHub Issue
- 发送邮件到项目邮箱
- 查看项目Wiki文档

---

**Agorix** - 现代雅典集市，智慧流动之地 🏛️ 