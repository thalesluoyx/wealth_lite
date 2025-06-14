# WealthLite 开发计划

## 一、需求分析与拆解

### 核心功能需求

#### 1. 资产分类管理

**预定义分类体系**：

| **一级类别**   | **二级类别**         | **风险水平** | **预期收益** | **流动性** | **适用场景**    |
| ---------- | ---------------- | -------- | -------- | ------- | ----------- |
| **现金及等价物** | 活期存款、货币基金、短期理财   | 低        | 低        | 极高      | 应急储备、短期资金存放 |
| **固定收益类**  | 定期存款、国债、企业债、债券基金 | 中低       | 中低       | 中高      | 稳健保值、低波动需求  |
| **权益类**    | 股票、股票型基金、ETF     | 高        | 高        | 高       | 长期增值、承担较高风险 |
| **不动产**    | 住宅、商铺、REITs      | 中高       | 中高       | 低       | 抗通胀、长期资产配置  |
| **大宗商品**   | 贵金属              | 高        | 高        | 中       | 对冲通胀、分散风险   |

**功能要求**：
- 支持预定义分类体系的完整实现
- 支持自定义分类和标签扩展
- 分类属性可编辑（风险水平、预期收益、流动性、适用场景）
- 支持分类的增删改查操作

#### 2. 投资数据记录

**核心字段**：
- 投入时间记录（精确到日）
- 初始投入金额
- 当前价值（支持定期更新）
- 资产变动历史追踪

**功能要求**：
- 支持单笔资产录入、编辑、删除
- 支持批量导入/导出
- 历史变动记录（时间、类型、金额、备注）
- 支持资产转移、分红、增减等操作类型

#### 3. 回报率计算引擎

**核心公式**：
年化回报率 = (当前价值/初始投入)^(1/持有年数) - 1

**功能要求**：
- 实时年化回报率计算
- 分类回报率统计（按资产类型/自定义标签）
- 持有期收益可视化
- 支持多币种计算（扩展功能）
- 历史回测功能（可选）

#### 4. 数据安全与离线功能

**核心要求**：
- 本地数据库存储（CSV/JSON文件）
- 数据加密存储
- 无网络依赖设计
- 支持数据备份与恢复
- 支持数据迁移

## 二、技术选型与架构设计

### 技术选型建议

| **模块**         | **技术选型**                          | **理由**                                                                 |
|------------------|---------------------------------------|--------------------------------------------------------------------------|
| **开发语言**     | Python 3.12                          | Cursor 原生支持，开发效率高，适合个人项目                                |
| **前端框架**     | Tkinter（主选））    | Tkinter：零依赖，内置GUI库；               |
| **数据存储**     | CSV 文件 + JSON 文件                  | 无需数据库，直接文件读写，适合小数据量（<1000条记录）                     |
| **Excel 导出**   | XlsxWriter（主选）或 pandas（备选）    | XlsxWriter：轻量级；pandas：功能强大但依赖多                             |
| **打包工具**     | PyInstaller（主选）或 Nuitka（备选）   | PyInstaller：一键打包EXE，绿色版；Nuitka：编译为C代码，体积小             |
| **数据加密**     | cryptography 库                       | 提供AES加密，安全可靠                                                    |
| **可视化**       | matplotlib（可选）                    | 简单图表绘制                                                             |

### 核心代码示例

#### 年化回报率计算
```python
import math
from datetime import datetime

def calculate_annualized_return(initial, current, start_date):
    """计算年化回报率"""
    days = (datetime.now() - start_date).days
    if days <= 0:
        return 0
    years = days / 365.25
    return (current / initial) ** (1 / years) - 1
```

#### 资产录入界面（Tkinter）
```python
import tkinter as tk
from tkinter import ttk

def create_asset_form():
    """创建资产录入表单"""
    root = tk.Tk()
    root.title("资产录入")
    
    # 资产类型选择
    tk.Label(root, text="一级类别").pack()
    category1 = ttk.Combobox(root, values=["现金及等价物", "固定收益类", "权益类", "不动产", "大宗商品"])
    category1.pack()
    
    # 二级类别
    tk.Label(root, text="二级类别").pack()
    category2 = ttk.Combobox(root)
    category2.pack()
    
    # 投入金额
    tk.Label(root, text="初始投入金额").pack()
    amount = tk.Entry(root)
    amount.pack()
    
    # 投入日期
    tk.Label(root, text="投入日期").pack()
    date_entry = tk.Entry(root)
    date_entry.pack()
    
    return root
```

#### 数据存储（CSV）
```python
import csv
from datetime import datetime

def save_asset_data(asset_data):
    """保存资产数据到CSV"""
    with open("assets.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            asset_data["category1"],
            asset_data["category2"], 
            asset_data["initial_amount"],
            asset_data["current_value"],
            asset_data["start_date"],
            datetime.now().strftime("%Y-%m-%d")
        ])
```

#### Excel 导出（XlsxWriter）
```python
import xlsxwriter
from datetime import datetime

def export_to_excel(asset_list):
    """导出资产数据到Excel"""
    workbook = xlsxwriter.Workbook(f"资产统计_{datetime.now().strftime('%Y%m%d')}.xlsx")
    
    # 按分类创建不同Sheet
    categories = {}
    for asset in asset_list:
        cat = asset["category1"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(asset)
    
    for cat_name, assets in categories.items():
        worksheet = workbook.add_worksheet(cat_name)
        # 写入表头
        headers = ["二级类别", "初始金额", "当前价值", "年化回报率", "投入日期"]
        worksheet.write_row(0, 0, headers)
        
        # 写入数据
        for i, asset in enumerate(assets, 1):
            worksheet.write_row(i, 0, [
                asset["category2"],
                asset["initial_amount"],
                asset["current_value"],
                asset["annualized_return"],
                asset["start_date"]
            ])
    
    workbook.close()
```

## 三、项目结构与开发规范

### 目录结构
```text
wealth_lite/
├── docs/                           # 项目文档
│   ├── DEVELOPMENT_PLAN.md         # 开发计划（本文件）
│   ├── index.md                    # 文档索引
│   ├── design/                     # 详细设计文档
│   ├── api/                        # API文档
│   └── guides/                     # 用户指南
├── src/                            # 源代码
│   ├── main.py                     # 主程序入口
│   ├── models/                     # 数据模型
│   │   ├── __init__.py
│   │   ├── asset.py                # 资产数据模型
│   │   └── category.py             # 分类数据模型
│   ├── gui/                        # 图形界面
│   │   ├── __init__.py
│   │   ├── main_window.py          # 主窗口
│   │   ├── asset_form.py           # 资产录入表单
│   │   └── report_view.py          # 报表视图
│   ├── data/                       # 数据处理
│   │   ├── __init__.py
│   │   ├── storage.py              # 数据存储
│   │   ├── encryption.py           # 数据加密
│   │   └── export.py               # 数据导出
│   ├── utils/                      # 工具函数
│   │   ├── __init__.py
│   │   ├── calculator.py           # 回报率计算
│   │   └── validator.py            # 数据验证
│   └── config/                     # 配置文件
│       ├── __init__.py
│       └── settings.py             # 应用设置
├── tests/                          # 测试用例
│   ├── unit/                       # 单元测试
│   └── integration/                # 集成测试
├── data/                           # 数据文件目录
│   ├── assets.csv                  # 资产数据
│   ├── categories.json             # 分类配置
│   └── backups/                    # 备份文件
├── dist/                           # 打包输出目录
├── requirements.txt                # 依赖列表
├── environment.yml                 # Conda环境配置
├── .env.example                    # 环境变量示例
└── README.md                       # 项目说明
```

### 命名规范
- 文件/目录：snake_case
- 类名：PascalCase
- 函数/变量：snake_case
- 常量：UPPER_CASE

## 四、开发流程与阶段目标

### 第一阶段：核心功能实现
**目标**：实现基础的资产录入、存储和回报率计算
- [ ] 数据模型设计（Asset、Category类）
- [ ] CSV数据存储实现
- [ ] 年化回报率计算引擎
- [ ] 基础CLI界面
- [ ] 单元测试覆盖

### 第二阶段：图形界面开发
**目标**：实现完整的Tkinter图形界面
- [ ] 主窗口设计
- [ ] 资产录入表单
- [ ] 数据展示表格（ttk.Treeview）
- [ ] 分类管理界面
- [ ] 基础数据可视化

### 第三阶段：增强功能
**目标**：实现Excel导出、数据加密等高级功能
- [ ] Excel导出功能（XlsxWriter）
- [ ] 数据加密存储
- [ ] 数据备份与恢复
- [ ] 持有期收益图表（matplotlib）
- [ ] 批量导入/导出

### 第四阶段：打包与分发
**目标**：生成绿色版可执行文件
- [ ] PyInstaller打包配置
- [ ] 绿色版ZIP包制作
- [ ] 跨平台兼容性测试
- [ ] 用户文档编写

## 五、依赖管理与环境配置

### requirements.txt
```text
# 核心依赖
xlsxwriter==3.1.9
cryptography==41.0.7

# 可选依赖（可视化）
matplotlib==3.8.2

# 开发依赖
pytest==7.4.3
pytest-cov==4.1.0
black==23.11.0
flake8==6.1.0
mypy==1.7.1
```

### 安装命令（使用清华镜像）
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 六、数据安全与性能优化

### 数据安全措施
1. **本地加密存储**：使用AES-256加密敏感数据
2. **密钥管理**：本地生成和存储加密密钥
3. **数据备份**：定期自动备份到指定目录
4. **访问控制**：可选的启动密码保护

### 性能优化策略
1. **依赖精简**：避免pandas等重型库，使用内置csv模块
2. **界面优化**：使用Tkinter原生控件，避免复杂布局
3. **数据分片**：按分类分别存储CSV文件
4. **批量处理**：数据处理采用批量模式，避免UI阻塞

### 体积控制目标
- 最终EXE体积：10-15MB
- 依赖库最小化：仅必需的第三方库
- 排除不必要模块：使用PyInstaller的--exclude-module参数

## 七、打包与分发方案

### PyInstaller配置
```bash
# 基础打包命令
pyinstaller --onefile --noconfirm --clean --distpath ./dist --workpath ./build src/main.py

# 优化打包命令
pyinstaller --onefile --noconfirm --clean \
    --distpath ./dist --workpath ./build \
    --exclude-module pandas --exclude-module numpy \
    --add-data "data;data" \
    --name WealthLite \
    src/main.py
```

### 绿色版ZIP包结构
```text
WealthLite_v1.0/
├── WealthLite.exe              # 主程序
├── data/                       # 数据目录
│   ├── categories.json         # 预设分类
│   └── README.txt              # 数据说明
├── docs/                       # 用户文档
│   ├── 用户手册.pdf
│   └── 常见问题.txt
└── README.txt                  # 使用说明
```

### Nuitka备选方案
```bash
# Nuitka编译命令
nuitka --standalone --onefile \
    --include-data-dir=data=data \
    --windows-disable-console \
    --output-filename=WealthLite.exe \
    src/main.py
```

## 八、测试策略与质量保证

### 测试覆盖要求
- 单元测试覆盖率：≥80%
- 集成测试：核心业务流程全覆盖
- 性能测试：1000条记录处理性能基准

### 测试用例设计
1. **数据模型测试**：Asset、Category类的CRUD操作
2. **计算引擎测试**：年化回报率计算的边界条件
3. **存储测试**：CSV读写、加密解密、数据完整性
4. **界面测试**：GUI组件的交互逻辑
5. **集成测试**：完整业务流程的端到端测试

### 代码质量工具
- **格式化**：black（行长度88字符）
- **静态检查**：flake8 + mypy
- **复杂度控制**：最大圈复杂度10
- **文档规范**：Google风格docstring

## 九、风险评估与应对策略

### 技术风险
1. **依赖兼容性**：固定版本号，定期更新测试
2. **打包体积**：持续监控，优化依赖选择
3. **跨平台兼容**：优先保证Windows，后续扩展

### 数据风险
1. **数据丢失**：自动备份机制，多重保护
2. **加密安全**：使用成熟加密库，定期安全审计
3. **数据迁移**：提供标准导入导出格式

### 用户体验风险
1. **界面复杂度**：保持简洁，渐进式功能展示
2. **学习成本**：提供详细用户手册和示例
3. **性能问题**：异步处理，进度提示

## 十、验证与发布流程

### 开发验证步骤
1. **Cursor环境初始化**
   - 创建新项目，配置Python 3.12环境
   - 安装依赖，验证开发环境

2. **核心功能验证**
   - 实现年化回报率计算，单元测试验证
   - CSV读写功能测试
   - 基础GUI界面测试

3. **集成测试验证**
   - 完整业务流程测试
   - 数据一致性验证
   - 性能基准测试

4. **打包验证**
   - PyInstaller打包，检查EXE体积和依赖
   - 绿色版ZIP包测试
   - 不同Windows版本兼容性测试

### 发布检查清单
- [ ] 功能完整性测试通过
- [ ] 性能基准达标
- [ ] 安全测试通过
- [ ] 用户文档完整
- [ ] 打包文件验证
- [ ] 版本号和更新日志

---

> 本开发计划基于详细需求分析制定，将严格按照各阶段目标推进开发，确保最终产品完全满足用户需求。