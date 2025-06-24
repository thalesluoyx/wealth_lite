"""
WealthLite 数据模型包

包含系统的核心数据模型，采用分层架构设计：
- 枚举类型：AssetType, TransactionType, Currency等
- 资产定义：Asset类
- 交易事件：BaseTransaction及其子类
- 持仓计算：Position类
- 投资组合：Portfolio, PortfolioSnapshot类
"""

from .enums import (
    AssetType, TransactionType, Currency, InterestType, PaymentFrequency,
    PositionStatus, RiskLevel, LiquidityLevel
)
from .asset import Asset
from .transaction import (
    BaseTransaction,
    CashTransaction,
    FixedIncomeTransaction,
    EquityTransaction,
    RealEstateTransaction
)
from .position import Position
from .portfolio import Portfolio, PortfolioSnapshot

__all__ = [
    # 枚举类型
    "AssetType",
    "TransactionType", 
    "Currency",
    "InterestType",
    "PaymentFrequency",
    "PositionStatus",
    "RiskLevel",
    "LiquidityLevel",
    
    # 核心模型
    "Asset",
    "BaseTransaction",
    "CashTransaction",
    "FixedIncomeTransaction", 
    "EquityTransaction",
    "RealEstateTransaction",
    "Position",
    "Portfolio",
    "PortfolioSnapshot"
] 