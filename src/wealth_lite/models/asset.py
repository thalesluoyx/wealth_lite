"""
WealthLite 资产模型

Asset类负责管理资产的静态属性，不包含交易记录和计算逻辑。
遵循单一职责原则，专注于资产基础信息的管理。
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from .enums import AssetType, Currency, RiskLevel, LiquidityLevel


@dataclass
class Asset:
    """
    资产基础信息类
    
    职责：
    - 管理资产的静态属性（名称、类型、分类等）
    - 提供资产基础信息的访问接口
    - 不包含交易记录和计算逻辑
    """
    
    # 基础信息
    asset_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    asset_name: str = ""
    asset_type: AssetType = AssetType.CASH
    
    # 分类信息
    primary_category: str = ""
    secondary_category: str = ""
    
    # 货币和地区
    currency: Currency = Currency.CNY
    country: str = "中国"
    exchange: str = ""  # 交易所（股票、基金等）
    
    # 资产详细信息
    description: str = ""
    issuer: str = ""  # 发行方
    credit_rating: str = ""  # 信用评级
    isin_code: str = ""  # 国际证券识别码
    symbol: str = ""  # 交易代码
    
    # 风险和流动性
    risk_level: RiskLevel = RiskLevel.MEDIUM
    liquidity_level: LiquidityLevel = LiquidityLevel.MEDIUM
    
    # 时间戳
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    
    # 扩展属性（JSON格式存储）
    extended_attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if not self.asset_name:
            raise ValueError("资产名称不能为空")
        
        # 设置默认分类
        if not self.primary_category:
            self.primary_category = self.asset_type.display_name
            
        # 更新时间戳
        self.updated_date = datetime.now()

    @property
    def display_name(self) -> str:
        """返回显示名称"""
        if self.symbol:
            return f"{self.asset_name} ({self.symbol})"
        return self.asset_name

    @property
    def full_category(self) -> str:
        """返回完整分类路径"""
        if self.secondary_category:
            return f"{self.primary_category} > {self.secondary_category}"
        return self.primary_category

    @property
    def currency_symbol(self) -> str:
        """返回货币符号"""
        return self.currency.symbol

    @property
    def risk_score(self) -> int:
        """返回风险评分（1-5）"""
        return self.risk_level.risk_score

    @property
    def liquidity_score(self) -> int:
        """返回流动性评分（1-5）"""
        return self.liquidity_level.liquidity_score

    def update_info(self, **kwargs) -> None:
        """更新资产信息"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_date = datetime.now()

    def set_extended_attribute(self, key: str, value: Any) -> None:
        """设置扩展属性"""
        self.extended_attributes[key] = value
        self.updated_date = datetime.now()

    def get_extended_attribute(self, key: str, default: Any = None) -> Any:
        """获取扩展属性"""
        return self.extended_attributes.get(key, default)

    def remove_extended_attribute(self, key: str) -> None:
        """删除扩展属性"""
        if key in self.extended_attributes:
            del self.extended_attributes[key]
            self.updated_date = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'asset_id': self.asset_id,
            'asset_name': self.asset_name,
            'asset_type': self.asset_type.name,
            'primary_category': self.primary_category,
            'secondary_category': self.secondary_category,
            'currency': self.currency.name,
            'country': self.country,
            'exchange': self.exchange,
            'description': self.description,
            'issuer': self.issuer,
            'credit_rating': self.credit_rating,
            'isin_code': self.isin_code,
            'symbol': self.symbol,
            'risk_level': self.risk_level.name,
            'liquidity_level': self.liquidity_level.name,
            'created_date': self.created_date.isoformat(),
            'updated_date': self.updated_date.isoformat(),
            'extended_attributes': self.extended_attributes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Asset':
        """从字典创建Asset实例"""
        # 处理枚举类型
        asset_type = AssetType[data.get('asset_type', 'CASH')]
        currency = Currency[data.get('currency', 'CNY')]
        risk_level = RiskLevel[data.get('risk_level', 'MEDIUM')]
        liquidity_level = LiquidityLevel[data.get('liquidity_level', 'MEDIUM')]
        
        # 处理时间戳
        created_date = datetime.fromisoformat(data.get('created_date', datetime.now().isoformat()))
        updated_date = datetime.fromisoformat(data.get('updated_date', datetime.now().isoformat()))
        
        return cls(
            asset_id=data.get('asset_id', str(uuid.uuid4())),
            asset_name=data.get('asset_name', ''),
            asset_type=asset_type,
            primary_category=data.get('primary_category', ''),
            secondary_category=data.get('secondary_category', ''),
            currency=currency,
            country=data.get('country', '中国'),
            exchange=data.get('exchange', ''),
            description=data.get('description', ''),
            issuer=data.get('issuer', ''),
            credit_rating=data.get('credit_rating', ''),
            isin_code=data.get('isin_code', ''),
            symbol=data.get('symbol', ''),
            risk_level=risk_level,
            liquidity_level=liquidity_level,
            created_date=created_date,
            updated_date=updated_date,
            extended_attributes=data.get('extended_attributes', {})
        )

    def __str__(self) -> str:
        """字符串表示"""
        return f"Asset({self.display_name}, {self.asset_type.display_name})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"Asset(id={self.asset_id[:8]}..., name='{self.asset_name}', "
                f"type={self.asset_type.name}, currency={self.currency.name})")

    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, Asset):
            return False
        return self.asset_id == other.asset_id

    def __hash__(self) -> int:
        """哈希值"""
        return hash(self.asset_id) 