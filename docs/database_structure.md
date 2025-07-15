# SuperRAG 数据库结构文档

## 概览

SuperRAG 系统使用 SQLite 数据库，包含以下核心功能模块：
- 用户管理系统
- 知识库管理系统
- 对话系统
- 社区功能系统

## 数据表结构

### 1. 用户管理 (User Management)

#### 1.1 users - 用户表 ✅ **核心表**
| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | VARCHAR(36) | ✓ | uuid | 主键，UUID格式 |
| username | VARCHAR(80) | ✓ | - | 用户名，唯一 |
| email | VARCHAR(120) | ✓ | - | 邮箱，唯一 |
| password_hash | VARCHAR(255) | ✓ | - | 密码哈希 |
| nickname | VARCHAR(100) | ✗ | NULL | 用户昵称 |
| avatar_url | VARCHAR(255) | ✗ | NULL | 头像URL |
| bio | TEXT | ✗ | NULL | 个人简介 |
| is_active | BOOLEAN | ✓ | TRUE | 是否活跃 |
| is_verified | BOOLEAN | ✓ | FALSE | 是否验证邮箱 |
| disabled | BOOLEAN | ✓ | FALSE | 是否禁用（可登录但无法使用功能） |
| deleted | BOOLEAN | ✓ | FALSE | 是否软删除（无法登录） |
| role | VARCHAR(6) | ✓ | 'user' | 用户角色（枚举：admin, tester, vip, user） |
| preferences | JSON | ✓ | {} | 用户偏好设置 |
| created_at | DATETIME | ✓ | 当前时间 | 创建时间 |
| updated_at | DATETIME | ✓ | 当前时间 | 更新时间 |
| last_login_at | DATETIME | ✗ | NULL | 最后登录时间 |

**相关功能模块：**
- 用户注册/登录 (`app/auth/routes.py`)
- 用户资料管理 (`app/templates/auth/profile.html`)
- 管理员用户管理 (`app/routes/admin.py`)
- 头像上传功能 (`app/utils/file_utils.py`)
- 权限控制 (`app/decorators.py`)


### 2. 知识库管理 (Knowledge Base Management)

#### 2.1 knowledge_bases - 知识库表 ✅ **核心表**
| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | VARCHAR(36) | ✓ | uuid | 主键，UUID格式 |
| name | VARCHAR(100) | ✓ | - | 知识库名称 |
| description | TEXT | ✗ | NULL | 知识库描述 |
| user_id | VARCHAR(36) | ✓ | - | 所属用户ID，外键→users.id |
| is_public | BOOLEAN | ✓ | FALSE | 是否公开 |
| is_active | BOOLEAN | ✓ | TRUE | 是否激活 |
| document_count | INTEGER | ✓ | 0 | 文档数量 |
| total_size | BIGINT | ✓ | 0 | 总大小（字节） |
| embedding_model | VARCHAR(50) | ✓ | 'text-embedding-ada-002' | 嵌入模型 |
| chunk_size | INTEGER | ✓ | 1000 | 分块大小 |
| chunk_overlap | INTEGER | ✓ | 200 | 分块重叠 |
| created_at | DATETIME | ✓ | 当前时间 | 创建时间 |
| updated_at | DATETIME | ✓ | 当前时间 | 更新时间 |

**依赖关系：**
- 外键：user_id → users.id (一对多)
- 反向关系：documents (一对多)

#### 2.2 documents - 文档表 ✅ **核心表**
| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | VARCHAR(36) | ✓ | uuid | 主键 |
| filename | VARCHAR(255) | ✓ | - | 文件名 |
| original_filename | VARCHAR(255) | ✓ | - | 原始文件名 |
| file_type | VARCHAR(10) | ✓ | - | 文件类型 |
| file_size | BIGINT | ✓ | - | 文件大小 |
| file_path | VARCHAR(500) | ✓ | - | 文件路径 |
| title | VARCHAR(200) | ✗ | NULL | 文档标题 |
| content_hash | VARCHAR(64) | ✓ | - | 内容哈希 |
| text_content | TEXT | ✗ | NULL | 文本内容 |
| doc_metadata | JSON | ✓ | {} | 文档元数据 |
| knowledge_base_id | VARCHAR(36) | ✓ | - | 所属知识库ID，外键→knowledge_bases.id |
| processing_status | VARCHAR(20) | ✓ | 'pending' | 处理状态 |
| processing_error | TEXT | ✗ | NULL | 处理错误信息 |
| is_vectorized | BOOLEAN | ✓ | FALSE | 是否已向量化 |
| chunk_count | INTEGER | ✓ | 0 | 分块数量 |
| is_active | BOOLEAN | ✓ | TRUE | 是否激活 |
| created_at | DATETIME | ✓ | 当前时间 | 创建时间 |
| updated_at | DATETIME | ✓ | 当前时间 | 更新时间 |
| processed_at | DATETIME | ✗ | NULL | 处理时间 |

**依赖关系：**
- 外键：knowledge_base_id → knowledge_bases.id (多对一)
- 反向关系：chunks (一对多)

#### 2.3 document_chunks - 文档分块表 ✅ **核心表**
| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | VARCHAR(36) | ✓ | uuid | 主键 |
| document_id | VARCHAR(36) | ✓ | - | 所属文档ID，外键→documents.id |
| chunk_index | INTEGER | ✓ | - | 分块索引 |
| content | TEXT | ✓ | - | 分块内容 |
| content_hash | VARCHAR(64) | ✓ | - | 内容哈希 |
| chunk_metadata | JSON | ✓ | {} | 分块元数据 |
| embedding | JSON | ✗ | NULL | 向量嵌入 |
| created_at | DATETIME | ✓ | 当前时间 | 创建时间 |

**依赖关系：**
- 外键：document_id → documents.id (多对一)

### 3. 对话系统 (Conversation System)

#### 3.1 conversations - 对话表 ✅ **核心表**
| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | VARCHAR(36) | ✓ | uuid | 主键 |
| title | VARCHAR(200) | ✓ | '新对话' | 对话标题 |
| user_id | VARCHAR(36) | ✓ | - | 用户ID，外键→users.id |
| knowledge_base_id | VARCHAR(36) | ✗ | NULL | 关联知识库ID，外键→knowledge_bases.id |
| model_name | VARCHAR(50) | ✓ | 'deepseek-chat' | AI模型名称 |
| system_prompt | TEXT | ✗ | NULL | 系统提示词 |
| temperature | FLOAT | ✓ | 0.7 | 随机性参数 |
| max_tokens | INTEGER | ✓ | 2000 | 最大token数 |
| message_count | INTEGER | ✓ | 0 | 消息数量 |
| total_tokens | INTEGER | ✓ | 0 | 总token消耗 |
| is_active | BOOLEAN | ✓ | TRUE | 是否激活 |
| created_at | DATETIME | ✓ | 当前时间 | 创建时间 |
| updated_at | DATETIME | ✓ | 当前时间 | 更新时间 |

**依赖关系：**
- 外键：user_id → users.id (多对一)
- 外键：knowledge_base_id → knowledge_bases.id (多对一，可选)
- 反向关系：messages (一对多)

#### 3.2 messages - 消息表 ✅ **核心表**
| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | VARCHAR(36) | ✓ | uuid | 主键 |
| conversation_id | VARCHAR(36) | ✓ | - | 所属对话ID，外键→conversations.id |
| role | VARCHAR(20) | ✓ | - | 角色（user/assistant/system） |
| content | TEXT | ✓ | - | 消息内容 |
| msg_metadata | JSON | ✓ | {} | 消息元数据 |
| token_count | INTEGER | ✗ | NULL | token数量 |
| used_knowledge_base | BOOLEAN | ✓ | FALSE | 是否使用知识库 |
| relevant_chunks | JSON | ✗ | NULL | 相关文档块ID列表 |
| created_at | DATETIME | ✓ | 当前时间 | 创建时间 |

**依赖关系：**
- 外键：conversation_id → conversations.id (多对一)

### 4. 社区功能 (Community System)

#### 4.1 community_posts - 社区帖子表 ⚠️ **需要修复**
| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | ✓ | 自增 | 主键 |
| user_id | INTEGER | ✓ | - | ⚠️ **类型不匹配**：应为VARCHAR(36) |
| content | TEXT | ✓ | - | 帖子内容 |
| ai_prompt | TEXT | ✗ | NULL | AI提示词 |
| ai_content_type | VARCHAR(12) | ✗ | NULL | AI内容类型 |
| ai_content_data | JSON | ✗ | NULL | AI内容数据 |
| conversation_id | INTEGER | ✗ | NULL | ⚠️ **类型不匹配**：应为VARCHAR(36) |
| pdf_url | VARCHAR(255) | ✗ | NULL | PDF文件URL |
| tags | JSON | ✗ | NULL | 标签 |
| is_featured | BOOLEAN | ✗ | FALSE | 是否精选 |
| status | VARCHAR(9) | ✗ | 'published' | 状态 |
| like_count | INTEGER | ✗ | 0 | 点赞数 |
| comment_count | INTEGER | ✗ | 0 | 评论数 |
| share_count | INTEGER | ✗ | 0 | 分享数 |
| view_count | INTEGER | ✗ | 0 | 浏览数 |
| created_at | DATETIME | ✗ | 当前时间 | 创建时间 |
| updated_at | DATETIME | ✗ | 当前时间 | 更新时间 |

**问题说明：**
- user_id和conversation_id定义为INTEGER，但实际存储UUID字符串
- 由于SQLite弱类型特性，目前能正常工作，但设计不规范

#### 4.2 community_interactions - 社区互动表 ⚠️ **需要修复**
| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | ✓ | 自增 | 主键 |
| user_id | INTEGER | ✓ | - | ⚠️ **类型不匹配**：应为VARCHAR(36) |
| post_id | INTEGER | ✓ | - | 帖子ID |
| interaction_type | VARCHAR(8) | ✓ | - | 互动类型 |
| content | TEXT | ✗ | NULL | 评论内容 |
| created_at | DATETIME | ✗ | 当前时间 | 创建时间 |

#### 4.3 user_follows - 用户关注表 ⚠️ **需要修复**
| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | ✓ | 自增 | 主键 |
| follower_id | INTEGER | ✓ | - | ⚠️ **类型不匹配**：应为VARCHAR(36) |
| following_id | INTEGER | ✓ | - | ⚠️ **类型不匹配**：应为VARCHAR(36) |
| created_at | DATETIME | ✗ | 当前时间 | 创建时间 |

**相关功能模块：**
- 社区服务 (`app/services/community_service.py`)
- 社区API (`app/routes/community_api.py`)
- 管理员社区管理 (`app/routes/admin.py`)

## 数据表使用统计

| 表名 | 数据量 | 状态 | 建议 |
|------|--------|------|------|
| users | 多条 | ✅ 正常使用 | 保留 |
| knowledge_bases | 多条 | ✅ 正常使用 | 保留 |
| documents | 多条 | ✅ 正常使用 | 保留 |
| document_chunks | 多条 | ✅ 正常使用 | 保留 |
| conversations | 多条 | ✅ 正常使用 | 保留 |
| messages | 多条 | ✅ 正常使用 | 保留 |
| community_posts | 9条 | ⚠️ 类型不匹配 | 修复类型 |
| community_interactions | 0条 | ⚠️ 类型不匹配 | 修复类型 |
| user_follows | 0条 | ⚠️ 类型不匹配 | 修复类型 |


## 数据库清理建议


### 需要修复的表：
1. **community_posts** - user_id和conversation_id字段类型需要修改为VARCHAR(36)
2. **community_interactions** - user_id字段类型需要修改为VARCHAR(36)
3. **user_follows** - follower_id和following_id字段类型需要修改为VARCHAR(36)

## 功能模块映射

| 功能模块 | 相关表 | 主要文件 |
|----------|--------|----------|
| 用户认证 | users | `app/auth/routes.py` |
| 知识库管理 | knowledge_bases, documents, document_chunks | `app/models/knowledge_base.py` |
| 对话系统 | conversations, messages | `app/routes/chat.py` |
| 社区功能 | community_posts, community_interactions, user_follows | `app/services/community_service.py` |
| 管理后台 | 所有表 | `app/routes/admin.py` |
| 头像管理 | users.avatar_url | `app/utils/file_utils.py` |
| 权限控制 | users.role, users.disabled, users.deleted | `app/decorators.py` |

## 索引优化建议

当前数据库已有的索引：
- users.username (唯一)
- users.email (唯一)  
- users.id (主键)
- knowledge_bases.user_id
- documents.knowledge_base_id
- documents.content_hash
- document_chunks.document_id
- document_chunks.content_hash
- conversations.user_id
- conversations.knowledge_base_id
- messages.conversation_id

建议添加的索引：
- users.role (用于角色筛选)
- users.created_at (用于注册时间排序)
- community_posts.user_id (修复类型后)
- community_posts.created_at (用于时间排序)
- community_interactions.user_id (修复类型后)
- community_interactions.post_id (用于帖子互动查询)

---

**最后更新时间：** 2024年12月
**文档版本：** 1.0
**数据库版本：** SQLite 3.x 