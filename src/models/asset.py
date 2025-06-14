"""
资产数据模型

定义单个资产的数据结构和相关操作方法。
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from decimal import Decimal
import uuid


@dataclass
class AssetTransaction:
    """资产变动记录"""
    
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    transaction_date: date = field(default_factory=date.today)
    transaction_type: str = ""  # 变动类型：买入、卖出、分红、转移等
    amount: Decimal = Decimal("0")  # 变动金额
    quantity: Optional[Decimal] = None  # 变动数量（可选）
    price: Optional[Decimal] = None  # 单价（可选）
    description: str = ""  # 备注说明
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "transaction_id": self.transaction_id,
            "transaction_date": self.transaction_date.isoformat(),
            "transaction_type": self.transaction_type,
            "amount": str(self.amount),
            "quantity": str(self.quantity) if self.quantity else None,
            "price": str(self.price) if self.price else None,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "AssetTransaction":
        """从字典创建交易记录对象"""
        return cls(
            transaction_id=data["transaction_id"],
            transaction_date=date.fromisoformat(data["transaction_date"]),
            transaction_type=data["transaction_type"],
            amount=Decimal(data["amount"]),
            quantity=Decimal(data["quantity"]) if data.get("quantity") else None,
            price=Decimal(data["price"]) if data.get("price") else None,
            description=data.get("description", "")
        )


@dataclass
class Asset:
    """资产模型"""
    
    # 基本信息
    asset_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    asset_name: str = ""  # 资产名称
    primary_category: str = ""  # 一级分类
    secondary_category: str = ""  # 二级分类
    
    # 投资数据
    initial_amount: Decimal = Decimal("0")  # 初始投入金额
    current_value: Decimal = Decimal("0")  # 当前价值
    start_date: date = field(default_factory=date.today)  # 投入日期
    last_update_date: date = field(default_factory=date.today)  # 最后更新日期
    
    # 币种和汇率信息
    currency: str = "人民币"  # 投资币种
    exchange_rate: Decimal = Decimal("1.0")  # 对人民币汇率（1单位外币=X人民币）
    
    # 可选信息
    description: str = ""  # 资产描述
    tags: List[str] = field(default_factory=list)  # 自定义标签
    
    # 固定收益类产品特殊属性
    annual_rate: Optional[Decimal] = None  # 年利率（百分比）
    maturity_date: Optional[date] = None  # 到期日期
    interest_type: Optional[str] = None  # 利息类型：单利、复利、浮动利率
    payment_frequency: Optional[str] = None  # 付息频率
    credit_rating: Optional[str] = None  # 信用评级
    issuer: Optional[str] = None  # 发行方
    coupon_rate: Optional[Decimal] = None  # 票面利率
    face_value: Optional[Decimal] = None  # 面值
    
    # 交易历史
    transactions: List[AssetTransaction] = field(default_factory=list)
    
    # 元数据
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    
    def is_fixed_income(self) -> bool:
        """判断是否为固定收益类产品"""
        return self.primary_category == "固定收益类"
    
    def get_initial_amount_in_cny(self) -> Decimal:
        """获取以人民币计价的初始投入金额"""
        return self.initial_amount * self.exchange_rate
    
    def get_current_value_in_cny(self) -> Decimal:
        """获取以人民币计价的当前价值"""
        return self.current_value * self.exchange_rate
    
    def calculate_total_return_in_cny(self) -> Decimal:
        """计算以人民币计价的总收益"""
        return self.get_current_value_in_cny() - self.get_initial_amount_in_cny()
    
    def calculate_holding_days(self, end_date: Optional[date] = None) -> int:
        """计算持有天数"""
        if end_date is None:
            end_date = date.today()
        return (end_date - self.start_date).days
    
    def calculate_holding_years(self, end_date: Optional[date] = None) -> float:
        """计算持有年数"""
        days = self.calculate_holding_days(end_date)
        return days / 365.25
    
    def calculate_total_return(self) -> Decimal:
        """计算总收益（原币种）"""
        return self.current_value - self.initial_amount
    
    def calculate_total_return_rate(self) -> float:
        """计算总收益率"""
        if self.initial_amount == 0:
            return 0.0
        return float((self.current_value - self.initial_amount) / self.initial_amount)
    
    def calculate_annualized_return(self, end_date: Optional[date] = None) -> float:
        """计算年化回报率"""
        if self.is_fixed_income() and self.annual_rate is not None:
            # 固定收益类产品使用专门的计算方法
            return self._calculate_fixed_income_annualized_return(end_date)
        
        if self.initial_amount == 0:
            return 0.0
        
        years = self.calculate_holding_years(end_date)
        if years <= 0:
            return 0.0
        
        # 年化回报率 = (当前价值/初始投入)^(1/持有年数) - 1
        # 转换为float进行计算
        current_val = float(self.current_value)
        initial_val = float(self.initial_amount)
        return (current_val / initial_val) ** (1 / years) - 1
    
    def _calculate_fixed_income_annualized_return(self, end_date: Optional[date] = None) -> float:
        """计算固定收益类产品的年化回报率"""
        if not self.annual_rate:
            return self.calculate_annualized_return(end_date)
        
        # 使用固定收益类产品的计算逻辑
        try:
            from models.fixed_income import FixedIncomeProduct, FixedIncomeType, InterestType, PaymentFrequency, Currency
            
            # 根据二级分类确定产品类型
            product_type_map = {
                "定期存款": FixedIncomeType.TERM_DEPOSIT,
                "国债": FixedIncomeType.GOVERNMENT_BOND,
                "企业债": FixedIncomeType.CORPORATE_BOND,
                "债券基金": FixedIncomeType.BOND_FUND
            }
            
            # 根据币种字符串确定Currency枚举
            currency_map = {
                "人民币": Currency.CNY,
                "港元": Currency.HKD,
                "美元": Currency.USD,
                "澳元": Currency.AUD
            }
            
            product_type = product_type_map.get(self.secondary_category, FixedIncomeType.TERM_DEPOSIT)
            currency = currency_map.get(self.currency, Currency.CNY)
            
            # 创建固定收益产品对象
            fixed_income = FixedIncomeProduct(
                product_type=product_type,
                principal=self.initial_amount,
                annual_rate=self.annual_rate,
                start_date=self.start_date,
                maturity_date=self.maturity_date or date.today(),
                currency=currency,
                exchange_rate=self.exchange_rate,
                interest_type=InterestType(self.interest_type) if self.interest_type else InterestType.COMPOUND,
                payment_frequency=PaymentFrequency(self.payment_frequency) if self.payment_frequency else PaymentFrequency.MATURITY,
                current_value=self.current_value,
                credit_rating=self.credit_rating,
                issuer=self.issuer,
                coupon_rate=self.coupon_rate,
                face_value=self.face_value
            )
            
            return float(fixed_income.calculate_annualized_yield()) / 100
            
        except ImportError:
            # 如果无法导入固定收益模块，使用默认计算方法
            return self.calculate_annualized_return(end_date)
    
    def calculate_maturity_value(self) -> Optional[Decimal]:
        """计算到期价值（仅适用于固定收益类产品，原币种）"""
        if not self.is_fixed_income() or not self.annual_rate or not self.maturity_date:
            return None
        
        try:
            from models.fixed_income import FixedIncomeProduct, FixedIncomeType, InterestType, PaymentFrequency, Currency
            
            # 根据二级分类确定产品类型
            product_type_map = {
                "定期存款": FixedIncomeType.TERM_DEPOSIT,
                "国债": FixedIncomeType.GOVERNMENT_BOND,
                "企业债": FixedIncomeType.CORPORATE_BOND,
                "债券基金": FixedIncomeType.BOND_FUND
            }
            
            # 根据币种字符串确定Currency枚举
            currency_map = {
                "人民币": Currency.CNY,
                "港元": Currency.HKD,
                "美元": Currency.USD,
                "澳元": Currency.AUD
            }
            
            product_type = product_type_map.get(self.secondary_category, FixedIncomeType.TERM_DEPOSIT)
            currency = currency_map.get(self.currency, Currency.CNY)
            
            # 创建固定收益产品对象
            fixed_income = FixedIncomeProduct(
                product_type=product_type,
                principal=self.initial_amount,
                annual_rate=self.annual_rate,
                start_date=self.start_date,
                maturity_date=self.maturity_date,
                currency=currency,
                exchange_rate=self.exchange_rate,
                interest_type=InterestType(self.interest_type) if self.interest_type else InterestType.COMPOUND,
                payment_frequency=PaymentFrequency(self.payment_frequency) if self.payment_frequency else PaymentFrequency.MATURITY,
                current_value=self.current_value,
                credit_rating=self.credit_rating,
                issuer=self.issuer,
                coupon_rate=self.coupon_rate,
                face_value=self.face_value
            )
            
            return fixed_income.calculate_maturity_value()
            
        except ImportError:
            # 如果无法导入固定收益模块，使用简单复利计算
            if self.maturity_date:
                years = (self.maturity_date - self.start_date).days / 365.25
                rate = float(self.annual_rate) / 100
                return self.initial_amount * Decimal(str((1 + rate) ** years))
            return None
    
    def calculate_maturity_value_in_cny(self) -> Optional[Decimal]:
        """计算以人民币计价的到期价值"""
        maturity_value = self.calculate_maturity_value()
        if maturity_value:
            return maturity_value * self.exchange_rate
        return None
    
    def get_days_to_maturity(self) -> Optional[int]:
        """获取距离到期的天数（仅适用于固定收益类产品）"""
        if not self.is_fixed_income() or not self.maturity_date:
            return None
        
        today = date.today()
        if today <= self.maturity_date:
            return (self.maturity_date - today).days
        return 0
    
    def is_matured(self) -> bool:
        """判断是否已到期（仅适用于固定收益类产品）"""
        if not self.is_fixed_income() or not self.maturity_date:
            return False
        return date.today() >= self.maturity_date
    
    def add_transaction(self, transaction: AssetTransaction) -> None:
        """添加交易记录"""
        self.transactions.append(transaction)
        self.updated_date = datetime.now()
        
        # 根据交易类型更新资产价值
        if transaction.transaction_type in ["买入", "追加投资"]:
            self.initial_amount += transaction.amount
        elif transaction.transaction_type in ["分红", "利息"]:
            self.current_value += transaction.amount
    
    def update_current_value(self, new_value: Decimal, update_date: Optional[date] = None) -> None:
        """更新当前价值"""
        self.current_value = new_value
        self.last_update_date = update_date or date.today()
        self.updated_date = datetime.now()
    
    def update_exchange_rate(self, new_rate: Decimal) -> None:
        """更新汇率"""
        self.exchange_rate = new_rate
        self.updated_date = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """添加标签"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_date = datetime.now()
    
    def remove_tag(self, tag: str) -> None:
        """移除标签"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_date = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "asset_id": self.asset_id,
            "asset_name": self.asset_name,
            "primary_category": self.primary_category,
            "secondary_category": self.secondary_category,
            "initial_amount": str(self.initial_amount),
            "current_value": str(self.current_value),
            "start_date": self.start_date.isoformat(),
            "last_update_date": self.last_update_date.isoformat(),
            "currency": self.currency,
            "exchange_rate": str(self.exchange_rate),
            "description": self.description,
            "tags": self.tags,
            # 固定收益类产品特殊属性
            "annual_rate": str(self.annual_rate) if self.annual_rate else None,
            "maturity_date": self.maturity_date.isoformat() if self.maturity_date else None,
            "interest_type": self.interest_type,
            "payment_frequency": self.payment_frequency,
            "credit_rating": self.credit_rating,
            "issuer": self.issuer,
            "coupon_rate": str(self.coupon_rate) if self.coupon_rate else None,
            "face_value": str(self.face_value) if self.face_value else None,
            # 交易记录和元数据
            "transactions": [t.to_dict() for t in self.transactions],
            "created_date": self.created_date.isoformat(),
            "updated_date": self.updated_date.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Asset":
        """从字典创建资产对象"""
        transactions = [
            AssetTransaction.from_dict(t) for t in data.get("transactions", [])
        ]
        
        return cls(
            asset_id=data["asset_id"],
            asset_name=data["asset_name"],
            primary_category=data["primary_category"],
            secondary_category=data["secondary_category"],
            initial_amount=Decimal(data["initial_amount"]),
            current_value=Decimal(data["current_value"]),
            start_date=date.fromisoformat(data["start_date"]),
            last_update_date=date.fromisoformat(data["last_update_date"]),
            currency=data.get("currency", "人民币"),
            exchange_rate=Decimal(data.get("exchange_rate", "1.0")),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            # 固定收益类产品特殊属性
            annual_rate=Decimal(data["annual_rate"]) if data.get("annual_rate") else None,
            maturity_date=date.fromisoformat(data["maturity_date"]) if data.get("maturity_date") else None,
            interest_type=data.get("interest_type"),
            payment_frequency=data.get("payment_frequency"),
            credit_rating=data.get("credit_rating"),
            issuer=data.get("issuer"),
            coupon_rate=Decimal(data["coupon_rate"]) if data.get("coupon_rate") else None,
            face_value=Decimal(data["face_value"]) if data.get("face_value") else None,
            # 交易记录和元数据
            transactions=transactions,
            created_date=datetime.fromisoformat(data["created_date"]),
            updated_date=datetime.fromisoformat(data["updated_date"])
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """获取资产摘要信息"""
        summary = {
            "asset_name": self.asset_name,
            "category": f"{self.primary_category} - {self.secondary_category}",
            "currency": self.currency,
            "exchange_rate": float(self.exchange_rate),
            "initial_amount": float(self.initial_amount),
            "current_value": float(self.current_value),
            "initial_amount_cny": float(self.get_initial_amount_in_cny()),
            "current_value_cny": float(self.get_current_value_in_cny()),
            "total_return": float(self.calculate_total_return()),
            "total_return_cny": float(self.calculate_total_return_in_cny()),
            "total_return_rate": self.calculate_total_return_rate(),
            "annualized_return": self.calculate_annualized_return(),
            "holding_days": self.calculate_holding_days(),
            "holding_years": round(self.calculate_holding_years(), 2)
        }
        
        # 为固定收益类产品添加特殊信息
        if self.is_fixed_income():
            maturity_value = self.calculate_maturity_value()
            maturity_value_cny = self.calculate_maturity_value_in_cny()
            
            summary.update({
                "annual_rate": float(self.annual_rate) if self.annual_rate else None,
                "maturity_date": self.maturity_date.isoformat() if self.maturity_date else None,
                "days_to_maturity": self.get_days_to_maturity(),
                "is_matured": self.is_matured(),
                "maturity_value": float(maturity_value) if maturity_value else None,
                "maturity_value_cny": float(maturity_value_cny) if maturity_value_cny else None,
                "interest_type": self.interest_type,
                "payment_frequency": self.payment_frequency,
                "credit_rating": self.credit_rating,
                "issuer": self.issuer
            })
        
        return summary 