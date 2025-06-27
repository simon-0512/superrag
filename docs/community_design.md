# SuperRAG 社区功能设计文档

## 🌟 功能概述

SuperRAG社区是一个专注于AI创作内容分享的社交平台，采用简洁清爽的时间流设计，让用户能够轻松分享和发现优质的AI创作内容。

## 📱 核心功能模块

### 1. 内容分享 (Content Sharing)

#### 1.1 分享内容类型
- **文字分享**: 用户原创文字(140字以内) + AI创作内容
- **对话分享**: 完整或部分对话记录分享
- **PDF分享**: 导出的知识总结PDF文档
- **提示词分享**: 优质的AI提示词模板

#### 1.2 分享组件结构
```
┌─────────────────────────────────────┐
│ 👤 用户头像 + 昵称 + 时间戳         │
├─────────────────────────────────────┤
│ 📝 用户文字描述 (≤140字)           │
├─────────────────────────────────────┤
│ 🤖 AI提示词 (可折叠显示)           │
├─────────────────────────────────────┤
│ ✨ AI创作内容                      │
│   - 对话内容/PDF预览/创作结果       │
├─────────────────────────────────────┤
│ 🏷️ 标签: #AI创作 #提示词 #知识分享 │
├─────────────────────────────────────┤
│ 💬 互动区: 👍点赞 💬评论 🔄转发 ⭐收藏 │
└─────────────────────────────────────┘
```

### 2. 时间流展示 (Timeline Feed)

#### 2.1 多种浏览模式
- **推荐流**: 基于用户兴趣的智能推荐
- **关注流**: 关注用户的最新分享
- **热门流**: 高互动量的优质内容
- **分类流**: 按内容类型筛选(创作/提示词/知识等)

#### 2.2 UI设计原则
- **极简风格**: 大量留白，重点突出内容
- **卡片布局**: 每条分享独立卡片设计
- **渐进加载**: 无限滚动 + 骨架屏
- **响应式**: 适配移动端和桌面端

### 3. 内容创作工具 (Creation Tools)

#### 3.1 分享编辑器
```
┌─────────────────────────────────────┐
│ 📝 分享你的AI创作...                │
├─────────────────────────────────────┤
│ [文字描述输入框] (140字倒计时)       │
├─────────────────────────────────────┤
│ [+ 添加提示词] [+ 选择对话] [+ 上传PDF] │
├─────────────────────────────────────┤
│ [预览] [保存草稿] [立即发布]        │
└─────────────────────────────────────┘
```

#### 3.2 内容导入功能
- **对话导入**: 从聊天记录中选择精彩片段
- **PDF导入**: 上传知识总结文档
- **提示词库**: 内置优质提示词模板
- **草稿保存**: 未完成的分享自动保存

### 4. 用户系统 (User System)

#### 4.1 用户档案
- **基础信息**: 头像、昵称、个人简介
- **创作统计**: 分享数、获赞数、粉丝数
- **专业标签**: AI研究者、创作者、学习者等
- **成就系统**: 创作达人、提示词专家等徽章

#### 4.2 社交关系
- **关注/粉丝**: 建立用户连接
- **好友系统**: 私信和深度交流
- **兴趣圈子**: 按主题聚集的用户群体

## 🏗️ 技术架构设计

### 数据库设计

#### 5.1 核心数据表

**用户表扩展 (users)**
```sql
ALTER TABLE users ADD COLUMN (
    nickname VARCHAR(50),           -- 昵称
    avatar_url VARCHAR(255),        -- 头像URL
    bio TEXT,                       -- 个人简介
    follower_count INT DEFAULT 0,   -- 粉丝数
    following_count INT DEFAULT 0,  -- 关注数
    post_count INT DEFAULT 0,       -- 分享数
    like_count INT DEFAULT 0,       -- 获赞总数
    badges JSON,                    -- 成就徽章
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**社区帖子表 (community_posts)**
```sql
CREATE TABLE community_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,              -- 用户文字描述(≤140字)
    ai_prompt TEXT,                     -- AI提示词(可选)
    ai_content_type ENUM('conversation', 'pdf', 'text'), -- AI内容类型
    ai_content_data JSON,               -- AI内容数据
    conversation_id INTEGER,            -- 关联的对话ID
    pdf_url VARCHAR(255),              -- PDF文件URL
    tags JSON,                         -- 标签数组
    is_featured BOOLEAN DEFAULT FALSE, -- 是否精选
    like_count INT DEFAULT 0,          -- 点赞数
    comment_count INT DEFAULT 0,       -- 评论数
    share_count INT DEFAULT 0,         -- 转发数
    view_count INT DEFAULT 0,          -- 浏览数
    status ENUM('draft', 'published', 'hidden') DEFAULT 'published',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

**互动表 (community_interactions)**
```sql
CREATE TABLE community_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    interaction_type ENUM('like', 'comment', 'share', 'bookmark'),
    content TEXT,                       -- 评论内容(comment类型)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (post_id) REFERENCES community_posts(id),
    UNIQUE(user_id, post_id, interaction_type) -- 防重复点赞等
);
```

**关注关系表 (user_follows)**
```sql
CREATE TABLE user_follows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    follower_id INTEGER NOT NULL,      -- 关注者ID
    following_id INTEGER NOT NULL,     -- 被关注者ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (follower_id) REFERENCES users(id),
    FOREIGN KEY (following_id) REFERENCES users(id),
    UNIQUE(follower_id, following_id)
);
```

### API设计

#### 5.2 核心API接口

**社区帖子相关**
```python
# 获取时间流
GET /api/community/feed?type=recommended&page=1&limit=20

# 发布帖子
POST /api/community/posts
{
    "content": "今天用AI写了一首诗...",
    "ai_prompt": "请写一首关于春天的诗",
    "ai_content_type": "conversation", 
    "conversation_id": 123,
    "tags": ["poetry", "ai-creation"]
}

# 获取帖子详情
GET /api/community/posts/{post_id}

# 编辑帖子
PUT /api/community/posts/{post_id}

# 删除帖子
DELETE /api/community/posts/{post_id}
```

**互动相关**
```python
# 点赞/取消点赞
POST /api/community/posts/{post_id}/like

# 评论
POST /api/community/posts/{post_id}/comments
{
    "content": "很棒的分享！"
}

# 转发
POST /api/community/posts/{post_id}/share
{
    "content": "推荐给大家"  # 可选转发语
}

# 收藏
POST /api/community/posts/{post_id}/bookmark
```

**用户相关**
```python
# 关注用户
POST /api/community/users/{user_id}/follow

# 获取用户主页
GET /api/community/users/{user_id}/profile

# 获取用户帖子
GET /api/community/users/{user_id}/posts?page=1&limit=20
```

## 🎨 前端实现设计

### 6.1 页面结构

**社区主页 (community.html)**
```html
<div class="community-container">
    <!-- 顶部导航 -->
    <nav class="community-nav">
        <div class="nav-tabs">
            <button class="tab active" data-feed="recommended">推荐</button>
            <button class="tab" data-feed="following">关注</button>
            <button class="tab" data-feed="trending">热门</button>
            <button class="tab" data-feed="categories">分类</button>
        </div>
        <button class="create-post-btn">+ 分享创作</button>
    </nav>
    
    <!-- 内容区域 -->
    <div class="community-content">
        <!-- 左侧时间流 -->
        <div class="feed-container">
            <div id="posts-container"></div>
            <div class="loading-indicator">加载中...</div>
        </div>
        
        <!-- 右侧信息栏 -->
        <div class="sidebar">
            <div class="trending-topics">热门话题</div>
            <div class="recommended-users">推荐关注</div>
            <div class="quick-actions">快捷操作</div>
        </div>
    </div>
</div>
```

### 6.2 核心组件

**帖子卡片组件**
```javascript
class PostCard {
    constructor(postData) {
        this.data = postData;
        this.element = this.render();
    }
    
    render() {
        return `
            <div class="post-card" data-post-id="${this.data.id}">
                <div class="post-header">
                    <img src="${this.data.user.avatar}" class="user-avatar">
                    <div class="user-info">
                        <span class="username">${this.data.user.nickname}</span>
                        <span class="timestamp">${this.formatTime(this.data.created_at)}</span>
                    </div>
                </div>
                
                <div class="post-content">
                    <p class="user-description">${this.data.content}</p>
                    ${this.renderAIContent()}
                    <div class="post-tags">
                        ${this.data.tags.map(tag => `<span class="tag">#${tag}</span>`).join('')}
                    </div>
                </div>
                
                <div class="post-actions">
                    <button class="action-btn like-btn" data-count="${this.data.like_count}">
                        <i class="bi bi-heart"></i> ${this.data.like_count}
                    </button>
                    <button class="action-btn comment-btn" data-count="${this.data.comment_count}">
                        <i class="bi bi-chat"></i> ${this.data.comment_count}
                    </button>
                    <button class="action-btn share-btn" data-count="${this.data.share_count}">
                        <i class="bi bi-share"></i> ${this.data.share_count}
                    </button>
                    <button class="action-btn bookmark-btn">
                        <i class="bi bi-bookmark"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    renderAIContent() {
        switch(this.data.ai_content_type) {
            case 'conversation':
                return this.renderConversation();
            case 'pdf':
                return this.renderPDF();
            case 'text':
                return this.renderText();
            default:
                return '';
        }
    }
}
```

### 6.3 样式设计 (CSS)

**极简卡片样式**
```css
.post-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border: 1px solid #f0f0f0;
    transition: all 0.2s ease;
}

.post-card:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    transform: translateY(-1px);
}

.post-content {
    margin: 16px 0;
    line-height: 1.6;
}

.user-description {
    font-size: 16px;
    color: #333;
    margin-bottom: 12px;
}

.ai-content {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 16px;
    margin: 12px 0;
    border-left: 4px solid #007bff;
}

.post-actions {
    display: flex;
    gap: 24px;
    padding-top: 12px;
    border-top: 1px solid #f0f0f0;
}

.action-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    background: none;
    border: none;
    color: #666;
    cursor: pointer;
    transition: color 0.2s ease;
}

.action-btn:hover {
    color: #007bff;
}

.action-btn.active {
    color: #007bff;
}
```

## 🚀 功能扩展规划

### 7.1 近期功能 (Phase 1)
- ✅ 基础分享功能
- ✅ 时间流展示
- ✅ 基础互动(点赞、评论)
- ✅ 用户关注系统

### 7.2 中期功能 (Phase 2)
- 🔄 AI创作大赛模块
- 🔄 提示词库和评分
- 🔄 知识专题和合集
- 🔄 用户等级和成就系统

### 7.3 长期功能 (Phase 3)
- 🔮 AI助手推荐优质内容
- 🔮 跨平台内容同步
- 🔮 付费优质内容订阅
- 🔮 创作者激励计划

## 📊 运营策略

### 8.1 内容质量保障
- **智能审核**: AI自动检测低质量内容
- **人工精选**: 运营团队筛选优质内容
- **用户举报**: 社区自治机制
- **创作指南**: 分享最佳实践

### 8.2 用户成长体系
- **新手引导**: 帮助用户快速上手
- **创作激励**: 优质内容获得更多曝光
- **专家认证**: 专业用户认证体系
- **社区活动**: 定期举办创作比赛

这个社区功能将成为SuperRAG平台的重要组成部分，为用户提供一个展示和发现AI创作内容的优质平台！ 