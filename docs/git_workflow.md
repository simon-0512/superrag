# SuperRAG Git工作流指南

## 分支策略

### 主要分支
- **main**: 生产环境分支，保持稳定可发布状态
- **develop**: 开发主分支，集成最新的开发特性

### 功能分支
- **feature/**: 新功能开发分支
- **bugfix/**: Bug修复分支
- **hotfix/**: 紧急修复分支

## 工作流程

### 1. 功能开发
```bash
# 从develop分支创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/new-feature

# 开发完成后合并回develop
git checkout develop
git merge feature/new-feature
git push origin develop
git branch -d feature/new-feature
```

### 2. Bug修复
```bash
# 从develop分支创建修复分支
git checkout develop
git checkout -b bugfix/fix-issue

# 修复完成后合并回develop
git checkout develop
git merge bugfix/fix-issue
git push origin develop
git branch -d bugfix/fix-issue
```

### 3. 发布流程
```bash
# 从develop创建发布分支
git checkout develop
git checkout -b release/v1.0.0

# 完成发布准备后合并到main
git checkout main
git merge release/v1.0.0
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin main --tags

# 同时合并回develop
git checkout develop
git merge release/v1.0.0
git branch -d release/v1.0.0
```

### 4. 紧急修复
```bash
# 从main分支创建热修复分支
git checkout main
git checkout -b hotfix/critical-fix

# 修复完成后合并到main和develop
git checkout main
git merge hotfix/critical-fix
git tag -a v1.0.1 -m "Hotfix version 1.0.1"
git push origin main --tags

git checkout develop
git merge hotfix/critical-fix
git branch -d hotfix/critical-fix
```

## 提交规范

### 提交消息格式
```
<类型>(<范围>): <描述>

[可选的正文]

[可选的脚注]
```

### 类型标识
- `✨ feat`: 新功能
- `🐛 fix`: Bug修复
- `📝 docs`: 文档更新
- `💄 style`: 代码格式(不影响代码运行的变动)
- `♻️ refactor`: 重构(既不是新增功能，也不是修改bug的代码变动)
- `⚡️ perf`: 性能优化
- `✅ test`: 增加测试
- `🔧 chore`: 构建过程或辅助工具的变动
- `🔒 security`: 安全相关修复

### 示例提交消息
```bash
✨ feat(auth): 添加用户注册功能

实现了用户注册页面和后端验证逻辑
- 添加注册表单验证
- 实现密码强度检查
- 集成邮箱验证功能

Closes #123
```

## 版本标签

### 版本号规范
采用语义化版本控制 (Semantic Versioning)：
- **主版本号**: 不兼容的API修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

### 标签创建
```bash
# 创建带注释的标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签到远程
git push origin --tags

# 查看所有标签
git tag -l
```

## 最佳实践

### 1. 提交频率
- 经常提交，保持每次提交的变更集合理小
- 每个提交应该是一个逻辑完整的变更
- 避免一次提交包含多个不相关的修改

### 2. 代码审查
- 所有合并到main的代码都应经过代码审查
- 功能分支合并前需要测试通过

### 3. 分支清理
- 及时删除已合并的功能分支
- 定期清理远程追踪的已删除分支

### 4. 冲突解决
```bash
# 拉取最新代码
git fetch origin

# 变基以保持线性历史
git rebase origin/develop

# 解决冲突后继续变基
git rebase --continue
```

## 项目状态

### 当前分支
- ✅ `main`: 生产环境分支
- ✅ `develop`: 开发主分支

### 最新版本
- v1.0.0: 初始版本发布 (待创建)

## 远程仓库配置

当需要推送到远程仓库时：
```bash
# 添加远程仓库
git remote add origin <repository-url>

# 首次推送
git push -u origin main
git push -u origin develop
``` 