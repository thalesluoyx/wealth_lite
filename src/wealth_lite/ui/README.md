# WealthLite UI 开发文档

基于轻量化原生Web技术栈的个人财富管理界面。

## 📁 目录结构

- `app/`：正式开发的前端代码（主业务UI、静态资源、组件、样式等）。
- `demo/`：仅供UI风格、交互、实验参考的演示代码，不参与主业务打包和部署。
- `docs/`：开发文档目录（如API文档等）。
- `dist/`：构建输出目录（自动生成，生产部署用）。
- `build.py`：构建脚本（以app为源码，输出到dist）。
- `serve.py`：本地开发服务器。
- `package.json`：前端依赖说明。
- `README.md`：本说明文档。

## 📂 目录作用详解

#### `app/` - 正式开发源码目录
- **用途**: 存放所有正式开发的源代码
- **结构**: 按功能模块组织（js、styles、components、assets、dev-tools）
- **特点**: 开发环境的工作目录，主业务UI全部在此
- **启动**: `python serve.py` (服务于app目录)

#### `demo/` - 演示和原型目录
- **用途**: 存放所有演示代码和原型文件
- **内容**: demo_modules.html、demo.html、stagewise_demo.html、test_stagewise.html、stagewise-toolbar.js、start_demo.py等
- **特点**: 独立运行，不影响正式开发
- **启动**: `cd demo && python start_demo.py`

#### `dist/` - 构建输出目录
- **用途**: 存放构建后的生产代码
- **生成**: 运行 `python build.py` 自动生成（以app为源码）
- **特点**: 代码经过合并、压缩、优化
- **部署**: 直接部署dist目录内容

#### `docs/` - 开发文档目录
- **用途**: 存放项目开发相关文档
- **内容**: API文档、组件文档、部署指南等
- **维护**: 随代码更新同步维护

#### 其它
- `build.py`：构建脚本，**以app/为源码目录**，输出到dist/
- `serve.py`：本地开发服务器，默认服务app/目录
- `package.json`：前端依赖说明

## 🛠️ 技术栈

- **HTML5**: 语义化标记
- **CSS3**: 原生CSS + CSS变量
- **JavaScript ES6+**: 原生JavaScript，面向对象设计
- **Chart.js**: 图表可视化库
- **Lucide Icons**: 现代SVG图标库
- **Stagewise Toolbar**: 开发调试工具（仅开发环境）

## 🚀 快速开始

### 开发环境启动
```bash
# 启动开发服务器
cd ui
python serve.py
# 浏览器自动打开 http://localhost:8000
```

### 查看演示
```bash
# 启动演示服务器
cd ui/demo
python start_demo.py
# 浏览器打开 http://localhost:8080
```

### 构建生产版本
```bash
# 构建到dist目录
cd ui
python build.py
# 注意：生产版本不包含开发工具
```

## 📝 开发规范

- **正式业务代码全部放在 `app/` 目录下**，构建、部署、静态服务只处理 `app/`。
- **`demo/` 目录仅供开发者参考**，禁止主业务代码 import/require 任何 demo 目录下内容。
- 如需参考 demo 风格，可复制相关片段到 `app/`，但请勿直接依赖 demo 代码。

## 目录示例

```
ui/
  ├─ app/      # 正式开发代码
  ├─ demo/     # 仅供参考的演示代码
  ├─ docs/     # 文档
  ├─ dist/     # 构建输出
  ├─ build.py
  ├─ serve.py
  ├─ package.json
  └─ README.md
```

---

如需调整目录结构或有其它需求，请联系维护者。

## 🎨 设计系统

### 色彩系统
```css
:root {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --accent-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  --success: #10b981;
  --danger: #ef4444;
  --warning: #f59e0b;
  --info: #3b82f6;
}
```

### 布局系统
- **网格布局**: CSS Grid + Flexbox
- **响应式断点**: 768px (移动端) / 1200px (桌面端)
- **间距系统**: 基于1rem的间距单位

## 📊 组件库

### 基础组件
- **Button**: 按钮组件
- **Card**: 卡片容器
- **Table**: 数据表格
- **Form**: 表单组件

### 业务组件
- **Dashboard**: 仪表板组件
- **AssetList**: 资产列表
- **TransactionForm**: 交易表单
- **ChartWidget**: 图表组件

## 🔧 构建配置

### 开发模式
- **热重载**: 文件变更自动刷新
- **源码映射**: 便于调试
- **开发工具**: Stagewise工具栏集成

### 生产模式
- **代码压缩**: JS/CSS文件压缩
- **资源优化**: 图片和字体优化
- **缓存策略**: 文件指纹和缓存控制

## 📱 浏览器支持

### 现代浏览器
- Chrome 76+
- Firefox 103+
- Safari 9+
- Edge 79+

### 优雅降级
- 毛玻璃效果回退
- CSS Grid回退到Flexbox
- 现代JavaScript特性检测

## 🚀 部署方案

### 本地应用
- Python HTTP服务器
- PyInstaller单文件打包
- 跨平台支持

### Web部署
- 静态文件托管
- CDN资源加速
- Service Worker离线支持

---

## 📞 联系方式

如有问题或建议，请参考项目文档或提交Issue。 