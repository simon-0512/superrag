# 思维导图功能增强说明

## 新增功能概述

为现有的思维导图画板系统增加了主题定制、配色方案和形状设置功能，提升用户的个性化体验和视觉效果。

## 主要功能

### 1. 主题设置系统
- **预设主题**：提供6种精心设计的主题
  - 默认主题：经典蓝色配色
  - 海洋主题：蓝绿色海洋风格
  - 森林主题：绿色自然风格
  - 日落主题：橙红色温暖风格
  - 极简主题：灰色简约风格
  - 暗色主题：深色护眼风格

- **自定义配色**：
  - 主节点颜色调整
  - 子节点颜色调整
  - 连接线颜色调整
  - 背景颜色调整
  - 网格显示开关

### 2. 形状定制系统
- **节点形状选择**：
  - 圆角矩形（默认）
  - 圆形
  - 方形
  - 菱形
  - 六边形

- **连接线样式**：
  - 曲线连接（默认）
  - 直线连接
  - 直角连接

- **尺寸调整**：
  - 节点大小滑块控制（80px-200px）
  - 连接线粗细调整（1px-5px）

### 3. 用户界面改进
- **浮动工具栏增强**：
  - 添加主题设置按钮（调色板图标）
  - 添加形状设置按钮（形状图标）
  - 工具栏分隔符优化布局

- **模态框设计**：
  - 主题设置面板：预设主题预览、自定义颜色选择器
  - 形状设置面板：形状选项网格、连接线样式选择
  - 实时预览效果

## 技术实现

### 前端技术
- **CSS样式系统**：使用CSS变量实现主题切换
- **JavaScript交互**：Bootstrap模态框和事件处理
- **响应式设计**：网格布局适配不同屏幕

### 核心函数
1. `showThemePanel()` - 显示主题设置面板
2. `showShapePanel()` - 显示形状设置面板
3. `applyTheme(themeName)` - 应用预设主题
4. `applyCustomTheme()` - 应用自定义主题配色
5. `applyThemeToCanvas(theme)` - 将主题应用到画布
6. `selectNodeShape(shape)` - 选择节点形状
7. `selectConnectionStyle(style)` - 选择连接线样式
8. `applyShapeSettings()` - 应用形状设置

### 数据结构
```javascript
// 主题配置对象
const themes = {
    default: {
        primaryColor: '#007bff',
        secondaryColor: '#6c757d',
        connectionColor: '#495057',
        backgroundColor: '#ffffff'
    },
    // ... 其他主题配置
};
```

## 使用指南

### 访问入口
- 通过侧边栏导航：「思维导图」菜单项
- 直接访问：`/mindmap/` 路径

### 主题设置操作
1. 点击浮动工具栏中的调色板图标
2. 选择预设主题或自定义配色
3. 实时预览效果
4. 点击「应用」按钮确认设置

### 形状设置操作
1. 点击浮动工具栏中的形状图标
2. 选择节点形状和连接线样式
3. 调整节点大小和连接线粗细
4. 点击「应用」按钮确认设置

## 扩展性设计

### 主题扩展
- 可轻松添加新的预设主题
- 支持主题配置的持久化存储
- 可实现主题导入/导出功能

### 形状扩展
- 节点形状系统支持CSS和SVG扩展
- 连接线样式可通过CSS类扩展
- 支持自定义形状和动画效果

## 未来规划

1. **主题商店**：提供更多精美主题下载
2. **协作模式**：多人同时编辑思维导图
3. **模板系统**：预设思维导图模板
4. **导出增强**：支持更多格式导出
5. **AI集成**：智能节点推荐和布局优化

## 技术亮点

- **实时预览**：颜色和形状变化即时可见
- **用户友好**：直观的图形化设置界面
- **性能优化**：CSS变量和类切换，避免重复渲染
- **兼容性强**：基于标准Web技术，浏览器兼容性好 