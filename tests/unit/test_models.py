"""
WealthLite Phase 1 核心数据模型单元测试

专注于现金及等价物和固定收益类资产的功能测试。
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta

from src.wealth_lite.models import (
    Asset, AssetType, Currency, RiskLevel, LiquidityLevel,
    CashTransaction, FixedIncomeTransaction, TransactionType, 
    InterestType, PaymentFrequency, Position, Portfolio, PortfolioSnapshot
)
from tests.factories import AssetFactory, TransactionFactory, PortfolioFactory, DataBuilder


class TestPhase1Assets:
    """Phase 1 资产模型测试 - 现金和固定收益"""
    
    def test_cash_asset_creation(self):
        """测试现金资产创建"""
        asset = AssetFactory.create_cash_asset(asset_name="测试储蓄账户")
        
        assert asset.asset_name == "测试储蓄账户"
        assert asset.asset_type == AssetType.CASH
        assert asset.currency == Currency.CNY
        assert asset.primary_category == "现金及等价物"
        assert asset.risk_level == RiskLevel.VERY_LOW
        assert asset.liquidity_level == LiquidityLevel.VERY_HIGH
        assert asset.asset_id is not None
        assert len(asset.asset_id) == 36  # UUID长度
    
    def test_fixed_income_asset_creation(self):
        """测试固定收益资产创建"""
        asset = AssetFactory.create_fixed_income_asset(asset_name="测试国债")
        
        assert asset.asset_name == "测试国债"
        assert asset.asset_type == AssetType.FIXED_INCOME
        assert asset.currency == Currency.CNY
        assert asset.primary_category == "固定收益类"
        assert asset.risk_level == RiskLevel.LOW
        assert asset.liquidity_level == LiquidityLevel.MEDIUM
    
    def test_asset_serialization(self):
        """测试资产序列化"""
        asset = AssetFactory.create_cash_asset(
            asset_name="测试序列化",
            description="序列化测试资产"
        )
        
        # 序列化
        data = asset.to_dict()
        assert data["asset_name"] == "测试序列化"
        assert data["asset_type"] == AssetType.CASH.name  # 使用.name而不是.value
        assert data["description"] == "序列化测试资产"
        
        # 反序列化
        restored_asset = Asset.from_dict(data)
        assert restored_asset.asset_name == asset.asset_name
        assert restored_asset.asset_id == asset.asset_id
        assert restored_asset.asset_type == asset.asset_type


class TestPhase1Transactions:
    """Phase 1 交易模型测试 - 现金和固定收益交易"""
    
    def test_cash_deposit_transaction(self):
        """测试现金存款交易"""
        asset = AssetFactory.create_cash_asset()
        transaction = TransactionFactory.create_cash_deposit(
            asset.asset_id,
            amount=Decimal('5000.00'),
            interest_rate=Decimal('2.5')
        )
        
        assert transaction.asset_id == asset.asset_id
        assert transaction.amount == Decimal('5000.00')
        assert transaction.interest_rate == Decimal('2.5')
        assert transaction.transaction_type == TransactionType.DEPOSIT
        assert transaction.account_type == "SAVINGS"
    
    def test_cash_withdraw_transaction(self):
        """测试现金取出交易"""
        asset = AssetFactory.create_cash_asset()
        transaction = TransactionFactory.create_cash_withdraw(
            asset.asset_id,
            amount=Decimal('1000.00')
        )
        
        assert transaction.asset_id == asset.asset_id
        assert transaction.amount == Decimal('1000.00')
        assert transaction.transaction_type == TransactionType.WITHDRAW
    
    def test_cash_interest_transaction(self):
        """测试现金利息交易"""
        asset = AssetFactory.create_cash_asset()
        transaction = TransactionFactory.create_cash_interest(
            asset.asset_id,
            amount=Decimal('50.00')
        )
        
        assert transaction.asset_id == asset.asset_id
        assert transaction.amount == Decimal('50.00')
        assert transaction.transaction_type == TransactionType.INTEREST
    
    def test_fixed_income_purchase_transaction(self):
        """测试固定收益购买交易"""
        asset = AssetFactory.create_fixed_income_asset()
        transaction = TransactionFactory.create_fixed_income_purchase(
            asset.asset_id,
            amount=Decimal('10000.00'),
            annual_rate=Decimal('3.5'),
            face_value=Decimal('10000.00')
        )
        
        assert transaction.asset_id == asset.asset_id
        assert transaction.amount == Decimal('10000.00')
        assert transaction.annual_rate == Decimal('3.5')
        assert transaction.face_value == Decimal('10000.00')
        assert transaction.interest_type == InterestType.SIMPLE
        assert transaction.payment_frequency == PaymentFrequency.ANNUALLY
        assert transaction.transaction_type == TransactionType.BUY
    
    def test_fixed_income_interest_transaction(self):
        """测试固定收益利息交易"""
        asset = AssetFactory.create_fixed_income_asset()
        transaction = TransactionFactory.create_fixed_income_interest(
            asset.asset_id,
            amount=Decimal('350.00')
        )
        
        assert transaction.asset_id == asset.asset_id
        assert transaction.amount == Decimal('350.00')
        assert transaction.transaction_type == TransactionType.INTEREST
        assert transaction.annual_rate == Decimal('3.5')
    
    def test_transaction_serialization(self):
        """测试交易序列化"""
        asset = AssetFactory.create_cash_asset()
        transaction = TransactionFactory.create_cash_deposit(asset.asset_id)
        
        # 序列化
        data = transaction.to_dict()
        assert data["asset_id"] == asset.asset_id
        assert data["transaction_type"] == TransactionType.DEPOSIT.name  # 使用.name而不是.value
        
        # 反序列化
        restored = CashTransaction.from_dict(data)
        assert restored.asset_id == transaction.asset_id
        assert restored.amount == transaction.amount


class TestPhase1Positions:
    """Phase 1 持仓模型测试"""
    
    def test_cash_position_calculation(self):
        """测试现金持仓计算"""
        asset = AssetFactory.create_cash_asset()
        
        # 创建多笔现金交易
        deposit1 = TransactionFactory.create_cash_deposit(
            asset.asset_id, amount=Decimal('10000.00')
        )
        deposit2 = TransactionFactory.create_cash_deposit(
            asset.asset_id, amount=Decimal('5000.00')
        )
        interest1 = TransactionFactory.create_cash_interest(
            asset.asset_id, amount=Decimal('25.00')
        )
        withdraw = TransactionFactory.create_cash_withdraw(
            asset.asset_id, amount=Decimal('2000.00')
        )
        
        position = Position(asset=asset, transactions=[deposit1, deposit2, interest1, withdraw])
        
        # 验证计算结果
        assert position.calculate_current_value() == Decimal('13025.00')  # 10000 + 5000 + 25 - 2000
        assert position.net_invested == Decimal('13000.00')  # 15000 - 2000 (净投入)
        assert position.calculate_total_return() == Decimal('25.00')       # 利息收入
        assert abs(position.calculate_total_return_rate() - 0.19230769230769232) < 0.001  # 25/13000 * 100
    
    def test_fixed_income_position_calculation(self):
        """测试固定收益持仓计算"""
        asset = AssetFactory.create_fixed_income_asset()
        
        # 创建固定收益交易
        purchase = TransactionFactory.create_fixed_income_purchase(
            asset.asset_id, amount=Decimal('10000.00')
        )
        interest1 = TransactionFactory.create_fixed_income_interest(
            asset.asset_id, amount=Decimal('350.00')
        )
        interest2 = TransactionFactory.create_fixed_income_interest(
            asset.asset_id, amount=Decimal('350.00')
        )
        
        position = Position(asset=asset, transactions=[purchase, interest1, interest2])
        
        # 验证计算结果
        assert position.calculate_current_value() == Decimal('10700.00')  # 10000 + 350 + 350
        assert position.total_invested == Decimal('10000.00')  # 购买金额
        assert position.calculate_total_return() == Decimal('700.00')      # 利息收入
        assert abs(position.calculate_total_return_rate() - 7.0) < 0.001   # 7%
    
    def test_position_serialization(self):
        """测试持仓序列化"""
        asset = AssetFactory.create_cash_asset()
        transaction = TransactionFactory.create_cash_deposit(asset.asset_id)
        position = Position(asset=asset, transactions=[transaction])
        
        # 序列化
        data = position.to_dict()
        assert data["asset"]["asset_id"] == asset.asset_id
        assert len(data["transactions"]) == 1
        
        # 注意：Position类没有from_dict方法，这里只测试序列化
        # restored = Position.from_dict(data)
        # assert restored.asset.asset_id == position.asset.asset_id
        # assert len(restored.transactions) == 1


class TestPhase1Portfolio:
    """Phase 1 投资组合模型测试"""
    
    def test_simple_cash_portfolio(self):
        """测试简单现金投资组合"""
        assets, transactions, portfolio = PortfolioFactory.create_simple_cash_portfolio()
        
        assert len(portfolio.positions) == 1
        assert portfolio.base_currency == Currency.CNY
        assert portfolio.total_value == Decimal('10025.00')  # 10000存款 + 25利息
        assert portfolio.total_invested == Decimal('10000.00')
        assert portfolio.calculate_total_return() == Decimal('25.00')
    
    def test_mixed_portfolio(self):
        """测试现金+固定收益混合投资组合"""
        assets, transactions, portfolio = PortfolioFactory.create_mixed_portfolio()
        
        # 基本指标验证
        assert len(portfolio.positions) == 2
        assert portfolio.base_currency == Currency.CNY
        
        # 计算总值：现金(50000+125) + 债券(30000+1050) = 81175
        expected_total = Decimal('81175.00')
        assert portfolio.total_value == expected_total
        
        # 投资成本：现金50000 + 债券30000 = 80000
        expected_invested = Decimal('80000.00')
        assert portfolio.total_invested == expected_invested
        
        # 收益：现金125 + 债券1050 = 1175
        expected_return = Decimal('1175.00')
        assert portfolio.calculate_total_return() == expected_return
        
        # 资产配置验证
        allocation = portfolio.calculate_asset_allocation()
        assert len(allocation) == 2
        
        # 现金配置：50125 / 81175 ≈ 0.6177 (61.77%)
        cash_allocation = allocation["CASH"]["percentage"]
        assert abs(cash_allocation - 61.77) < 0.1
        
        # 固定收益配置：31050 / 81175 ≈ 0.3823 (38.23%)
        bond_allocation = allocation["FIXED_INCOME"]["percentage"]
        assert abs(bond_allocation - 38.23) < 0.1
    
    def test_portfolio_with_builder(self):
        """测试使用构建器创建投资组合"""
        assets, transactions, portfolio = (DataBuilder()
            .with_cash_asset_full(deposit_amount=Decimal('20000'), interest_amount=Decimal('50'))
            .with_bond_asset_full(purchase_amount=Decimal('15000'), interest_amount=Decimal('525'))
            .build_data())
        
        assert len(assets) == 2
        assert len(transactions) == 4  # 2个资产 × 2笔交易
        
        # 总值：现金(20000+50) + 债券(15000+525) = 35575
        expected_total = Decimal('35575.00')
        assert portfolio.total_value == expected_total
    
    def test_portfolio_serialization(self):
        """测试投资组合序列化"""
        assets, transactions, portfolio = PortfolioFactory.create_simple_cash_portfolio()
        
        # 序列化
        data = portfolio.to_dict()
        assert data["base_currency"] == Currency.CNY.name  # 使用.name而不是.value
        assert len(data["positions"]) == 1
        
        # 注意：Portfolio类没有from_dict方法，这里只测试序列化
        # restored = Portfolio.from_dict(data)
        # assert restored.base_currency == portfolio.base_currency
        # assert len(restored.positions) == len(portfolio.positions)


class TestPhase1PortfolioSnapshot:
    """Phase 1 投资组合快照测试"""
    
    def test_snapshot_creation(self):
        """测试快照创建"""
        assets, transactions, portfolio = PortfolioFactory.create_mixed_portfolio()
        
        snapshot = PortfolioSnapshot.from_portfolio(
            portfolio=portfolio,
            description="现金+固定收益组合快照"
        )
        
        assert snapshot.description == "现金+固定收益组合快照"
        assert snapshot.total_value == portfolio.total_value
        assert snapshot.snapshot_date.date() == date.today()
        assert len(snapshot.position_snapshots) == len(portfolio.positions)
    
    def test_snapshot_comparison(self):
        """测试快照比较"""
        # 创建第一个快照（较小金额）
        assets1, transactions1, portfolio1 = (DataBuilder()
            .with_cash_asset(amount=Decimal('10000'))
            .build_data())
        snapshot1 = PortfolioSnapshot.from_portfolio(portfolio1, "快照1")
        # 手动设置快照日期
        snapshot1.snapshot_date = datetime(2024, 1, 1)
        
        # 创建第二个快照（较大金额）
        assets2, transactions2, portfolio2 = (DataBuilder()
            .with_cash_asset_full(deposit_amount=Decimal('15000'), interest_amount=Decimal('50'))
            .build_data())
        snapshot2 = PortfolioSnapshot.from_portfolio(portfolio2, "快照2")
        # 手动设置快照日期
        snapshot2.snapshot_date = datetime(2024, 2, 1)
        
        # 比较快照
        comparison = snapshot2.compare_with(snapshot1)
        
        # 价值变化：15050 - 10000 = 5050
        assert comparison["value_change"] == Decimal('5050.00')
        assert comparison["value_change_rate"] > 0
        assert comparison["time_span_days"] == 31  # 1月1日到2月1日


class TestPhase1DataConsistency:
    """Phase 1 数据一致性测试"""
    
    def test_transaction_asset_relationship(self):
        """测试交易与资产的关联关系"""
        asset = AssetFactory.create_cash_asset()
        transaction = TransactionFactory.create_cash_deposit(asset.asset_id)
        
        # 确保交易正确关联到资产
        assert transaction.asset_id == asset.asset_id
    
    def test_cash_position_calculation_consistency(self):
        """测试现金持仓计算一致性"""
        asset = AssetFactory.create_cash_asset()
        
        # 创建已知的交易序列
        transactions = [
            TransactionFactory.create_cash_deposit(asset.asset_id, amount=Decimal('1000')),
            TransactionFactory.create_cash_deposit(asset.asset_id, amount=Decimal('2000')),
            TransactionFactory.create_cash_interest(asset.asset_id, amount=Decimal('30')),
            TransactionFactory.create_cash_withdraw(asset.asset_id, amount=Decimal('500'))
        ]
        
        position = Position(asset=asset, transactions=transactions)
        
        # 手动计算预期值
        expected_net_invested = Decimal('2500')  # 1000 + 2000 - 500 (净投入)
        expected_return = Decimal('30')      # 利息
        expected_value = Decimal('2530')     # 净投入 + 收益
        
        assert position.net_invested == expected_net_invested
        assert position.calculate_total_return() == expected_return
        assert position.calculate_current_value() == expected_value
    
    def test_fixed_income_position_calculation_consistency(self):
        """测试固定收益持仓计算一致性"""
        asset = AssetFactory.create_fixed_income_asset()
        
        # 创建已知的交易序列
        transactions = [
            TransactionFactory.create_fixed_income_purchase(asset.asset_id, amount=Decimal('5000')),
            TransactionFactory.create_fixed_income_purchase(asset.asset_id, amount=Decimal('3000')),
            TransactionFactory.create_fixed_income_interest(asset.asset_id, amount=Decimal('280'))
        ]
        
        position = Position(asset=asset, transactions=transactions)
        
        # 手动计算预期值
        expected_invested = Decimal('8000')  # 5000 + 3000
        expected_return = Decimal('280')     # 利息
        expected_value = Decimal('8280')     # 投入 + 收益
        
        assert position.total_invested == expected_invested
        assert position.calculate_total_return() == expected_return
        assert position.calculate_current_value() == expected_value
    
    def test_portfolio_aggregation_consistency(self):
        """测试投资组合聚合一致性"""
        # 使用构建器创建已知数据
        builder = DataBuilder()
        builder.with_cash_asset(amount=Decimal('10000'))
        builder.with_bond_asset(amount=Decimal('5000'))
        
        assets, transactions, portfolio = builder.build_data()
        
        # 验证聚合计算
        expected_total = Decimal('15000')
        assert portfolio.total_value == expected_total
        
        # 验证各持仓总和等于组合总值
        positions_sum = sum(pos.calculate_current_value() for pos in portfolio.positions)
        assert positions_sum == portfolio.total_value
