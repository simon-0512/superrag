# CLAUDE_CHN.md

本文件为Claude Code (claude.ai/code) 在此代码库中工作时提供中文指导。

## 项目概述

SuperRAG (Agorix) 是一个基于Flask构建的现代智能对话和知识分享平台。它融合了AI对话功能、知识库管理和社区特性。系统集成了DeepSeek-V3 API进行AI响应，并使用LangChain进行上下文管理。

## 开发命令

### 数据库管理
```bash
# 初始化数据库并创建示例数据
python manage.py init_db

# 数据库健康检查
python manage.py health_check

# 显示数据库信息
python manage.py db_info

# 创建新用户
python manage.py create_user

# 列出所有用户
python manage.py list_users

# 重置数据库（谨慎使用）
python manage.py reset_db
```

### 应用启动
```bash
# 开发模式（运行在2727端口）
python run.py

# 生产模式（通过环境变量）
FLASK_ENV=production python run.py
```

### 测试
项目没有配置特定的测试框架。检查现有测试文件：
- `test_admin_system.py`
- `test_langchain_integration.py`
- `test_timezone_only.py`

### 代码质量工具
项目使用以下开发工具（来自requirements.txt）：
- `black` - 代码格式化
- `flake8` - 代码检查
- `isort` - 导入排序
- `pytest` - 测试框架

## 架构概览

### 核心组件

**Flask应用工厂** (`app/__init__.py`):
- 多环境配置（开发、生产、测试）
- 模块化路由的蓝图注册
- 错误处理（404、500）
- 自定义Jinja2过滤器

**数据库层** (`app/database.py`):
- SQLAlchemy ORM，SQLite（开发）/ PostgreSQL（生产）
- 大部分表使用UUID主键
- 时区感知的日期时间处理（UTC+8）

**认证系统** (`app/auth/`):
- 基于Flask-Login的用户会话
- 基于角色的访问控制（admin、tester、vip、user）
- 用户注册和个人资料管理

**AI集成**:
- DeepSeek-V3 API集成 (`app/services/deepseek_service.py`)
- LangChain框架用于上下文管理 (`app/services/langchain_service.py`)
- 对话摘要和token管理

### 关键模型

**用户系统** (`app/models/user.py`):
- UUID主键
- 基于角色的权限（admin、tester、vip、user）
- 用户状态标志（active、verified、disabled、deleted）
- 时区感知的时间戳

**知识库** (`app/models/knowledge_base.py`):
- 文档上传和处理（PDF、Word、TXT）
- 使用FAISS/ChromaDB的向量嵌入
- 用于RAG检索的文档分块
- 带消息线程的对话历史

**社区功能** (`app/models/community.py`):
- 带AI生成内容的社交帖子
- 用户互动（点赞、评论、分享）
- 用户关注系统

### 服务层

**对话服务** (`app/services/conversation_service.py`):
- 多轮对话管理
- 上下文窗口处理
- 每5轮自动对话摘要
- Token计数和优化

**LangChain服务** (`app/services/langchain_service.py`):
- 内存管理（buffer、summary_buffer、sliding_window）
- 上下文分析和效率评估
- 可配置的内存类型和参数

**社区服务** (`app/services/community_service.py`):
- 社交媒体功能
- 帖子创建和管理
- 用户互动追踪

### 路由结构

**主要路由** (`app/routes/main.py`):
- `/` - 首页
- `/chat` - AI对话界面
- `/knowledge` - 知识库管理
- `/dashboard` - 用户仪表板

**API路由** (`app/routes/api.py`):
- `/api/chat` - 聊天消息
- `/api/conversations` - 对话管理
- `/api/upload` - 文档上传
- `/api/database_search` - 数据库查询

**管理员路由** (`app/routes/admin.py`):
- `/admin/dashboard` - 管理员仪表板（带分析）
- `/admin/users` - 用户管理
- `/admin/conversations` - 对话监督
- `/admin/database_tools` - SQL查询界面

## 配置

### 环境设置
配置通过`config/settings.py`中的环境特定类管理：
- `DevelopmentConfig` - 调试模式，SQLite数据库
- `ProductionConfig` - 生产设置
- `TestingConfig` - 内存数据库用于测试

### 关键配置选项
```python
# DeepSeek API
DEEPSEEK_API_KEY = "your-api-key"
DEEPSEEK_API_BASE = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# LangChain设置
LANGCHAIN_ENABLED = True
LANGCHAIN_MEMORY_TYPE = "buffer"  # 或 "summary_buffer", "sliding_window"
LANGCHAIN_MAX_TOKEN_LIMIT = 8000
LANGCHAIN_WINDOW_SIZE = 10

# 对话管理
CONVERSATION_SUMMARY_ROUNDS = 10
MAX_CONTEXT_MESSAGES = 20
```

## 数据库结构

### 主要表格
- `users` - 带基于角色访问的用户账户
- `knowledge_bases` - 每个用户的文档集合
- `documents` - 带处理状态的单个文件
- `document_chunks` - 用于RAG检索的文本片段
- `conversations` - 带元数据的聊天会话
- `messages` - 单个聊天消息
- `community_posts` - 社交媒体帖子
- `community_interactions` - 用户参与数据

### 已知问题
社区表存在类型不匹配（外键的INTEGER vs VARCHAR(36)），但由于SQLite的弱类型特性仍能工作。详情请参阅`docs/database_structure.md`。

## 开发模式

### 错误处理
- 自定义错误页面 (`app/templates/errors/`)
- 500错误时数据库会话回滚
- 服务层全面日志记录

### 安全性
- 通过装饰器实现基于角色的访问控制
- 所有表单的输入验证
- 使用Flask-WTF的CSRF保护
- 使用bcrypt的密码哈希

### 前端架构
- 使用Jinja2的服务器端渲染模板
- Bootstrap 5 + 遵循GitHub设计原则的自定义CSS
- WebSocket集成用于实时聊天
- 移动优先的响应式设计

### 文件结构约定
- `app/models/` - 数据库模式定义
- `app/services/` - 业务逻辑层
- `app/routes/` - HTTP端点处理程序
- `app/templates/` - HTML模板
- `app/static/` - CSS、JS、图像静态资源

## 测试策略

运行现有测试以验证功能：
```bash
python test_admin_system.py
python test_langchain_integration.py
python test_timezone_only.py
```

对于新功能，遵循现有测试模式并考虑：
- 测试中的数据库事务回滚
- 模拟外部API调用（DeepSeek）
- 测试基于角色的访问控制
- 验证时区处理

## 常见开发任务

### 添加新的AI模型
1. 在`app/services/`中创建服务类
2. 在`config/settings.py`中添加配置选项
3. 更新对话服务以处理新模型
4. 在聊天界面中添加模型选择

### 扩展用户角色
1. 更新`app/models/user.py`中的`User`模型
2. 修改`app/decorators.py`中的角色权限
3. 在模板中添加角色特定的UI元素
4. 更新管理员用户管理界面

### 添加文档类型
1. 扩展`app/services/`中的文档处理
2. 更新文件上传验证
3. 添加新的MIME类型支持
4. 测试文档分块和向量化

## 部署说明

- 默认端口：2727
- 支持SQLite（开发）和PostgreSQL（生产）
- 可用Redis缓存
- 生产环境推荐Gunicorn + Nginx
- 详细设置请参阅`docs/deployment_guide.md`

## 安全考虑

- 切勿将API密钥提交到仓库
- 使用环境变量进行敏感配置
- 对所有用户输入实施适当的输入验证
- 定期审计用户权限
- 保持依赖项更新以获得安全补丁

## 用户角色权限

### 管理员 (admin)
- 拥有所有系统权限
- 可以管理用户账户
- 可以访问后台管理界面
- 可以执行数据库操作
- 默认账户：admin/admin123

### 测试人员 (tester)
- 可以访问测试功能按钮
- 可以进行系统调试
- 具有高级功能权限
- 默认账户：tester/tester123

### VIP用户 (vip)
- 拥有高级功能权限
- 可以使用知识库管理
- 默认账户：vipuser/vip123

### 普通用户 (user)
- 基础功能权限
- 可以进行对话
- 可以查看知识库
- 默认账户：testuser/test123

## 特色功能

### 智能对话系统
- 支持多轮深度对话
- 流式响应显示
- 自动对话摘要
- 智能标题生成

### 知识库管理
- 支持多种文档格式（PDF、Word、TXT）
- 基于RAG的智能检索
- 文档向量化存储
- 分类管理

### 智能划线功能
- 选中文本深度提问
- AI内容真实性验证
- 实时响应用户选择

### 社区功能
- 社交媒体式的帖子分享
- 用户互动（点赞、评论、关注）
- AI生成内容支持

### 管理员后台
- 数据可视化仪表板
- 用户管理和权限控制
- 对话系统监控
- 数据库查询工具

## 故障排除

### 常见问题
1. **数据库连接失败**
   - 检查数据库配置
   - 运行`python manage.py health_check`

2. **API调用失败**
   - 验证DeepSeek API密钥
   - 检查网络连接

3. **文档上传失败**
   - 检查文件格式支持
   - 确认文件大小限制

### 日志查看
```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log
```

## 开发环境设置

### 依赖安装
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 配置文件
在`config/settings.py`中配置：
- DeepSeek API密钥
- 数据库连接
- LangChain参数
- 其他系统设置

### 启动流程
1. 初始化数据库：`python manage.py init_db`
2. 启动应用：`python run.py`
3. 访问：`http://localhost:2727`

这个项目采用了模块化的设计，便于功能扩展和维护。所有的核心功能都有相应的服务层处理，确保了代码的清晰性和可维护性。