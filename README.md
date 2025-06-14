# WealthLite

WealthLite 是一款面向个人用户的轻量级资产分类与投资回报管理工具，支持本地数据加密存储、年化回报率计算、资产变动追踪及多种导出方式。

## 🎯 项目特色

- **轻量级设计**：零数据库依赖，使用CSV/JSON文件存储
- **离线运行**：完全本地化，无需网络连接
- **数据安全**：AES-256加密存储，密钥本地管理
- **绿色版分发**：单文件EXE，解压即用
- **专业计算**：精确的年化回报率计算引擎
- **分类管理**：预定义5大资产类别，支持自定义扩展

## 📊 主要功能

### 资产分类管理
- **现金及等价物**：活期存款、货币基金、短期理财
- **固定收益类**：定期存款、国债、企业债、债券基金
- **权益类**：股票、股票型基金、ETF
- **不动产**：住宅、商铺、REITs
- **大宗商品**：贵金属等

### 投资数据记录
- 投入时间记录（精确到日）
- 初始投入金额与当前价值
- 资产变动历史追踪
- 支持批量导入/导出

### 回报率计算引擎
- 实时年化回报率计算
- 分类回报率统计
- 持有期收益可视化
- 多维度数据分析

### 数据安全与导出
- 本地加密存储
- Excel导出功能
- 数据备份与恢复
- 跨设备数据迁移

## 🛠 技术栈

| 模块 | 技术选型 | 说明 |
|------|----------|------|
| **开发语言** | Python 3.12 | 高效开发，易于维护 |
| **GUI框架** | Tkinter | 零依赖，内置GUI库 |
| **数据存储** | CSV + JSON | 轻量级，易于迁移 |
| **Excel导出** | XlsxWriter | 轻量级Excel生成 |
| **数据加密** | cryptography | AES-256加密 |
| **打包工具** | PyInstaller | 生成绿色版EXE |
| **可视化** | matplotlib | 简单图表绘制 |

## 📁 项目结构

```text
wealth_lite/
├── docs/                           # 项目文档
│   ├── DEVELOPMENT_PLAN.md         # 开发计划
│   ├── work_log.md                 # 工作日志
│   ├── index.md                    # 文档索引
│   ├── design/                     # 详细设计文档
│   ├── api/                        # API文档
│   └── guides/                     # 用户指南
├── src/                            # 源代码
│   ├── main.py                     # 主程序入口
│   ├── models/                     # 数据模型
│   ├── gui/                        # 图形界面
│   ├── data/                       # 数据处理
│   ├── utils/                      # 工具函数
│   └── config/                     # 配置文件
├── tests/                          # 测试用例
│   ├── unit/                       # 单元测试
│   └── integration/                # 集成测试
├── data/                           # 数据文件目录
├── dist/                           # 打包输出目录
├── requirements.txt                # 依赖列表
├── environment.yml                 # Conda环境配置
└── README.md                       # 项目说明（本文件）
```

## 🚀 快速开始

### 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd wealth_lite

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖（使用清华镜像）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 启动应用程序
```bash
# 方式1：使用启动脚本（推荐）
python run_wealthlite.py

# 方式2：直接运行主程序
python src/main.py

# 方式3：运行演示脚本
python demo_storage.py
```

### 开发运行
```bash
# 运行测试
pytest tests/

# 代码格式化
black src/ tests/

# 静态检查
flake8 src/ tests/
mypy src/
```

### 打包分发
```bash
# 打包为EXE
pyinstaller --onefile --noconfirm --clean \
    --distpath ./dist --workpath ./build \
    --exclude-module pandas --exclude-module numpy \
    --add-data "data;data" \
    --name WealthLite \
    src/main.py
```

## 📈 开发进度

### ✅ 已完成
- [x] 项目初始化和文档体系建立
- [x] 详细需求分析和技术选型
- [x] 开发计划制定和环境配置
- [x] 核心数据模型实现（Asset、Category类）
- [x] CSV/JSON数据存储系统
- [x] 年化回报率计算引擎
- [x] 资产管理器和工具函数库
- [x] 完整的单元测试覆盖（43个测试用例）
- [x] GUI图形界面开发
- [x] 资产列表、表单、主窗口组件
- [x] Excel导出和数据备份功能

### 🔄 进行中（第二阶段：界面优化）
- [x] 基础GUI界面实现
- [ ] 界面美化和用户体验优化
- [ ] 数据可视化图表
- [ ] 高级搜索和筛选功能

### 📋 待开发
- **第三阶段**：增强功能（数据加密、批量导入等，1-2周）
- **第四阶段**：打包与分发（1周）

## 🖥️ GUI界面功能

### 主要功能
- **资产管理**：新建、编辑、删除资产
- **数据展示**：资产列表、详情面板、投资组合摘要
- **数据操作**：搜索、排序、Excel导出、数据备份
- **分类管理**：5大资产类别，14个二级分类

### 界面布局
- **菜单栏**：文件、编辑、帮助菜单
- **工具栏**：常用操作按钮和搜索框
- **主内容区**：
  - 左侧：资产列表（支持排序和搜索）
  - 右侧：资产详情和投资组合摘要
- **状态栏**：显示操作状态和资产数量

### 键盘快捷键
- `Ctrl+N`：新建资产
- `Ctrl+E`：编辑资产
- `Ctrl+Q`：退出应用
- `F5`：刷新数据
- `Delete`：删除资产

## 📚 文档入口

- [开发计划](docs/DEVELOPMENT_PLAN.md) - 详细的开发规划和技术方案
- [工作日志](docs/work_log.md) - 开发进展和重要决策记录
- [文档索引](docs/index.md) - 完整文档导航

## 🔧 开发规范

- **代码风格**：使用black格式化，遵循PEP8规范
- **命名规范**：文件/目录使用snake_case，类名使用PascalCase
- **测试覆盖**：单元测试覆盖率≥80%
- **文档规范**：Google风格docstring，markdown格式文档

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

**项目状态**：🚧 开发中 | **当前版本**：v0.1.0-dev | **预计发布**：6-9周后 