# SuperRAG - 智能问答与知识管理平台

**Version 0.1.0** - 智能对话，深度学习，知识留存

## 🌟 项目简介

SuperRAG 是一个基于大模型的智能问答与知识管理平台，通过连续对话、上下文管理、知识总结等功能，帮助用户深入理解和掌握知识。

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
│   │   ├── user.py            # 用户模型
│   │   └── knowledge_base.py  # 知识库、对话、消息模型
│   ├── routes/                 # 路由控制器
│   │   ├── main.py            # 主要页面路由
│   │   └── api.py             # API接口
│   ├── services/               # 业务服务层
│   │   ├── deepseek_service.py    # DeepSeek API服务
│   │   ├── conversation_service.py # 对话管理服务
│   │   └── langchain_service.py   # LangChain上下文服务
│   ├── prompts/                # 提示词管理
│   ├── auth/                   # 用户认证
│   ├── static/                 # 静态资源
│   │   ├── css/style.css      # 样式文件
│   │   └── js/               # JavaScript文件
│   └── templates/              # HTML模板
│       ├── index.html         # 首页
│       ├── chat.html          # 对话页面
│       └── dashboard.html     # 用户仪表板
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
git clone <repository-url>
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

**管理员账号**：
- 用户名：`admin`
- 密码：`admin123`

**测试账号**：
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

**SuperRAG** - 让AI对话更智能，让知识管理更高效 🚀 