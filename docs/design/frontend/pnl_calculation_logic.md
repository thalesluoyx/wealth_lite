# WealthLite 收益逻辑设计文档

## 文档信息
- **创建时间**: 2025-07-06
- **版本**: 1.0
- **作者**: WealthLite开发团队

## 概述

本文档详细说明WealthLite系统中不同资产类型的收益计算逻辑，包括已实现损益和未实现损益的计算方法。

## 核心概念

### 基本定义
- **成本基础 (Cost Basis)**: `principal_amount` = 净投入金额 - 费用
- **当前估值 (Current Value)**: 资产的当前市场价值或账面价值
- **已实现损益 (Realized PnL)**: 已经确定的收益或损失
- **未实现损益 (Unrealized PnL)**: 尚未确定的浮动盈亏

### 总收益组成
```
总收益 = 已实现损益 + 未实现损益
```

## 不同资产类型的计算逻辑

### 1. 现金及等价物 (CASH)

#### 计算方法
```python
# 已实现损益
realized_pnl = total_income  # 利息收入

# 未实现损益
unrealized_pnl = 0  # 现金无市场价格波动
```

#### 示例：活期-人民币
- **投资本金**: 1,022,000元
- **利息收入**: 0元
- **已实现损益**: 0元
- **未实现损益**: 0元
- **总收益**: 0元

### 2. 固定收益 (FIXED_INCOME) - 方案三：分阶段确认

#### 计算方法
```python
# 已实现损益
realized_pnl = total_income  # 利息收入

# 未实现损益
if status == 'MATURED' or status == 'CLOSED':
    unrealized_pnl = 0  # 已到期，全部转为已实现
else:
    unrealized_pnl = current_value - principal_amount  # 持有期间的浮动盈亏
```

#### 示例1：浦发理财一年（已到期）
- **投资本金**: 1,000,000元
- **利息收入**: 22,000元
- **当前估值**: 1,000,000元（已到期）
- **状态**: MATURED
- **已实现损益**: 22,000元
- **未实现损益**: 0元（已全部转为已实现）
- **总收益**: 22,000元

#### 示例2：浦发三年定期（持有中）
- **投资本金**: 1,000,000元
- **年利率**: 2.6%
- **持有天数**: 368天（约1.01年）
- **当前估值**: 1,026,214元（按比例计息）
- **利息收入**: 0元（未到期）
- **状态**: ACTIVE
- **已实现损益**: 0元
- **未实现损益**: 26,214元
- **总收益**: 26,214元

#### 示例3：工行尊益基金（持有中）
- **投资本金**: 1,500,000元
- **年利率**: 2.6%
- **持有天数**: 353天（约0.97年）
- **当前估值**: 1,537,611元（按比例计息）
- **利息收入**: 0元（未到期）
- **状态**: ACTIVE
- **已实现损益**: 0元
- **未实现损益**: 37,611元
- **总收益**: 37,611元

### 3. 权益类资产 (EQUITY)

#### 计算方法
```python
# 已实现损益
realized_pnl = total_income  # 分红收入 + 卖出收益

# 未实现损益
unrealized_pnl = current_market_value - principal_amount - realized_pnl
```

#### 示例：股票投资（假设）
- **投资本金**: 100,000元
- **当前市值**: 105,000元
- **分红收入**: 2,000元
- **已实现损益**: 2,000元
- **未实现损益**: 105,000 - 100,000 - 2,000 = 3,000元
- **总收益**: 5,000元

## UI显示逻辑

### 持仓明细表格
- **总收益**: 显示在主表格中，包含已实现和未实现损益
- **收益率**: 基于总收益计算的百分比

### 持仓详情展开面板

#### 收益分析标签页
```
总收益: ¥22,000 (绿色/红色)
总收益率: 2.20%
未实现损益: ¥0 (已到期产品)
已实现损益: ¥22,000 (利息收入)
年化收益率: 2.20%
```

### 颜色规则
- **绿色 (positive)**: 收益 ≥ 0
- **红色 (negative)**: 收益 < 0

## 实际系统数据示例

基于系统日志的真实数据：

### 当前持仓概览
```
总资产: 3,044,000元
现金资产: 1,022,000元
固定收益资产: 2,022,000元
```

### 具体持仓明细

#### 1. 活期-人民币
```json
{
  "name": "活期-人民币",
  "type": "cash",
  "amount": 1022000,
  "total_return": 0,
  "realized_pnl": 0,
  "unrealized_pnl": 0,
  "status": "ACTIVE"
}
```

#### 2. 浦发三年定期
```json
{
  "name": "浦发三年定期",
  "type": "fixed_income",
  "amount": 1000000,
  "total_return": 0,
  "realized_pnl": 0,
  "unrealized_pnl": 0,
  "status": "ACTIVE"
}
```

#### 3. 浦发理财一年
```json
{
  "name": "浦发理财一年",
  "type": "fixed_income",
  "amount": 1022000,
  "total_return": 22000,
  "realized_pnl": 22000,
  "unrealized_pnl": 0,
  "status": "MATURED"
}
```

## 计算公式总结

### 基础公式
```
成本基础 = 净投入金额 - 费用
当前估值 = 根据资产类型计算的当前价值
总收益 = 当前估值 - 成本基础
```

### 分类公式

#### 现金类
```
已实现损益 = 利息收入
未实现损益 = 0
```

#### 固定收益类（方案三）
```
已实现损益 = 利息收入
未实现损益 = 
  if (已到期) then 0
  else (当前估值 - 成本基础)

当前估值计算（持有期间）:
  预期收益 = 本金 × 年利率 × (持有天数 / 365)
  当前估值 = 本金 + 预期收益 + 已实现收益
```

#### 权益类
```
已实现损益 = 分红收入 + 卖出收益
未实现损益 = 当前市值 - 成本基础 - 已实现损益
```

## 技术实现

### 后端模型
- `Position.calculate_realized_pnl()`: 计算已实现损益
- `Position.calculate_unrealized_pnl()`: 计算未实现损益
- `Position.calculate_total_return()`: 计算总收益

### 前端显示
- 主表格显示总收益和收益率
- 详情面板分别显示已实现和未实现损益
- 根据正负值应用不同颜色样式

## 未来改进方向

1. **净值跟踪**: 为银行理财产品添加净值跟踪功能
2. **市场价格**: 为权益类资产集成实时市场价格
3. **汇率处理**: 完善多币种资产的损益计算
4. **历史记录**: 记录损益变化历史
5. **风险指标**: 添加波动率、最大回撤等风险指标

## 版本历史

- **v1.0 (2025-07-06)**: 初始版本，实现基础损益计算逻辑 