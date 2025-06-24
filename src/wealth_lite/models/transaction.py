"""
WealthLite 交易模型

定义交易事件层的所有模型，采用继承结构：
- BaseTransaction: 通用交易基类
- CashTransaction: 现金类交易
- FixedIncomeTransaction: 固定收益交易
- EquityTransaction: 权益类交易
- RealEstateTransaction: 房产交易
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from .enums import TransactionType, Currency, InterestType, PaymentFrequency


@dataclass
class BaseTransaction(ABC):
    """
    通用交易基类
    
    职责：
    - 定义所有交易的共同属性
    - 提供交易的基础操作接口
    - 支持多货币和汇率转换
    """
    
    # 基础标识
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    asset_id: str = ""  # 关联到具体资产
    
    # 交易信息
    transaction_date: date = field(default_factory=date.today)
    transaction_type: TransactionType = TransactionType.DEPOSIT
    amount: Decimal = Decimal('0')
    currency: Currency = Currency.CNY
    
    # 汇率和基础货币
    exchange_rate: Decimal = Decimal('1.0')  # 对基础货币的汇率
    amount_base_currency: Decimal = Decimal('0')  # 基础货币金额
    
    # 附加信息
    notes: str = ""
    reference_number: str = ""  # 参考号码（银行流水号等）
    
    # 时间戳
    created_date: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """初始化后处理"""
        if not self.asset_id:
            raise ValueError("资产ID不能为空")
        
        if self.amount <= 0:
            raise ValueError("交易金额必须大于0")
            
        # 自动计算基础货币金额
        if self.amount_base_currency == 0:
            self.amount_base_currency = self.amount * self.exchange_rate

    @property
    def display_amount(self) -> str:
        """返回格式化的金额显示"""
        return f"{self.currency.symbol}{self.amount:,.2f}"

    @property
    def display_amount_base(self) -> str:
        """返回格式化的基础货币金额显示"""
        return f"{self.amount_base_currency:,.2f}"

    @property
    def is_income(self) -> bool:
        """判断是否为收入类型交易"""
        return self.transaction_type in TransactionType.get_income_types()

    @property
    def is_expense(self) -> bool:
        """判断是否为支出类型交易"""
        return self.transaction_type in TransactionType.get_expense_types()

    @property
    def is_investment(self) -> bool:
        """判断是否为投资类型交易"""
        return self.transaction_type in TransactionType.get_investment_types()

    def update_exchange_rate(self, new_rate: Decimal) -> None:
        """更新汇率并重新计算基础货币金额"""
        self.exchange_rate = new_rate
        self.amount_base_currency = self.amount * self.exchange_rate

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        base_dict = {
            'transaction_id': self.transaction_id,
            'asset_id': self.asset_id,
            'transaction_date': self.transaction_date.isoformat(),
            'transaction_type': self.transaction_type.name,
            'amount': str(self.amount),
            'currency': self.currency.name,
            'exchange_rate': str(self.exchange_rate),
            'amount_base_currency': str(self.amount_base_currency),
            'notes': self.notes,
            'reference_number': self.reference_number,
            'created_date': self.created_date.isoformat()
        }
        
        # 添加子类特有属性
        base_dict.update(self._get_specific_attributes())
        return base_dict

    @abstractmethod
    def _get_specific_attributes(self) -> Dict[str, Any]:
        """获取子类特有属性"""
        pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseTransaction':
        """从字典创建Transaction实例"""
        # 这个方法将在具体子类中实现
        raise NotImplementedError("子类必须实现from_dict方法")

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}({self.transaction_type.display_name}, {self.display_amount})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"{self.__class__.__name__}(id={self.transaction_id[:8]}..., "
                f"type={self.transaction_type.name}, amount={self.amount})")


@dataclass
class CashTransaction(BaseTransaction):
    """
    现金类交易
    
    适用于：活期存款、储蓄存款、货币基金等现金及等价物
    """
    
    # 现金特有属性
    account_type: str = "SAVINGS"  # CHECKING, SAVINGS, MONEY_MARKET
    interest_rate: Decimal = Decimal('0')  # 年利率（百分比）
    compound_frequency: str = "ANNUALLY"  # 复利频率

    def _get_specific_attributes(self) -> Dict[str, Any]:
        """获取现金交易特有属性"""
        return {
            'account_type': self.account_type,
            'interest_rate': str(self.interest_rate),
            'compound_frequency': self.compound_frequency
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CashTransaction':
        """从字典创建CashTransaction实例"""
        transaction_type = TransactionType[data.get('transaction_type', 'DEPOSIT')]
        currency = Currency[data.get('currency', 'CNY')]
        transaction_date = date.fromisoformat(data.get('transaction_date', date.today().isoformat()))
        created_date = datetime.fromisoformat(data.get('created_date', datetime.now().isoformat()))
        
        return cls(
            transaction_id=data.get('transaction_id', str(uuid.uuid4())),
            asset_id=data.get('asset_id', ''),
            transaction_date=transaction_date,
            transaction_type=transaction_type,
            amount=Decimal(data.get('amount', '0')),
            currency=currency,
            exchange_rate=Decimal(data.get('exchange_rate', '1.0')),
            amount_base_currency=Decimal(data.get('amount_base_currency', '0')),
            notes=data.get('notes', ''),
            reference_number=data.get('reference_number', ''),
            created_date=created_date,
            account_type=data.get('account_type', 'SAVINGS'),
            interest_rate=Decimal(data.get('interest_rate', '0')),
            compound_frequency=data.get('compound_frequency', 'ANNUALLY')
        )


@dataclass
class FixedIncomeTransaction(BaseTransaction):
    """
    固定收益交易
    
    适用于：定期存款、国债、企业债、债券基金等固定收益产品
    """
    
    # 固定收益特有属性
    annual_rate: Decimal = Decimal('0')  # 年利率（百分比）
    start_date: Optional[date] = None  # 起息日期
    maturity_date: Optional[date] = None  # 到期日期
    interest_type: InterestType = InterestType.SIMPLE  # 利息类型
    payment_frequency: PaymentFrequency = PaymentFrequency.MATURITY  # 付息频率
    face_value: Decimal = Decimal('0')  # 面值
    coupon_rate: Decimal = Decimal('0')  # 票面利率

    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()
        
        # 设置默认起息日期
        if self.start_date is None:
            self.start_date = self.transaction_date
            
        # 设置默认面值
        if self.face_value == 0:
            self.face_value = self.amount

    @property
    def days_to_maturity(self) -> Optional[int]:
        """计算距离到期日的天数"""
        if self.maturity_date:
            return (self.maturity_date - date.today()).days
        return None

    @property
    def is_matured(self) -> bool:
        """判断是否已到期"""
        if self.maturity_date:
            return date.today() >= self.maturity_date
        return False

    def _get_specific_attributes(self) -> Dict[str, Any]:
        """获取固定收益交易特有属性"""
        return {
            'annual_rate': str(self.annual_rate),
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'maturity_date': self.maturity_date.isoformat() if self.maturity_date else None,
            'interest_type': self.interest_type.name,
            'payment_frequency': self.payment_frequency.name,
            'face_value': str(self.face_value),
            'coupon_rate': str(self.coupon_rate)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FixedIncomeTransaction':
        """从字典创建FixedIncomeTransaction实例"""
        transaction_type = TransactionType[data.get('transaction_type', 'DEPOSIT')]
        currency = Currency[data.get('currency', 'CNY')]
        interest_type = InterestType[data.get('interest_type', 'SIMPLE')]
        payment_frequency = PaymentFrequency[data.get('payment_frequency', 'MATURITY')]
        
        transaction_date = date.fromisoformat(data.get('transaction_date', date.today().isoformat()))
        created_date = datetime.fromisoformat(data.get('created_date', datetime.now().isoformat()))
        
        start_date = None
        if data.get('start_date'):
            start_date = date.fromisoformat(data['start_date'])
            
        maturity_date = None
        if data.get('maturity_date'):
            maturity_date = date.fromisoformat(data['maturity_date'])
        
        return cls(
            transaction_id=data.get('transaction_id', str(uuid.uuid4())),
            asset_id=data.get('asset_id', ''),
            transaction_date=transaction_date,
            transaction_type=transaction_type,
            amount=Decimal(data.get('amount', '0')),
            currency=currency,
            exchange_rate=Decimal(data.get('exchange_rate', '1.0')),
            amount_base_currency=Decimal(data.get('amount_base_currency', '0')),
            notes=data.get('notes', ''),
            reference_number=data.get('reference_number', ''),
            created_date=created_date,
            annual_rate=Decimal(data.get('annual_rate', '0')),
            start_date=start_date,
            maturity_date=maturity_date,
            interest_type=interest_type,
            payment_frequency=payment_frequency,
            face_value=Decimal(data.get('face_value', '0')),
            coupon_rate=Decimal(data.get('coupon_rate', '0'))
        )


@dataclass
class EquityTransaction(BaseTransaction):
    """
    权益类交易
    
    适用于：股票、股票型基金、ETF等权益类投资
    """
    
    # 权益特有属性
    quantity: Decimal = Decimal('0')  # 交易数量（股数）
    price_per_share: Decimal = Decimal('0')  # 每股价格
    dividend_amount: Decimal = Decimal('0')  # 分红金额
    split_ratio: Decimal = Decimal('1')  # 拆股比例
    commission: Decimal = Decimal('0')  # 佣金费用

    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()
        
        # 自动计算金额（如果未设置）
        if self.amount == 0 and self.quantity > 0 and self.price_per_share > 0:
            self.amount = self.quantity * self.price_per_share + self.commission

    @property
    def total_cost(self) -> Decimal:
        """总成本（包含佣金）"""
        return self.quantity * self.price_per_share + self.commission

    def _get_specific_attributes(self) -> Dict[str, Any]:
        """获取权益交易特有属性"""
        return {
            'quantity': str(self.quantity),
            'price_per_share': str(self.price_per_share),
            'dividend_amount': str(self.dividend_amount),
            'split_ratio': str(self.split_ratio),
            'commission': str(self.commission)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EquityTransaction':
        """从字典创建EquityTransaction实例"""
        transaction_type = TransactionType[data.get('transaction_type', 'BUY')]
        currency = Currency[data.get('currency', 'CNY')]
        transaction_date = date.fromisoformat(data.get('transaction_date', date.today().isoformat()))
        created_date = datetime.fromisoformat(data.get('created_date', datetime.now().isoformat()))
        
        return cls(
            transaction_id=data.get('transaction_id', str(uuid.uuid4())),
            asset_id=data.get('asset_id', ''),
            transaction_date=transaction_date,
            transaction_type=transaction_type,
            amount=Decimal(data.get('amount', '0')),
            currency=currency,
            exchange_rate=Decimal(data.get('exchange_rate', '1.0')),
            amount_base_currency=Decimal(data.get('amount_base_currency', '0')),
            notes=data.get('notes', ''),
            reference_number=data.get('reference_number', ''),
            created_date=created_date,
            quantity=Decimal(data.get('quantity', '0')),
            price_per_share=Decimal(data.get('price_per_share', '0')),
            dividend_amount=Decimal(data.get('dividend_amount', '0')),
            split_ratio=Decimal(data.get('split_ratio', '1')),
            commission=Decimal(data.get('commission', '0'))
        )


@dataclass
class RealEstateTransaction(BaseTransaction):
    """
    房产交易
    
    适用于：住宅、商铺、REITs等不动产投资
    """
    
    # 房产特有属性
    property_area: Decimal = Decimal('0')  # 物业面积（平方米）
    price_per_unit: Decimal = Decimal('0')  # 单价（每平方米）
    rental_income: Decimal = Decimal('0')  # 租金收入
    property_type: str = "RESIDENTIAL"  # RESIDENTIAL, COMMERCIAL, LAND
    location: str = ""  # 位置
    tax_amount: Decimal = Decimal('0')  # 税费

    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()
        
        # 自动计算金额（如果未设置）
        if self.amount == 0 and self.property_area > 0 and self.price_per_unit > 0:
            self.amount = self.property_area * self.price_per_unit + self.tax_amount

    @property
    def total_cost(self) -> Decimal:
        """总成本（包含税费）"""
        return self.property_area * self.price_per_unit + self.tax_amount

    def _get_specific_attributes(self) -> Dict[str, Any]:
        """获取房产交易特有属性"""
        return {
            'property_area': str(self.property_area),
            'price_per_unit': str(self.price_per_unit),
            'rental_income': str(self.rental_income),
            'property_type': self.property_type,
            'location': self.location,
            'tax_amount': str(self.tax_amount)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RealEstateTransaction':
        """从字典创建RealEstateTransaction实例"""
        transaction_type = TransactionType[data.get('transaction_type', 'BUY')]
        currency = Currency[data.get('currency', 'CNY')]
        transaction_date = date.fromisoformat(data.get('transaction_date', date.today().isoformat()))
        created_date = datetime.fromisoformat(data.get('created_date', datetime.now().isoformat()))
        
        return cls(
            transaction_id=data.get('transaction_id', str(uuid.uuid4())),
            asset_id=data.get('asset_id', ''),
            transaction_date=transaction_date,
            transaction_type=transaction_type,
            amount=Decimal(data.get('amount', '0')),
            currency=currency,
            exchange_rate=Decimal(data.get('exchange_rate', '1.0')),
            amount_base_currency=Decimal(data.get('amount_base_currency', '0')),
            notes=data.get('notes', ''),
            reference_number=data.get('reference_number', ''),
            created_date=created_date,
            property_area=Decimal(data.get('property_area', '0')),
            price_per_unit=Decimal(data.get('price_per_unit', '0')),
            rental_income=Decimal(data.get('rental_income', '0')),
            property_type=data.get('property_type', 'RESIDENTIAL'),
            location=data.get('location', ''),
            tax_amount=Decimal(data.get('tax_amount', '0'))
        )


# 交易工厂函数
def create_transaction(asset_type: str, **kwargs) -> BaseTransaction:
    """根据资产类型创建对应的交易实例"""
    transaction_classes = {
        'CASH': CashTransaction,
        'FIXED_INCOME': FixedIncomeTransaction,
        'EQUITY': EquityTransaction,
        'REAL_ESTATE': RealEstateTransaction
    }
    
    transaction_class = transaction_classes.get(asset_type.upper())
    if not transaction_class:
        raise ValueError(f"不支持的资产类型: {asset_type}")
    
    return transaction_class(**kwargs) 