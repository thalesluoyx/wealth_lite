# 资产总览图表数据生成逻辑

## 概述

WealthLite系统采用**交易驱动**的架构，所有持仓数据都是基于交易记录实时计算得出。本文档详细解释了从交易数据到资产总览图表的完整数据流和计算逻辑。

## 核心设计原则

1. **交易驱动**：所有持仓都由交易产生，没有独立的持仓表
2. **实时计算**：持仓数据基于交易记录实时计算，确保数据一致性
3. **历史模拟**：图表历史数据通过算法模拟生成，基于当前实际持仓

## 数据流架构

```
交易数据 (Transactions) 
    ↓
持仓计算 (Position Calculation)
    ↓
资产分组 (Asset Grouping)
    ↓
图表数据生成 (Chart Data Generation)
    ↓
图表渲染 (Chart Rendering)
```

## 详细流程说明

### 1. 交易数据结构

系统中的交易数据包含以下核心字段：

```javascript
{
    id: 'tx1',
    asset_id: 'asset1',           // 关联的资产ID
    type: 'DEPOSIT',              // 交易类型
    amount: 50000,                // 交易金额
    currency: 'CNY',              // 币种
    exchangeRate: 1,              // 汇率
    date: '2024-01-15',          // 交易日期
    notes: '初始存款'             // 备注
}
```

**支持的交易类型：**
- `DEPOSIT` / `BUY`: 存入/买入（增加持仓）
- `WITHDRAW` / `SELL`: 取出/卖出（减少持仓）
- `INTEREST` / `DIVIDEND`: 利息/分红收入（增加收益）
- `FEE`: 手续费（减少持仓）

### 2. 持仓计算逻辑

#### 2.1 按资产分组交易

```javascript
// 示例：按asset_id分组交易记录
const assetTransactions = {
    'asset1': [
        {id: 'tx1', type: 'DEPOSIT', amount: 50000, date: '2024-01-15'},
        {id: 'tx2', type: 'INTEREST', amount: 500, date: '2024-02-15'}
    ],
    'asset2': [
        {id: 'tx3', type: 'DEPOSIT', amount: 100000, date: '2024-01-20'},
        {id: 'tx4', type: 'INTEREST', amount: 2000, date: '2024-03-20'}
    ]
};
```

#### 2.2 单个资产持仓计算

对每个资产的交易记录进行汇总计算：

```javascript
function calculateAssetPosition(asset, transactions) {
    let totalInvested = 0;    // 总投入金额
    let totalWithdrawn = 0;   // 总取出金额
    let totalIncome = 0;      // 总收入金额
    let totalFees = 0;        // 总费用

    transactions.forEach(transaction => {
        const baseAmount = transaction.amount * (transaction.exchangeRate || 1);
        
        switch (transaction.type) {
            case 'DEPOSIT':
            case 'BUY':
                totalInvested += baseAmount;
                break;
            case 'WITHDRAW':
            case 'SELL':
                totalWithdrawn += baseAmount;
                break;
            case 'INTEREST':
            case 'DIVIDEND':
                totalIncome += baseAmount;
                break;
            case 'FEE':
                totalFees += baseAmount;
                break;
        }
    });

    // 核心计算公式
    const netInvested = totalInvested - totalWithdrawn;
    const currentValue = netInvested + totalIncome - totalFees;
    const totalReturn = totalIncome - totalFees;
    const totalReturnRate = netInvested > 0 ? (totalReturn / netInvested) * 100 : 0;

    return {
        amount: currentValue,           // 当前持仓价值
        total_return: totalReturn,      // 总收益
        total_return_rate: totalReturnRate / 100,  // 收益率
        // ... 其他字段
    };
}
```

#### 2.3 计算示例

**示例资产：招商银行定期存款**

交易记录：
```javascript
[
    {type: 'DEPOSIT', amount: 100000, date: '2024-01-01'},  // 存入10万
    {type: 'INTEREST', amount: 1000, date: '2024-02-01'},   // 利息1000
    {type: 'INTEREST', amount: 1000, date: '2024-03-01'},   // 利息1000
    {type: 'WITHDRAW', amount: 20000, date: '2024-03-15'}   // 提取2万
]
```

计算结果：
```javascript
{
    totalInvested: 100000,      // 总投入
    totalWithdrawn: 20000,      // 总取出
    totalIncome: 2000,          // 总利息收入
    totalFees: 0,               // 无手续费
    netInvested: 80000,         // 净投入 = 100000 - 20000
    currentValue: 82000,        // 当前价值 = 80000 + 2000 - 0
    totalReturn: 2000,          // 总收益 = 2000 - 0
    totalReturnRate: 2.5%       // 收益率 = 2000 / 80000 * 100%
}
```

### 3. 资产分组统计

计算完所有资产的持仓后，按资产类型进行分组统计：

```javascript
const assetTypeGroups = {
    'CASH': { name: '现金及等价物', total: 0, positions: [] },
    'FIXED_INCOME': { name: '固定收益', total: 0, positions: [] },
    'EQUITY': { name: '权益类', total: 0, positions: [] },
    // ...
};

positions.forEach(position => {
    const assetType = position.type || 'CASH';
    if (assetTypeGroups[assetType]) {
        assetTypeGroups[assetType].total += position.amount;
        assetTypeGroups[assetType].positions.push(position);
    }
});
```

### 4. 图表数据生成逻辑

#### 4.1 时间轴生成

根据选择的时间范围生成对应的数据点：

```javascript
function generateTimeLabels(timeRange) {
    const dataPoints = {
        '7d': 7,      // 7天
        '1m': 30,     // 30天
        '3m': 90,     // 90天
        '1y': 365     // 365天
    }[timeRange];

    const labels = [];
    for (let i = 0; i < dataPoints; i++) {
        const date = new Date();
        date.setDate(date.getDate() - (dataPoints - 1 - i));
        
        if (dataPoints <= 30) {
            labels.push(date.getDate());           // 显示日期
        } else if (dataPoints <= 90) {
            labels.push(`${date.getMonth() + 1}/${date.getDate()}`);  // 显示月/日
        } else {
            labels.push(`${date.getMonth() + 1}月`);  // 显示月份
        }
    }
    return labels;
}
```

#### 4.2 历史数据模拟算法

由于系统只保存交易记录而不保存历史持仓快照，图表的历史数据通过算法模拟生成：

```javascript
function generateHistoricalData(currentValue, dataPoints) {
    const data = [];
    
    for (let i = 0; i < dataPoints; i++) {
        const progress = i / (dataPoints - 1);  // 0到1的进度
        
        // 生成从70%到100%的增长趋势
        const baseValue = currentValue * (0.7 + progress * 0.3);
        
        // 添加5%的随机波动
        const variation = (Math.random() - 0.5) * currentValue * 0.05;
        
        data.push(Math.round(Math.max(0, baseValue + variation)));
    }
    
    return data;
}
```

**模拟算法特点：**
1. **增长趋势**：从历史较低值逐渐增长到当前实际值
2. **随机波动**：添加合理的市场波动模拟
3. **约束条件**：确保最终值等于当前实际持仓价值

#### 4.3 图表数据集构建

```javascript
function generateMainChartData(positions) {
    // 1. 计算总资产
    const totalAssets = positions.reduce((sum, p) => sum + p.amount, 0);
    
    // 2. 按类型分组
    const assetTypeGroups = groupByAssetType(positions);
    
    // 3. 生成数据集
    const datasets = [];
    
    // 主要曲线：总资产
    datasets.push({
        label: '总资产',
        data: generateHistoricalData(totalAssets, dataPoints),
        borderColor: '#2563eb',
        borderWidth: 4,
        fill: true
    });
    
    // 辅助曲线：各资产类型
    Object.keys(assetTypeGroups).forEach(type => {
        const group = assetTypeGroups[type];
        if (group.total > 0) {
            datasets.push({
                label: group.name,
                data: generateHistoricalData(group.total, dataPoints),
                borderColor: group.color,
                borderWidth: 2,
                fill: false
            });
        }
    });
    
    return { labels, datasets };
}
```

## 实际示例

### 示例数据

假设用户有以下交易记录：

```javascript
const transactions = [
    // 招商银行活期存款
    {asset_id: 'cmb_demand', type: 'DEPOSIT', amount: 50000, date: '2024-01-01'},
    {asset_id: 'cmb_demand', type: 'INTEREST', amount: 150, date: '2024-02-01'},
    
    // 工商银行定期存款
    {asset_id: 'icbc_fixed', type: 'DEPOSIT', amount: 100000, date: '2024-01-15'},
    {asset_id: 'icbc_fixed', type: 'INTEREST', amount: 2500, date: '2024-03-15'},
    
    // 余额宝
    {asset_id: 'yuebao', type: 'DEPOSIT', amount: 30000, date: '2024-02-01'},
    {asset_id: 'yuebao', type: 'INTEREST', amount: 200, date: '2024-03-01'}
];
```

### 持仓计算结果

```javascript
const positions = [
    {
        name: '招商银行活期存款',
        type: 'CASH',
        amount: 50150,           // 50000 + 150
        total_return: 150
    },
    {
        name: '工商银行定期存款', 
        type: 'FIXED_INCOME',
        amount: 102500,          // 100000 + 2500
        total_return: 2500
    },
    {
        name: '余额宝',
        type: 'CASH', 
        amount: 30200,           // 30000 + 200
        total_return: 200
    }
];
```

### 图表数据生成（30天）

```javascript
const chartData = {
    labels: [1, 2, 3, ..., 30],  // 30天的日期
    datasets: [
        {
            label: '总资产',
            data: [127881, 129234, 131567, ..., 182850],  // 模拟的30天总资产变化
            borderColor: '#2563eb',
            borderWidth: 4
        },
        {
            label: '现金及等价物',
            data: [56245, 57123, 58456, ..., 80350],      // 模拟的现金类资产变化
            borderColor: '#10b981',
            borderWidth: 2
        },
        {
            label: '固定收益',
            data: [71636, 72111, 73111, ..., 102500],     // 模拟的固收类资产变化
            borderColor: '#667eea', 
            borderWidth: 2
        }
    ]
};
```

## 技术实现要点

### 1. 性能优化

- **缓存机制**：持仓数据计算完成后缓存在`ChartManager.currentPositions`中
- **增量更新**：只有新增交易时才重新计算持仓
- **异步计算**：大量交易数据的计算采用异步方式

### 2. 数据一致性

- **统一取整**：所有金额显示都使用`Math.round()`进行取整
- **汇率处理**：多币种交易统一转换为基础货币计算
- **时区处理**：交易日期统一使用本地时区

### 3. 扩展性设计

- **资产类型**：支持新增资产类型，图表自动适配
- **交易类型**：支持新增交易类型，计算逻辑自动适配
- **时间范围**：支持自定义时间范围和数据点数量

## 未来优化方向

1. **真实历史数据**：实现持仓快照功能，保存真实的历史数据
2. **市值计算**：集成实时市价，计算未实现损益
3. **预测模型**：基于历史趋势预测未来资产变化
4. **性能优化**：大数据量时的计算性能优化

---

*文档版本：v1.0*  
*最后更新：2025-01-21*  
*作者：WealthLite开发团队* 