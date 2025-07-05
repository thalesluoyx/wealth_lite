"""
WealthLite 枚举类型定义

定义系统中使用的所有枚举类型，确保类型安全和一致性。
所有枚举类都集中在此文件中，便于管理和维护。

枚举分组：
1. 核心业务枚举 - 资产、交易、货币
2. 资产分类枚举 - 资产子类型
3. 金融产品枚举 - 利息、付息频率
4. 状态评级枚举 - 持仓状态、风险等级、流动性等级
5. 工具函数 - 枚举查找和转换

分类架构：
- 第一层：AssetType（资产类型）- 现金及等价物、固定收益类、权益类
- 第二层：AssetSubType（资产子类型）- 具体的资产细分类别
"""

from enum import Enum
from typing import Dict, Any, List


# ============================================================================
# 核心业务枚举
# ============================================================================


class AssetType(Enum):
    """
    资产类型枚举（第一层分类）
    
    定义系统支持的三大资产类型，作为资产分类的顶层架构。
    采用简化的三分法，便于管理和理解。
    """
    CASH = "现金及等价物"
    FIXED_INCOME = "固定收益类"
    EQUITY = "权益类"

    @property
    def display_name(self) -> str:
        """返回显示名称"""
        return self.value

    @classmethod
    def get_all_types(cls) -> Dict[str, str]:
        """获取所有资产类型的字典 {name: value}"""
        return {item.name: item.value for item in cls}

    @classmethod
    def get_liquid_types(cls) -> List['AssetType']:
        """获取流动性较高的资产类型"""
        return [cls.CASH, cls.EQUITY]

    @classmethod
    def get_stable_types(cls) -> List['AssetType']:
        """获取相对稳定的资产类型"""
        return [cls.CASH, cls.FIXED_INCOME]


class TransactionType(Enum):
    """
    交易类型枚举
    
    定义系统支持的所有交易类型，用于交易记录和资金流向分析。
    """
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
    def get_income_types(cls) -> List['TransactionType']:
        """获取收入类型的交易"""
        return [cls.INTEREST, cls.DIVIDEND]

    @classmethod
    def get_expense_types(cls) -> List['TransactionType']:
        """获取支出类型的交易"""
        return [cls.FEE, cls.SELL, cls.WITHDRAW, cls.TRANSFER_OUT]

    @classmethod
    def get_investment_types(cls) -> List['TransactionType']:
        """获取投资类型的交易"""
        return [cls.BUY, cls.DEPOSIT, cls.TRANSFER_IN]

    @property
    def is_income(self) -> bool:
        """判断是否为收入类型"""
        return self in self.get_income_types()

    @property
    def is_expense(self) -> bool:
        """判断是否为支出类型"""
        return self in self.get_expense_types()


class Currency(Enum):
    """
    货币类型枚举
    
    定义系统支持的所有货币类型，用于多币种资产管理和汇率转换。
    """
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
    def get_major_currencies(cls) -> List['Currency']:
        """获取主要货币"""
        return [cls.CNY, cls.USD, cls.EUR, cls.GBP, cls.JPY, cls.HKD]

    @classmethod
    def get_all_symbols(cls) -> Dict[str, str]:
        """获取所有货币符号字典 {name: symbol}"""
        return {item.name: item.symbol for item in cls}


# ============================================================================
# 资产分类枚举
# ============================================================================

class AssetSubType(Enum):
    """
    资产子类型枚举（第二层分类）
    
    定义资产的具体细分类别，与AssetType形成两层分类架构。
    提供精确的资产分类管理，便于投资组合分析和风险控制。
    """
    # 现金及等价物
    CHECKING_ACCOUNT = "活期存款"
    MONEY_MARKET_FUND = "货币市场基金"
    
    # 固定收益类
    TIME_DEPOSIT = "定期存款"
    FOREIGN_CURRENCY_DEPOSIT = "外币定期存款"
    BANK_WEALTH_PRODUCT = "银行理财"
    GOVERNMENT_BOND = "政府债券"
    CORPORATE_BOND = "企业债券"

    # 权益类
    DOMESTIC_STOCK = "A股股票"
    FOREIGN_STOCK = "海外股票"
    MUTUAL_FUND = "公募基金"
    ETF = "交易所基金"

    @property
    def display_name(self) -> str:
        """返回显示名称"""
        return self.value

    @classmethod
    def get_all_subtypes(cls) -> Dict[str, str]:
        """获取所有资产子类型的字典 {name: value}"""
        return {item.name: item.value for item in cls}

    @classmethod
    def get_subtypes_by_asset_type(cls, asset_type: AssetType) -> List['AssetSubType']:
        """根据资产类型获取对应的子类型"""
        category_mapping = {
            AssetType.CASH: [
                cls.CHECKING_ACCOUNT, 
                 cls.MONEY_MARKET_FUND
            ],
            AssetType.FIXED_INCOME: [
                cls.TIME_DEPOSIT,cls.FOREIGN_CURRENCY_DEPOSIT, cls.BANK_WEALTH_PRODUCT,
                cls.GOVERNMENT_BOND, cls.CORPORATE_BOND
            ],
            AssetType.EQUITY: [
                cls.DOMESTIC_STOCK, cls.FOREIGN_STOCK, cls.MUTUAL_FUND, 
                cls.ETF
            ]
        }
        return category_mapping.get(asset_type, [])

    def get_asset_type(self) -> AssetType:
        """获取当前资产子类型对应的资产类型"""
        # 现金及等价物
        if self in [self.CHECKING_ACCOUNT, 
                   self.MONEY_MARKET_FUND]:
            return AssetType.CASH
        # 固定收益类
        elif self in [
                      self.TIME_DEPOSIT,  self.FOREIGN_CURRENCY_DEPOSIT, self.BANK_WEALTH_PRODUCT,
                      self.GOVERNMENT_BOND, self.CORPORATE_BOND]:
            return AssetType.FIXED_INCOME
        # 权益类
        elif self in [self.DOMESTIC_STOCK, self.FOREIGN_STOCK, self.MUTUAL_FUND,
                     self.ETF]:
            return AssetType.EQUITY
        else:
            return AssetType.CASH  # 默认返回现金类


# ============================================================================
# 金融产品枚举
# ============================================================================


class InterestType(Enum):
    """
    利息类型枚举
    
    定义固定收益产品的利息计算方式。
    """
    SIMPLE = "单利"
    COMPOUND = "复利"
    FLOATING = "浮动利率"

    @property
    def display_name(self) -> str:
        """返回显示名称"""
        return self.value


class PaymentFrequency(Enum):
    """
    付息频率枚举
    
    定义固定收益产品的付息频率，用于收益计算。
    """
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

    @classmethod
    def get_frequent_types(cls) -> List['PaymentFrequency']:
        """获取高频付息类型"""
        return [cls.MONTHLY, cls.QUARTERLY]


# ============================================================================
# 状态评级枚举
# ============================================================================


class PositionStatus(Enum):
    """
    持仓状态枚举
    
    定义投资持仓的各种状态，用于持仓管理和状态跟踪。
    """
    ACTIVE = "持有中"
    CLOSED = "已平仓"
    MATURED = "已到期"
    SUSPENDED = "暂停交易"

    @property
    def display_name(self) -> str:
        """返回显示名称"""
        return self.value

    @property
    def is_active(self) -> bool:
        """判断是否为活跃状态"""
        return self == self.ACTIVE

    @classmethod
    def get_inactive_statuses(cls) -> List['PositionStatus']:
        """获取非活跃状态"""
        return [cls.CLOSED, cls.MATURED, cls.SUSPENDED]


class RiskLevel(Enum):
    """
    风险等级枚举
    
    定义投资产品的风险等级，用于风险评估和资产配置。
    """
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

    @classmethod
    def get_conservative_levels(cls) -> List['RiskLevel']:
        """获取保守型风险等级"""
        return [cls.VERY_LOW, cls.LOW]

    @classmethod
    def get_aggressive_levels(cls) -> List['RiskLevel']:
        """获取激进型风险等级"""
        return [cls.HIGH, cls.VERY_HIGH]


class LiquidityLevel(Enum):
    """
    流动性等级枚举
    
    定义投资产品的流动性等级，用于流动性管理和资产配置。
    """
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

    @classmethod
    def get_high_liquidity_levels(cls) -> List['LiquidityLevel']:
        """获取高流动性等级"""
        return [cls.VERY_HIGH, cls.HIGH]

    @classmethod
    def get_low_liquidity_levels(cls) -> List['LiquidityLevel']:
        """获取低流动性等级"""
        return [cls.LOW, cls.VERY_LOW]


# ============================================================================
# 枚举工具函数
# ============================================================================


def get_enum_by_value(enum_class: type, value: str) -> Any:
    """
    根据值获取枚举项
    
    Args:
        enum_class: 枚举类
        value: 枚举值（中文显示名称）
    
    Returns:
        对应的枚举项，如果未找到则返回 None
    """
    for item in enum_class:
        if item.value == value:
            return item
    return None


def get_enum_by_name(enum_class: type, name: str) -> Any:
    """
    根据名称获取枚举项
    
    Args:
        enum_class: 枚举类
        name: 枚举名称（英文键名）
    
    Returns:
        对应的枚举项，如果未找到则返回 None
    """
    try:
        return enum_class[name.upper()]
    except KeyError:
        return None


def get_all_enum_classes() -> Dict[str, type]:
    """
    获取所有枚举类的字典
    
    Returns:
        字典，键为类名，值为枚举类
    """
    return {
        'AssetType': AssetType,
        'TransactionType': TransactionType,
        'Currency': Currency,
        'AssetSubType': AssetSubType,
        'InterestType': InterestType,
        'PaymentFrequency': PaymentFrequency,
        'PositionStatus': PositionStatus,
        'RiskLevel': RiskLevel,
        'LiquidityLevel': LiquidityLevel,
    }


def validate_enum_value(enum_class: type, value: str) -> bool:
    """
    验证值是否为有效的枚举值
    
    Args:
        enum_class: 枚举类
        value: 要验证的值
    
    Returns:
        True 如果值有效，否则 False
    """
    return get_enum_by_value(enum_class, value) is not None


def validate_enum_name(enum_class: type, name: str) -> bool:
    """
    验证名称是否为有效的枚举名称
    
    Args:
        enum_class: 枚举类
        name: 要验证的名称
    
    Returns:
        True 如果名称有效，否则 False
    """
    return get_enum_by_name(enum_class, name) is not None


# ============================================================================
# 枚举常量集合（用于快速访问）
# ============================================================================

# 所有核心枚举类的列表
CORE_ENUMS = [AssetType, TransactionType, Currency]

# 所有分类枚举类的列表（简化为只有资产子类型）
CATEGORY_ENUMS = [AssetSubType]

# 所有金融产品枚举类的列表
FINANCIAL_ENUMS = [InterestType, PaymentFrequency]

# 所有状态评级枚举类的列表
STATUS_ENUMS = [PositionStatus, RiskLevel, LiquidityLevel]

# 所有枚举类的列表
ALL_ENUMS = CORE_ENUMS + CATEGORY_ENUMS + FINANCIAL_ENUMS + STATUS_ENUMS 