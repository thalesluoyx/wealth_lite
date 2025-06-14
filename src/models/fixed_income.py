"""
固定收益类产品数据模型

定义固定收益类产品的特殊属性和计算方法。
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from enum import Enum
import math


class FixedIncomeType(Enum):
    """固定收益类产品类型"""
    TERM_DEPOSIT = "定期存款"
    GOVERNMENT_BOND = "国债"
    CORPORATE_BOND = "企业债"
    BOND_FUND = "债券基金"


class InterestType(Enum):
    """利息类型"""
    SIMPLE = "单利"
    COMPOUND = "复利"
    FLOATING = "浮动利率"


class PaymentFrequency(Enum):
    """付息频率"""
    MATURITY = "到期一次性付息"
    ANNUAL = "年付"
    SEMI_ANNUAL = "半年付"
    QUARTERLY = "季付"
    MONTHLY = "月付"


class Currency(Enum):
    """支持的币种"""
    CNY = "人民币"
    HKD = "港元"
    USD = "美元"
    AUD = "澳元"


@dataclass
class FixedIncomeProduct:
    """固定收益类产品模型"""
    
    # 基本信息
    product_type: FixedIncomeType
    
    # 投资参数
    principal: Decimal  # 本金
    annual_rate: Decimal  # 年利率（百分比，如5.5表示5.5%）
    start_date: date  # 起息日期
    maturity_date: date  # 到期日期
    
    # 币种和汇率
    currency: Currency = Currency.CNY  # 投资币种
    exchange_rate: Decimal = Decimal('1.0')  # 对人民币汇率（1单位外币=X人民币）
    
    # 产品特性
    interest_type: InterestType = InterestType.COMPOUND  # 利息类型
    payment_frequency: PaymentFrequency = PaymentFrequency.MATURITY  # 付息频率
    
    # 可选参数
    current_value: Optional[Decimal] = None  # 当前价值（用于债券基金等）
    credit_rating: Optional[str] = None  # 信用评级（用于债券）
    issuer: Optional[str] = None  # 发行方
    coupon_rate: Optional[Decimal] = None  # 票面利率（用于债券）
    face_value: Optional[Decimal] = None  # 面值（用于债券）
    
    # 计算字段
    term_days: int = field(init=False)  # 投资期限（天数）
    term_years: Decimal = field(init=False)  # 投资期限（年数）
    
    def __post_init__(self):
        """初始化后处理"""
        self.term_days = (self.maturity_date - self.start_date).days
        self.term_years = Decimal(str(self.term_days / 365.25))
        
        # 如果没有设置当前价值，使用本金
        if self.current_value is None:
            self.current_value = self.principal
    
    def get_principal_in_cny(self) -> Decimal:
        """获取以人民币计价的本金"""
        return self.principal * self.exchange_rate
    
    def get_current_value_in_cny(self) -> Decimal:
        """获取以人民币计价的当前价值"""
        if self.current_value:
            return self.current_value * self.exchange_rate
        return self.get_principal_in_cny()
    
    def calculate_maturity_value(self) -> Decimal:
        """计算到期价值（原币种）"""
        if self.product_type == FixedIncomeType.TERM_DEPOSIT:
            return self._calculate_deposit_maturity_value()
        elif self.product_type in [FixedIncomeType.GOVERNMENT_BOND, FixedIncomeType.CORPORATE_BOND]:
            return self._calculate_bond_maturity_value()
        elif self.product_type == FixedIncomeType.BOND_FUND:
            return self._calculate_bond_fund_value()
        else:
            return self._calculate_simple_compound_value()
    
    def calculate_maturity_value_in_cny(self) -> Decimal:
        """计算以人民币计价的到期价值"""
        maturity_value = self.calculate_maturity_value()
        return maturity_value * self.exchange_rate
    
    def _calculate_deposit_maturity_value(self) -> Decimal:
        """计算定期存款到期价值"""
        rate = self.annual_rate / Decimal('100')
        
        if self.interest_type == InterestType.SIMPLE:
            # 单利：P * (1 + r * t)
            return self.principal * (Decimal('1') + rate * self.term_years)
        else:
            # 复利：P * (1 + r)^t
            return self.principal * (Decimal('1') + rate) ** self.term_years
    
    def _calculate_bond_maturity_value(self) -> Decimal:
        """计算债券到期价值"""
        if self.face_value and self.coupon_rate:
            # 使用票面价值和票面利率
            face_value = self.face_value
            coupon_rate = self.coupon_rate / Decimal('100')
        else:
            # 使用本金和年利率
            face_value = self.principal
            coupon_rate = self.annual_rate / Decimal('100')
        
        if self.payment_frequency == PaymentFrequency.MATURITY:
            # 到期一次性付息
            return face_value * (Decimal('1') + coupon_rate * self.term_years)
        else:
            # 定期付息，计算复利
            payments_per_year = self._get_payments_per_year()
            periods = int(self.term_years * payments_per_year)
            period_rate = coupon_rate / payments_per_year
            
            return face_value * (Decimal('1') + period_rate) ** periods
    
    def _calculate_bond_fund_value(self) -> Decimal:
        """计算债券基金价值（使用当前净值）"""
        if self.current_value:
            return self.current_value
        else:
            # 如果没有当前价值，按简单复利计算
            return self._calculate_simple_compound_value()
    
    def _calculate_simple_compound_value(self) -> Decimal:
        """简单复利计算"""
        rate = self.annual_rate / Decimal('100')
        return self.principal * (Decimal('1') + rate) ** self.term_years
    
    def _get_payments_per_year(self) -> Decimal:
        """获取每年付息次数"""
        frequency_map = {
            PaymentFrequency.ANNUAL: Decimal('1'),
            PaymentFrequency.SEMI_ANNUAL: Decimal('2'),
            PaymentFrequency.QUARTERLY: Decimal('4'),
            PaymentFrequency.MONTHLY: Decimal('12'),
            PaymentFrequency.MATURITY: Decimal('1')
        }
        return frequency_map.get(self.payment_frequency, Decimal('1'))
    
    def calculate_current_yield(self) -> Decimal:
        """计算当前收益率"""
        if self.current_value and self.current_value > 0:
            total_return = self.calculate_maturity_value() - self.current_value
            return (total_return / self.current_value) * Decimal('100')
        return Decimal('0')
    
    def calculate_annualized_yield(self) -> Decimal:
        """计算年化收益率"""
        # 对于固定收益类产品，年化收益率就是年利率
        # 除非是债券基金等需要根据当前净值计算的产品
        if self.product_type == FixedIncomeType.BOND_FUND and self.current_value and self.current_value != self.principal:
            # 债券基金使用实际收益率计算
            if self.term_years > 0 and self.current_value > 0:
                maturity_value = self.calculate_maturity_value()
                # 年化收益率 = (到期价值/当前价值)^(1/年数) - 1
                yield_ratio = maturity_value / self.current_value
                annualized_yield = yield_ratio ** (Decimal('1') / self.term_years) - Decimal('1')
                return annualized_yield * Decimal('100')
        else:
            # 对于定期存款、国债、企业债等固定收益产品，年化收益率就是年利率
            return self.annual_rate
        
        return Decimal('0')
    
    def calculate_ytm(self) -> Decimal:
        """计算到期收益率（YTM）"""
        # 对于简单产品，YTM等于年化收益率
        return self.calculate_annualized_yield()
    
    def get_days_to_maturity(self) -> int:
        """获取距离到期的天数"""
        today = date.today()
        if today <= self.maturity_date:
            return (self.maturity_date - today).days
        return 0
    
    def is_matured(self) -> bool:
        """判断是否已到期"""
        return date.today() >= self.maturity_date
    
    def get_accrued_interest(self) -> Decimal:
        """计算已计提利息（原币种）"""
        today = date.today()
        if today <= self.start_date:
            return Decimal('0')
        
        # 计算已持有天数
        held_days = min((today - self.start_date).days, self.term_days)
        held_years = Decimal(str(held_days / 365.25))
        
        # 计算已计提利息
        rate = self.annual_rate / Decimal('100')
        if self.interest_type == InterestType.SIMPLE:
            return self.principal * rate * held_years
        else:
            return self.principal * ((Decimal('1') + rate) ** held_years - Decimal('1'))
    
    def get_accrued_interest_in_cny(self) -> Decimal:
        """计算以人民币计价的已计提利息"""
        return self.get_accrued_interest() * self.exchange_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "product_type": self.product_type.value,
            "principal": str(self.principal),
            "annual_rate": str(self.annual_rate),
            "start_date": self.start_date.isoformat(),
            "maturity_date": self.maturity_date.isoformat(),
            "currency": self.currency.value,
            "exchange_rate": str(self.exchange_rate),
            "interest_type": self.interest_type.value,
            "payment_frequency": self.payment_frequency.value,
            "current_value": str(self.current_value) if self.current_value else None,
            "credit_rating": self.credit_rating,
            "issuer": self.issuer,
            "coupon_rate": str(self.coupon_rate) if self.coupon_rate else None,
            "face_value": str(self.face_value) if self.face_value else None,
            "term_days": self.term_days,
            "term_years": str(self.term_years)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FixedIncomeProduct":
        """从字典创建对象"""
        return cls(
            product_type=FixedIncomeType(data["product_type"]),
            principal=Decimal(data["principal"]),
            annual_rate=Decimal(data["annual_rate"]),
            start_date=date.fromisoformat(data["start_date"]),
            maturity_date=date.fromisoformat(data["maturity_date"]),
            currency=Currency(data.get("currency", "人民币")),
            exchange_rate=Decimal(data.get("exchange_rate", "1.0")),
            interest_type=InterestType(data["interest_type"]),
            payment_frequency=PaymentFrequency(data["payment_frequency"]),
            current_value=Decimal(data["current_value"]) if data.get("current_value") else None,
            credit_rating=data.get("credit_rating"),
            issuer=data.get("issuer"),
            coupon_rate=Decimal(data["coupon_rate"]) if data.get("coupon_rate") else None,
            face_value=Decimal(data["face_value"]) if data.get("face_value") else None
        )


class ExchangeRateManager:
    """汇率管理器"""
    
    # 默认汇率（相对于人民币）
    DEFAULT_RATES = {
        Currency.CNY: Decimal('1.0'),      # 人民币
        Currency.HKD: Decimal('0.92'),     # 港元
        Currency.USD: Decimal('7.25'),     # 美元
        Currency.AUD: Decimal('4.85'),     # 澳元
    }
    
    def __init__(self):
        self.rates = self.DEFAULT_RATES.copy()
    
    def get_rate(self, currency: Currency) -> Decimal:
        """获取指定币种对人民币的汇率"""
        return self.rates.get(currency, Decimal('1.0'))
    
    def set_rate(self, currency: Currency, rate: Decimal):
        """设置指定币种对人民币的汇率"""
        self.rates[currency] = rate
    
    def update_rates(self, rates: Dict[Currency, Decimal]):
        """批量更新汇率"""
        self.rates.update(rates)
    
    def convert_to_cny(self, amount: Decimal, from_currency: Currency) -> Decimal:
        """将指定币种金额转换为人民币"""
        rate = self.get_rate(from_currency)
        return amount * rate
    
    def convert_from_cny(self, cny_amount: Decimal, to_currency: Currency) -> Decimal:
        """将人民币金额转换为指定币种"""
        rate = self.get_rate(to_currency)
        if rate > 0:
            return cny_amount / rate
        return Decimal('0')
    
    def get_all_rates(self) -> Dict[Currency, Decimal]:
        """获取所有汇率"""
        return self.rates.copy()


class FixedIncomeCalculator:
    """固定收益类产品计算器"""
    
    @staticmethod
    def create_term_deposit(principal: Decimal, annual_rate: Decimal, 
                          start_date: date, term_months: int,
                          currency: Currency = Currency.CNY,
                          exchange_rate: Decimal = Decimal('1.0'),
                          interest_type: InterestType = InterestType.COMPOUND) -> FixedIncomeProduct:
        """创建定期存款产品"""
        from dateutil.relativedelta import relativedelta
        maturity_date = start_date + relativedelta(months=term_months)
        
        return FixedIncomeProduct(
            product_type=FixedIncomeType.TERM_DEPOSIT,
            principal=principal,
            annual_rate=annual_rate,
            start_date=start_date,
            maturity_date=maturity_date,
            currency=currency,
            exchange_rate=exchange_rate,
            interest_type=interest_type,
            payment_frequency=PaymentFrequency.MATURITY
        )
    
    @staticmethod
    def create_government_bond(principal: Decimal, coupon_rate: Decimal,
                             start_date: date, maturity_date: date,
                             currency: Currency = Currency.CNY,
                             exchange_rate: Decimal = Decimal('1.0'),
                             payment_frequency: PaymentFrequency = PaymentFrequency.ANNUAL,
                             face_value: Optional[Decimal] = None) -> FixedIncomeProduct:
        """创建国债产品"""
        return FixedIncomeProduct(
            product_type=FixedIncomeType.GOVERNMENT_BOND,
            principal=principal,
            annual_rate=coupon_rate,
            start_date=start_date,
            maturity_date=maturity_date,
            currency=currency,
            exchange_rate=exchange_rate,
            interest_type=InterestType.COMPOUND,
            payment_frequency=payment_frequency,
            coupon_rate=coupon_rate,
            face_value=face_value or principal,
            credit_rating="AAA"
        )
    
    @staticmethod
    def create_corporate_bond(principal: Decimal, coupon_rate: Decimal,
                            start_date: date, maturity_date: date,
                            issuer: str, credit_rating: str = "AA",
                            currency: Currency = Currency.CNY,
                            exchange_rate: Decimal = Decimal('1.0'),
                            payment_frequency: PaymentFrequency = PaymentFrequency.ANNUAL,
                            face_value: Optional[Decimal] = None) -> FixedIncomeProduct:
        """创建企业债产品"""
        return FixedIncomeProduct(
            product_type=FixedIncomeType.CORPORATE_BOND,
            principal=principal,
            annual_rate=coupon_rate,
            start_date=start_date,
            maturity_date=maturity_date,
            currency=currency,
            exchange_rate=exchange_rate,
            interest_type=InterestType.COMPOUND,
            payment_frequency=payment_frequency,
            coupon_rate=coupon_rate,
            face_value=face_value or principal,
            issuer=issuer,
            credit_rating=credit_rating
        )
    
    @staticmethod
    def create_bond_fund(principal: Decimal, expected_annual_return: Decimal,
                        start_date: date, current_value: Decimal,
                        currency: Currency = Currency.CNY,
                        exchange_rate: Decimal = Decimal('1.0')) -> FixedIncomeProduct:
        """创建债券基金产品"""
        # 债券基金没有固定到期日，使用一年后作为评估期
        from dateutil.relativedelta import relativedelta
        evaluation_date = start_date + relativedelta(years=1)
        
        return FixedIncomeProduct(
            product_type=FixedIncomeType.BOND_FUND,
            principal=principal,
            annual_rate=expected_annual_return,
            start_date=start_date,
            maturity_date=evaluation_date,
            currency=currency,
            exchange_rate=exchange_rate,
            interest_type=InterestType.COMPOUND,
            payment_frequency=PaymentFrequency.MATURITY,
            current_value=current_value
        ) 