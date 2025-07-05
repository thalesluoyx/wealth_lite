"""
WealthLite 测试数据工厂

提供创建各种测试对象的工厂方法，确保测试数据的一致性和可重用性。
"""

import uuid
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any

from src.wealth_lite.models import (
    Asset, AssetType, AssetSubType, Currency, RiskLevel, LiquidityLevel,
    BaseTransaction, CashTransaction, FixedIncomeTransaction,
    TransactionType, InterestType, PaymentFrequency, Position, Portfolio
)

# Phase 1: 只导入现金和固定收益相关的模型
# EquityTransaction, RealEstateTransaction 将在Phase 2/3中添加


class AssetFactory:
    """资产对象工厂 - Phase 1版本"""
    
    @staticmethod
    def create_cash_asset(**kwargs) -> Asset:
        """创建现金类资产"""
        defaults = {
            'asset_name': f"测试现金资产-{uuid.uuid4().hex[:8]}",
            'asset_type': AssetType.CASH,
            'asset_subtype': AssetSubType.CHECKING_ACCOUNT,
            'currency': Currency.CNY,
            'risk_level': RiskLevel.VERY_LOW,
            'liquidity_level': LiquidityLevel.VERY_HIGH,
            'description': "测试用现金资产"
        }
        defaults.update(kwargs)
        return Asset(**defaults)
    
    @staticmethod
    def create_fixed_income_asset(**kwargs) -> Asset:
        """创建固定收益资产"""
        defaults = {
            'asset_name': f"测试债券-{uuid.uuid4().hex[:8]}",
            'asset_type': AssetType.FIXED_INCOME,
            'asset_subtype': AssetSubType.GOVERNMENT_BOND,
            'currency': Currency.CNY,
            'risk_level': RiskLevel.LOW,
            'liquidity_level': LiquidityLevel.MEDIUM,
            'description': "测试用固定收益资产"
        }
        defaults.update(kwargs)
        return Asset(**defaults)
    
    # Phase 2+ 资产类型将在后续版本中添加
    # @staticmethod
    # def create_equity_asset(**kwargs) -> Asset:
    #     """创建权益类资产 - Phase 2"""
    #     pass
    
    # @staticmethod  
    # def create_real_estate_asset(**kwargs) -> Asset:
    #     """创建房产资产 - Phase 3"""
    #     pass


class TransactionFactory:
    """交易对象工厂 - Phase 1版本"""
    
    @staticmethod
    def create_cash_deposit(asset_id: str, **kwargs) -> CashTransaction:
        """创建现金存款交易"""
        defaults = {
            'asset_id': asset_id,
            'transaction_type': TransactionType.DEPOSIT,
            'transaction_date': date.today(),
            'amount': Decimal('1000.00'),
            'currency': Currency.CNY,
            'notes': "测试存款",
            'account_type': "SAVINGS",
            'interest_rate': Decimal('2.5')
        }
        defaults.update(kwargs)
        return CashTransaction(**defaults)
    
    @staticmethod
    def create_cash_withdraw(asset_id: str, **kwargs) -> CashTransaction:
        """创建现金取出交易"""
        defaults = {
            'asset_id': asset_id,
            'transaction_type': TransactionType.WITHDRAW,
            'transaction_date': date.today(),
            'amount': Decimal('500.00'),
            'currency': Currency.CNY,
            'notes': "测试取出",
            'account_type': "SAVINGS"
        }
        defaults.update(kwargs)
        return CashTransaction(**defaults)
    
    @staticmethod
    def create_cash_interest(asset_id: str, **kwargs) -> CashTransaction:
        """创建利息收入交易"""
        defaults = {
            'asset_id': asset_id,
            'transaction_type': TransactionType.INTEREST,
            'transaction_date': date.today(),
            'amount': Decimal('20.83'),
            'currency': Currency.CNY,
            'notes': "利息收入",
            'account_type': "SAVINGS"
        }
        defaults.update(kwargs)
        return CashTransaction(**defaults)
    
    @staticmethod
    def create_fixed_income_purchase(asset_id: str, **kwargs) -> FixedIncomeTransaction:
        """创建固定收益购买交易"""
        defaults = {
            'asset_id': asset_id,
            'transaction_type': TransactionType.BUY,
            'transaction_date': date.today(),
            'amount': Decimal('10000.00'),
            'currency': Currency.CNY,
            'notes': "购买债券",
            'annual_rate': Decimal('3.5'),
            'maturity_date': date.today() + timedelta(days=365),
            'interest_type': InterestType.SIMPLE,
            'payment_frequency': PaymentFrequency.ANNUALLY,
            'face_value': Decimal('10000.00')
        }
        defaults.update(kwargs)
        return FixedIncomeTransaction(**defaults)
    
    @staticmethod
    def create_fixed_income_interest(asset_id: str, **kwargs) -> FixedIncomeTransaction:
        """创建固定收益利息收入交易"""
        defaults = {
            'asset_id': asset_id,
            'transaction_type': TransactionType.INTEREST,
            'transaction_date': date.today(),
            'amount': Decimal('350.00'),
            'currency': Currency.CNY,
            'notes': "债券利息收入",
            'annual_rate': Decimal('3.5'),
            'interest_type': InterestType.SIMPLE
        }
        defaults.update(kwargs)
        return FixedIncomeTransaction(**defaults)
    
    # Phase 2+ 交易类型将在后续版本中添加
    # @staticmethod
    # def create_equity_purchase(asset_id: str, **kwargs) -> EquityTransaction:
    #     """创建股票购买交易 - Phase 2"""
    #     pass
        
    # @staticmethod
    # def create_real_estate_purchase(asset_id: str, **kwargs) -> RealEstateTransaction:
    #     """创建房产购买交易 - Phase 3"""
    #     pass


class PortfolioFactory:
    """投资组合工厂 - Phase 1版本"""
    
    @staticmethod
    def create_simple_cash_portfolio() -> tuple[list[Asset], list[BaseTransaction], Portfolio]:
        """创建简单的现金投资组合"""
        # 创建现金资产
        cash_asset = AssetFactory.create_cash_asset(asset_name="简单现金组合")
        
        # 创建交易
        deposit = TransactionFactory.create_cash_deposit(cash_asset.asset_id, amount=Decimal('10000'))
        interest = TransactionFactory.create_cash_interest(cash_asset.asset_id, amount=Decimal('25'))
        
        # 创建持仓
        position = Position(asset=cash_asset, transactions=[deposit, interest])
        
        # 创建投资组合
        portfolio = Portfolio(positions=[position], base_currency=Currency.CNY)
        
        return [cash_asset], [deposit, interest], portfolio
    
    @staticmethod
    def create_mixed_portfolio() -> tuple[list[Asset], list[BaseTransaction], Portfolio]:
        """创建现金+固定收益混合投资组合 - Phase 1专用"""
        assets = []
        transactions = []
        positions = []
        
        # 现金资产
        cash_asset = AssetFactory.create_cash_asset(asset_name="混合组合-现金")
        cash_deposit = TransactionFactory.create_cash_deposit(
            cash_asset.asset_id, amount=Decimal('50000')
        )
        cash_interest = TransactionFactory.create_cash_interest(
            cash_asset.asset_id, amount=Decimal('125')
        )
        assets.append(cash_asset)
        transactions.extend([cash_deposit, cash_interest])
        positions.append(Position(asset=cash_asset, transactions=[cash_deposit, cash_interest]))
        
        # 固定收益资产
        bond_asset = AssetFactory.create_fixed_income_asset(asset_name="混合组合-债券")
        bond_purchase = TransactionFactory.create_fixed_income_purchase(
            bond_asset.asset_id, amount=Decimal('30000')
        )
        bond_interest = TransactionFactory.create_fixed_income_interest(
            bond_asset.asset_id, amount=Decimal('1050')
        )
        assets.append(bond_asset)
        transactions.extend([bond_purchase, bond_interest])
        positions.append(Position(asset=bond_asset, transactions=[bond_purchase, bond_interest]))
        
        # 创建投资组合
        portfolio = Portfolio(positions=positions, base_currency=Currency.CNY)
        
        return assets, transactions, portfolio
    
    # 为了向后兼容，保留原方法名但指向新的混合组合
    @staticmethod
    def create_diversified_portfolio() -> tuple[list[Asset], list[BaseTransaction], Portfolio]:
        """创建多元化投资组合 - Phase 1版本（现金+固定收益）"""
        return PortfolioFactory.create_mixed_portfolio()


class DataBuilder:
    """测试数据构建器 - Phase 1版本（链式调用风格）"""
    
    def __init__(self):
        self.assets: list[Asset] = []
        self.transactions: list[BaseTransaction] = []
        self.positions: list[Position] = []
    
    def with_cash_asset(self, amount: Decimal = Decimal('10000'), **kwargs) -> 'DataBuilder':
        """添加现金资产和存款交易"""
        asset = AssetFactory.create_cash_asset(**kwargs)
        transaction = TransactionFactory.create_cash_deposit(asset.asset_id, amount=amount)
        
        self.assets.append(asset)
        self.transactions.append(transaction)
        self.positions.append(Position(asset=asset, transactions=[transaction]))
        
        return self
    
    def with_cash_asset_full(self, deposit_amount: Decimal = Decimal('10000'), 
                            interest_amount: Decimal = Decimal('25'), **kwargs) -> 'DataBuilder':
        """添加现金资产和完整交易（存款+利息）"""
        asset = AssetFactory.create_cash_asset(**kwargs)
        deposit = TransactionFactory.create_cash_deposit(asset.asset_id, amount=deposit_amount)
        interest = TransactionFactory.create_cash_interest(asset.asset_id, amount=interest_amount)
        
        self.assets.append(asset)
        self.transactions.extend([deposit, interest])
        self.positions.append(Position(asset=asset, transactions=[deposit, interest]))
        
        return self
    
    def with_bond_asset(self, amount: Decimal = Decimal('10000'), **kwargs) -> 'DataBuilder':
        """添加债券资产和购买交易"""
        asset = AssetFactory.create_fixed_income_asset(**kwargs)
        transaction = TransactionFactory.create_fixed_income_purchase(asset.asset_id, amount=amount)
        
        self.assets.append(asset)
        self.transactions.append(transaction)
        self.positions.append(Position(asset=asset, transactions=[transaction]))
        
        return self
    
    def with_bond_asset_full(self, purchase_amount: Decimal = Decimal('10000'),
                            interest_amount: Decimal = Decimal('350'), **kwargs) -> 'DataBuilder':
        """添加债券资产和完整交易（购买+利息）"""
        asset = AssetFactory.create_fixed_income_asset(**kwargs)
        purchase = TransactionFactory.create_fixed_income_purchase(asset.asset_id, amount=purchase_amount)
        interest = TransactionFactory.create_fixed_income_interest(asset.asset_id, amount=interest_amount)
        
        self.assets.append(asset)
        self.transactions.extend([purchase, interest])
        self.positions.append(Position(asset=asset, transactions=[purchase, interest]))
        
        return self
    
    # Phase 2+ 资产类型将在后续版本中添加
    # def with_stock_asset(self, amount: Decimal = Decimal('5000'), **kwargs) -> 'TestDataBuilder':
    #     """添加股票资产和购买交易 - Phase 2"""
    #     pass
    
    def build_portfolio(self, base_currency: Currency = Currency.CNY) -> Portfolio:
        """构建投资组合"""
        return Portfolio(positions=self.positions.copy(), base_currency=base_currency)
    
    def build_data(self) -> tuple[list[Asset], list[BaseTransaction], Portfolio]:
        """构建所有数据"""
        portfolio = self.build_portfolio()
        return self.assets.copy(), self.transactions.copy(), portfolio 