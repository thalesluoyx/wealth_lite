"""
WealthLite 枚举类型定义

定义系统中使用的所有枚举类型，确保类型安全和一致性。
"""

from enum import Enum
from typing import Dict, Any


class AssetType(Enum):
    """资产类型枚举"""
    CASH = "现金及等价物"
    FIXED_INCOME = "固定收益类"
    EQUITY = "权益类"
    REAL_ESTATE = "不动产"
    COMMODITY = "大宗商品"

    @property
    def display_name(self) -> str:
        """返回显示名称"""
        return self.value

    @classmethod
    def get_all_types(cls) -> Dict[str, str]:
        """获取所有资产类型的字典"""
        return {item.name: item.value for item in cls}


class TransactionType(Enum):
    """交易类型枚举"""
    BUY = "买入"
    SELL = "卖出"
    DEPOSIT = "存入"
    WITHDRAW = "取出"
    INTEREST = "利息收入"
    DIVIDEND = "分红收入"
    FEE = "手续费"
    TRANSFER_IN = "转入"
    TRANSFER_OUT = "转出"

    @property
    def display_name(self) -> str:
        """返回显示名称"""
        return self.value

    @classmethod
    def get_income_types(cls) -> list:
        """获取收入类型的交易"""
        return [cls.INTEREST, cls.DIVIDEND]

    @classmethod
    def get_expense_types(cls) -> list:
        """获取支出类型的交易"""
        return [cls.FEE, cls.SELL, cls.WITHDRAW, cls.TRANSFER_OUT]

    @classmethod
    def get_investment_types(cls) -> list:
        """获取投资类型的交易"""
        return [cls.BUY, cls.DEPOSIT, cls.TRANSFER_IN]


class Currency(Enum):
    """货币类型枚举"""
    CNY = "人民币"
    USD = "美元"
    EUR = "欧元"
    GBP = "英镑"
    JPY = "日元"
    HKD = "港币"
    AUD = "澳元"
    CAD = "加元"
    SGD = "新加坡元"
    KRW = "韩元"

    @property
    def display_name(self) -> str:
        """返回显示名称"""
        return self.value

    @property
    def symbol(self) -> str:
        """返回货币符号"""
        symbols = {
            'CNY': '¥',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥',
            'HKD': 'HK$',
            'AUD': 'A$',
            'CAD': 'C$',
            'SGD': 'S$',
            'KRW': '₩'
        }
        return symbols.get(self.name, self.name)

    @classmethod
    def get_major_currencies(cls) -> list:
        """获取主要货币"""
        return [cls.CNY, cls.USD, cls.EUR, cls.GBP, cls.JPY, cls.HKD]


class InterestType(Enum):
    """利息类型枚举"""
    SIMPLE = "单利"
    COMPOUND = "复利"
    FLOATING = "浮动利率"

    @property
    def display_name(self) -> str:
        """返回显示名称"""
        return self.value


class PaymentFrequency(Enum):
    """付息频率枚举"""
    MATURITY = "到期一次性"
    MONTHLY = "按月"
    QUARTERLY = "按季度"
    SEMI_ANNUALLY = "半年"
    ANNUALLY = "按年"

    @property
    def display_name(self) -> str:
        """返回显示名称"""
        return self.value

    @property
    def times_per_year(self) -> int:
        """返回每年付息次数"""
        frequency_map = {
            'MATURITY': 1,
            'MONTHLY': 12,
            'QUARTERLY': 4,
            'SEMI_ANNUALLY': 2,
            'ANNUALLY': 1
        }
        return frequency_map.get(self.name, 1)


class PositionStatus(Enum):
    """持仓状态枚举"""
    ACTIVE = "持有中"
    CLOSED = "已平仓"
    MATURED = "已到期"
    SUSPENDED = "暂停交易"

    @property
    def display_name(self) -> str:
        """返回显示名称"""
        return self.value


class RiskLevel(Enum):
    """风险等级枚举"""
    VERY_LOW = "极低风险"
    LOW = "低风险"
    MEDIUM = "中等风险"
    HIGH = "高风险"
    VERY_HIGH = "极高风险"

    @property
    def display_name(self) -> str:
        """返回显示名称"""
        return self.value

    @property
    def risk_score(self) -> int:
        """返回风险评分（1-5）"""
        scores = {
            'VERY_LOW': 1,
            'LOW': 2,
            'MEDIUM': 3,
            'HIGH': 4,
            'VERY_HIGH': 5
        }
        return scores.get(self.name, 3)


class LiquidityLevel(Enum):
    """流动性等级枚举"""
    VERY_HIGH = "极高流动性"
    HIGH = "高流动性"
    MEDIUM = "中等流动性"
    LOW = "低流动性"
    VERY_LOW = "极低流动性"

    @property
    def display_name(self) -> str:
        """返回显示名称"""
        return self.value

    @property
    def liquidity_score(self) -> int:
        """返回流动性评分（1-5）"""
        scores = {
            'VERY_HIGH': 5,
            'HIGH': 4,
            'MEDIUM': 3,
            'LOW': 2,
            'VERY_LOW': 1
        }
        return scores.get(self.name, 3)


# 枚举工具函数
def get_enum_by_value(enum_class: type, value: str) -> Any:
    """根据值获取枚举项"""
    for item in enum_class:
        if item.value == value:
            return item
    return None


def get_enum_by_name(enum_class: type, name: str) -> Any:
    """根据名称获取枚举项"""
    try:
        return enum_class[name.upper()]
    except KeyError:
        return None 