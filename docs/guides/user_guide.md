# WealthLite 用户操作指南

## 目录
1. [软件简介](#软件简介)
2. [启动软件](#启动软件)
3. [界面介绍](#界面介绍)
4. [基本操作](#基本操作)
5. [高级功能](#高级功能)
6. [数据管理](#数据管理)
7. [常见问题](#常见问题)

---

## 软件简介

WealthLite 是一款轻量级的个人资产分类与投资回报管理工具，帮助您：

- **资产分类管理**：按照专业的5大资产类别进行分类
- **投资回报追踪**：自动计算总收益率、年化回报率等关键指标
- **投资组合分析**：提供详细的投资组合摘要和表现分析
- **数据导出备份**：支持Excel导出和数据备份功能

### 支持的资产类别

1. **现金及等价物**：活期存款、货币基金、短期理财
2. **固定收益类**：定期存款、国债、企业债、债券基金
3. **权益类**：股票、股票型基金、ETF
4. **不动产**：住宅、商铺、REITs
5. **大宗商品**：贵金属

---

## 启动软件

### 方法一：直接启动
```bash
python main.py
```

### 方法二：使用启动脚本
```bash
python run_wealthlite.py
```

### 系统要求
- Python 3.7+
- tkinter（通常随Python安装）
- 其他依赖包（见requirements.txt）

---

## 界面介绍

### 主界面布局

```
┌─────────────────────────────────────────────────────────────┐
│ 文件(F)  编辑(E)  帮助(H)                                    │
├─────────────────────────────────────────────────────────────┤
│ [新建] [编辑] [删除] [刷新] [导出]    [搜索框]              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────────────┐   │
│  │                     │  │                             │   │
│  │     资产列表        │  │      资产详情               │   │
│  │                     │  │                             │   │
│  │  - 资产名称         │  │  ┌─────────────────────────┐ │   │
│  │  - 分类信息         │  │  │     资产详情            │ │   │
│  │  - 投资金额         │  │  │                         │ │   │
│  │  - 收益情况         │  │  └─────────────────────────┘ │   │
│  │                     │  │  ┌─────────────────────────┐ │   │
│  │                     │  │  │    投资组合摘要         │ │   │
│  │                     │  │  │                         │ │   │
│  └─────────────────────┘  │  └─────────────────────────┘ │   │
│                           └─────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│ 就绪                                            资产: 0     │
└─────────────────────────────────────────────────────────────┘
```

### 界面组件说明

1. **菜单栏**
   - 文件：新建资产、导出数据、退出
   - 编辑：编辑资产、删除资产、刷新数据
   - 帮助：关于软件

2. **工具栏**
   - 新建：创建新资产
   - 编辑：编辑选中资产
   - 删除：删除选中资产
   - 刷新：重新加载数据
   - 导出：导出Excel文件
   - 搜索框：快速搜索资产

3. **资产列表**（左侧面板）
   - 显示所有资产的汇总信息
   - 支持按列排序
   - 颜色标识：绿色（盈利）、红色（亏损）、黑色（持平）

4. **详情面板**（右侧面板）
   - 资产详情：显示选中资产的详细信息
   - 投资组合：显示整体投资组合摘要

5. **状态栏**
   - 显示当前操作状态
   - 显示资产总数

---

## 基本操作

### 1. 新建资产

#### 步骤：
1. 点击工具栏的"新建"按钮，或使用快捷键 `Ctrl+N`
2. 在弹出的对话框中填写资产信息：

**基本信息**
- **资产名称**：输入资产的名称（必填）
- **一级分类**：从下拉菜单选择资产类别（必填）
- **二级分类**：根据一级分类自动更新选项（必填）
- **描述**：输入资产的详细描述（可选）

**投资信息**
- **初始投入**：输入投资的本金金额（必填）
- **当前价值**：输入资产的当前市值（必填）
- **开始日期**：选择投资开始日期（必填，默认为今天）

3. 点击"保存"按钮完成创建

#### 示例：
```
资产名称：招商银行股票
一级分类：权益类
二级分类：股票
描述：长期持有的银行股
初始投入：10000
当前价值：12500
开始日期：2023-01-15
```

### 2. 查看资产详情

#### 步骤：
1. 在资产列表中点击选择任意资产
2. 右侧"资产详情"面板会自动显示该资产的详细信息

#### 详情内容包括：
- **基本信息**：名称、分类、描述、标签
- **投资信息**：初始投入、当前价值、总收益、收益率、年化回报率
- **时间信息**：开始日期、持有天数、最后更新日期
- **交易记录**：历史交易记录（如有）

### 3. 编辑资产

#### 步骤：
1. 在资产列表中选择要编辑的资产
2. 点击工具栏的"编辑"按钮，或使用快捷键 `Ctrl+E`
3. 在弹出的对话框中修改资产信息
4. 点击"保存"按钮确认修改

### 4. 删除资产

#### 步骤：
1. 在资产列表中选择要删除的资产
2. 点击工具栏的"删除"按钮，或按 `Delete` 键
3. 在确认对话框中点击"是"确认删除

⚠️ **注意**：删除操作不可撤销，请谨慎操作！

### 5. 搜索资产

#### 步骤：
1. 在工具栏的搜索框中输入关键词
2. 系统会实时过滤显示匹配的资产
3. 清空搜索框可显示所有资产

#### 搜索范围：
- 资产名称
- 资产分类
- 资产描述

---

## 高级功能

### 1. 投资组合分析

在右侧面板的"投资组合"标签页中，您可以查看：

#### 整体统计
- **总资产数量**：当前管理的资产总数
- **初始投资金额**：所有资产的投入本金总和
- **当前总价值**：所有资产的当前市值总和
- **总收益**：总收益金额
- **总收益率**：整体投资收益率

#### 分类明细
- 按资产类别统计各类资产的：
  - 资产数量
  - 投资价值
  - 占比情况
  - 收益率表现

### 2. 数据排序

#### 操作方法：
- 点击资产列表的任意列标题即可按该列排序
- 再次点击可切换升序/降序

#### 支持排序的列：
- 资产名称（文本排序）
- 分类信息（文本排序）
- 金额数据（数值排序）
- 收益率（数值排序）
- 日期信息（日期排序）

### 3. 颜色标识

资产列表使用颜色来快速识别投资表现：
- 🟢 **绿色**：收益率为正（盈利）
- 🔴 **红色**：收益率为负（亏损）
- ⚫ **黑色**：收益率为零（持平）

---

## 数据管理

### 1. 数据存储

WealthLite 使用以下文件存储数据：
- `data/assets.csv`：资产基本信息
- `data/transactions.csv`：交易记录
- `data/config.json`：应用配置
- `data/settings.json`：用户设置

### 2. 数据备份

#### 自动备份
- 每次保存数据时自动创建备份
- 备份文件存储在 `data/backups/` 目录
- 备份文件名包含时间戳

#### 手动备份
1. 复制整个 `data/` 目录到安全位置
2. 或使用Excel导出功能导出数据

### 3. Excel导出

#### 操作步骤：
1. 点击工具栏的"导出"按钮
2. 选择保存位置和文件名
3. 点击"保存"完成导出

#### 导出内容：
- **资产汇总**工作表：所有资产的详细信息
- **投资组合摘要**工作表：整体投资分析
- **分类统计**工作表：按类别统计数据

### 4. 数据刷新

#### 操作方法：
- 点击工具栏的"刷新"按钮
- 或使用快捷键 `F5`
- 或通过菜单：编辑 → 刷新数据

#### 刷新内容：
- 重新加载所有数据文件
- 更新资产列表显示
- 重新计算投资组合摘要

---

## 常见问题

### Q1: 软件启动失败怎么办？

**A1**: 请检查以下几点：
1. 确认Python版本为3.7或以上
2. 确认已安装所有依赖包：`pip install -r requirements.txt`
3. 确认tkinter模块可用（通常随Python安装）
4. 查看错误信息，如有导入错误请检查模块路径

### Q2: 如何修改已有资产的当前价值？

**A2**: 
1. 选择要修改的资产
2. 点击"编辑"按钮
3. 修改"当前价值"字段
4. 点击"保存"

### Q3: 年化回报率是如何计算的？

**A3**: 年化回报率计算公式：
```
年化回报率 = (当前价值/初始投入)^(1/持有年数) - 1
```
其中持有年数 = 持有天数 ÷ 365.25

### Q4: 可以导入其他软件的数据吗？

**A4**: 目前版本不支持直接导入，但您可以：
1. 手动录入资产信息
2. 或修改CSV文件格式后放入data目录

### Q5: 数据文件损坏了怎么办？

**A5**: 
1. 检查 `data/backups/` 目录中的备份文件
2. 将最新的备份文件复制到 `data/` 目录
3. 重新启动软件

### Q6: 如何添加自定义资产分类？

**A6**: 当前版本使用预定义的5大资产类别，暂不支持自定义分类。如有需要，可在描述字段中添加更详细的分类信息。

### Q7: 软件支持多用户吗？

**A7**: 当前版本为单用户设计。如需多用户使用，建议为每个用户创建独立的软件目录。

---

## 快捷键一览

| 功能 | 快捷键 |
|------|--------|
| 新建资产 | `Ctrl+N` |
| 编辑资产 | `Ctrl+E` |
| 删除资产 | `Delete` |
| 刷新数据 | `F5` |
| 退出软件 | `Ctrl+Q` |

---

## 技术支持

如果您在使用过程中遇到问题，请：

1. 查阅本操作指南
2. 检查软件日志文件
3. 联系技术支持

---

*WealthLite v1.0 - 轻量级资产管理工具* 