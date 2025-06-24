# WealthLite 外币资产处理设计方案

## 文档信息
- **创建日期**: 2024-12-31
- **版本**: 1.0
- **状态**: 已验证通过

## 概述

本文档详细记录了WealthLite系统中外币资产（以港元定存为例）的处理方案设计、实现和验证结果。采用简化原则，通过在交易层面记录汇率信息，实现了对外币资产全生命周期的完整支持。

## 设计背景

### 核心问题
用户询问简化方案是否能够处理港元定存到期后的两种情况：
1. **情况A**：到期后变成港元现金
2. **情况B**：到期后转回人民币

### 设计原则
1. **简化原则**：不单独记录外汇兑换交易，直接在存取款交易中体现
2. **自动计算**：汇率收益自动体现在基础货币转换中
3. **用户习惯**：符合大部分用户的记账习惯
4. **完整性**：支持外币资产的完整生命周期管理

## 技术架构

### 核心数据结构

#### BaseTransaction 汇率支持
```python
class BaseTransaction:
    # 交易金额（原币种）
    amount: Decimal = Decimal('0')
    currency: Currency = Currency.CNY
    
    # 汇率和基础货币转换
    exchange_rate: Decimal = Decimal('1.0')  # 对基础货币的汇率
    amount_base_currency: Decimal = Decimal('0')  # 基础货币金额
    
    def __post_init__(self):
        # 自动计算基础货币金额
        if self.amount_base_currency == 0:
            self.amount_base_currency = self.amount * self.exchange_rate
```

#### Position 双币种支持
```python
class Position:
    # 基础货币计算（用于投资组合汇总）
    @property
    def current_book_value(self) -> Decimal:
        """当前账面价值（基础货币）"""
        return self.principal_amount + self.total_income
    
    # 原币种计算（用于资产详情显示）
    @property
    def current_book_value_original_currency(self) -> Decimal:
        """当前账面价值（原币种）"""
        return self.principal_amount_original_currency + self.total_income_original_currency
```

### 数据流设计
```
外币交易 → 记录汇率 → 双币种计算 → 组合汇总
    ↓           ↓           ↓           ↓
原币种金额  基础货币金额  持仓状态   投资组合
```

## 实现方案

### 情况A：港元定存到期后变成港元现金

#### 1. 港元定存阶段
```python
# 创建港元定存资产
hkd_deposit_asset = wealth_service.create_asset(
    asset_name="汇丰银行港元定期存款",
    asset_type=AssetType.FIXED_INCOME,
    currency=Currency.HKD
)

# 存入港元定存
deposit_transaction = wealth_service.create_fixed_income_transaction(
    asset_id=hkd_deposit_asset.asset_id,
    transaction_type=TransactionType.DEPOSIT,
    amount=Decimal('90000.00'),  # 港币金额
    currency=Currency.HKD,
    exchange_rate=Decimal('0.9'),  # 1 HKD = 0.9 CNY
    transaction_date=date(2024, 1, 15),
    annual_rate=Decimal('3.5')
)
# 结果：90,000 HKD → 等值 81,000 CNY

# 利息收入
interest_transaction = wealth_service.create_fixed_income_transaction(
    asset_id=hkd_deposit_asset.asset_id,
    transaction_type=TransactionType.INTEREST,
    amount=Decimal('787.50'),  # 港币利息
    currency=Currency.HKD,
    exchange_rate=Decimal('0.92'),  # 到期时汇率变化
    transaction_date=date(2024, 4, 15)
)
# 结果：787.5 HKD → 等值 724.5 CNY
```

#### 2. 转为港元现金阶段
```python
# 创建港元现金资产
hkd_cash_asset = wealth_service.create_asset(
    asset_name="汇丰银行港元储蓄账户",
    asset_type=AssetType.CASH,
    currency=Currency.HKD
)

# 定存到期转现金
maturity_transfer = wealth_service.create_cash_transaction(
    asset_id=hkd_cash_asset.asset_id,
    transaction_type=TransactionType.DEPOSIT,
    amount=Decimal('90787.50'),  # 本金+利息
    currency=Currency.HKD,
    exchange_rate=Decimal('0.92'),  # 到期时汇率
    transaction_date=date(2024, 4, 15)
)
# 结果：90,787.5 HKD → 等值 83,524.5 CNY
```

#### 3. 收益分析
- **港币收益**：787.5 HKD（利息收入）
- **汇率收益**：自动体现在基础货币转换中
- **最终状态**：持有90,787.5 HKD现金

### 情况B：港元定存到期后转回人民币

#### 1. 港元定存阶段（同情况A）
```python
# 存入90,000 HKD，汇率0.9，等值81,000 CNY
# 利息1,710 HKD，汇率0.95，等值1,624.5 CNY
```

#### 2. 兑换回人民币阶段
```python
# 创建人民币现金资产
cny_cash_asset = wealth_service.create_asset(
    asset_name="招商银行人民币储蓄账户",
    asset_type=AssetType.CASH,
    currency=Currency.CNY
)

# 外汇兑换（港币换人民币）
conversion_transaction = wealth_service.create_cash_transaction(
    asset_id=cny_cash_asset.asset_id,
    transaction_type=TransactionType.DEPOSIT,
    amount=Decimal('87124.50'),  # 兑换后的人民币金额
    currency=Currency.CNY,
    exchange_rate=Decimal('1.0'),  # 人民币对人民币汇率为1
    transaction_date=date(2024, 7, 1),
    notes="港元定存到期兑换，91710 HKD * 0.95 = 87124.5 CNY"
)
```

#### 3. 收益分析
- **原始投资**：81,000 CNY
- **最终收回**：87,124.5 CNY
- **总收益**：6,124.5 CNY（包含利息收益和汇率收益）

## 验证结果

### 测试覆盖
创建了完整的测试套件 `tests/integration/test_foreign_currency_deposits.py`：

1. **test_hkd_deposit_to_hkd_cash_scenario**：验证情况A
2. **test_hkd_deposit_to_cny_conversion_scenario**：验证情况B
3. **test_multiple_currency_deposits_portfolio**：多币种组合管理
4. **test_exchange_rate_fluctuation_impact**：汇率波动影响

### 核心功能验证

#### ✅ 双币种计算支持
```python
# Position模型新增原币种计算方法
position.current_book_value_original_currency  # 原币种金额
position.current_book_value                    # 基础货币金额
```

#### ✅ 汇率自动转换
```python
# 每笔交易自动计算基础货币金额
transaction.amount = Decimal('90000.00')           # 港币
transaction.exchange_rate = Decimal('0.9')         # 汇率
transaction.amount_base_currency = Decimal('81000.00')  # 自动计算
```

#### ✅ 投资组合汇总
```python
# 不同币种资产统一汇总为基础货币
portfolio.total_value  # 自动汇总所有资产的基础货币价值
```

### 测试结果
```bash
tests/integration/test_foreign_currency_deposits.py::TestForeignCurrencyDeposits::test_hkd_deposit_to_hkd_cash_scenario PASSED
tests/integration/test_foreign_currency_deposits.py::TestForeignCurrencyDeposits::test_hkd_deposit_to_cny_conversion_scenario PASSED
tests/integration/test_foreign_currency_deposits.py::TestForeignCurrencyDeposits::test_multiple_currency_deposits_portfolio PASSED
tests/integration/test_foreign_currency_deposits.py::TestForeignCurrencyDeposits::test_exchange_rate_fluctuation_impact PASSED

==================================================== 4 passed in 0.51s ====================================================
```

## 方案优势

### 1. 简洁性
- **交易记录简洁**：不需要单独记录外汇兑换交易
- **操作直观**：直接在存取款中体现汇率和币种
- **减少复杂度**：避免了复杂的外汇交易链

### 2. 准确性
- **汇率记录**：每笔交易记录当时的准确汇率
- **自动转换**：系统自动计算基础货币等值
- **收益追踪**：汇率收益和利息收益都能准确追踪

### 3. 灵活性
- **双币种显示**：支持原币种和基础货币两种显示模式
- **多账户支持**：同一币种可以有多个账户（定存、储蓄等）
- **扩展性强**：方案可扩展到其他外币资产

### 4. 用户友好
- **符合习惯**：符合大部分用户的记账思维
- **信息完整**：提供完整的资产变化轨迹
- **分析便利**：便于进行收益分析和资产配置

## 技术实现细节

### 数据库设计
```sql
-- transactions表支持多币种
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,           -- 原币种金额
    currency TEXT NOT NULL,                  -- 币种
    exchange_rate DECIMAL(10,6) NOT NULL,    -- 汇率
    amount_base_currency DECIMAL(15,2) NOT NULL, -- 基础货币金额
    transaction_date DATE NOT NULL,
    -- 其他字段...
);
```

### 关键算法
```python
# 汇率收益计算示例
def calculate_exchange_gain(transactions):
    """计算汇率收益"""
    total_gain = Decimal('0')
    for tx in transactions:
        if tx.currency != base_currency:
            # 汇率收益 = 原币种金额 × (当前汇率 - 交易时汇率)
            current_rate = get_current_rate(tx.currency)
            gain = tx.amount * (current_rate - tx.exchange_rate)
            total_gain += gain
    return total_gain
```

## 使用场景扩展

### 支持的外币类型
- **港币 (HKD)**：已验证
- **美元 (USD)**：已支持
- **欧元 (EUR)**：已支持
- **其他主要货币**：框架已就绪

### 支持的资产类型
- **外币定存**：已验证
- **外币储蓄**：已验证
- **外币理财**：框架支持
- **外币债券**：框架支持

### 业务场景
1. **跨境投资**：海外资产配置
2. **外汇储蓄**：多币种现金管理
3. **汇率套利**：汇率波动收益追踪
4. **风险对冲**：多币种风险分散

## 结论

**简化方案完全能够处理港元定存到期后的两种情况**，并且提供了一个优雅、简洁、完整的外币资产管理解决方案。

### 核心成果
1. ✅ **功能完整性**：支持外币资产的完整生命周期
2. ✅ **数据准确性**：汇率和收益计算准确可靠
3. ✅ **操作简便性**：符合用户直觉，操作简单
4. ✅ **系统扩展性**：可扩展到更多币种和资产类型

### 验证状态
- **设计验证**：✅ 通过
- **代码实现**：✅ 完成
- **单元测试**：✅ 通过
- **集成测试**：✅ 通过
- **场景验证**：✅ 通过

该方案已准备好投入生产使用，为WealthLite系统的外币资产管理提供了坚实的技术基础。 