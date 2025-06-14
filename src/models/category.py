"""
资产分类数据模型

定义资产的分类体系，包括一级类别、二级类别及其属性。
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class RiskLevel(Enum):
    """风险水平枚举"""
    LOW = "低"
    MEDIUM_LOW = "中低"
    MEDIUM_HIGH = "中高"
    HIGH = "高"


class ReturnLevel(Enum):
    """预期收益枚举"""
    LOW = "低"
    MEDIUM_LOW = "中低"
    MEDIUM_HIGH = "中高"
    HIGH = "高"


class LiquidityLevel(Enum):
    """流动性枚举"""
    VERY_HIGH = "极高"
    HIGH = "高"
    MEDIUM_HIGH = "中高"
    MEDIUM = "中"
    LOW = "低"


@dataclass
class Category:
    """资产分类模型"""
    
    # 基本信息
    primary_category: str  # 一级类别
    secondary_category: str  # 二级类别
    
    # 属性
    risk_level: RiskLevel  # 风险水平
    return_level: ReturnLevel  # 预期收益
    liquidity_level: LiquidityLevel  # 流动性
    use_case: str  # 适用场景
    
    # 可选属性
    description: Optional[str] = None  # 描述
    is_custom: bool = False  # 是否为自定义分类
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "primary_category": self.primary_category,
            "secondary_category": self.secondary_category,
            "risk_level": self.risk_level.value,
            "return_level": self.return_level.value,
            "liquidity_level": self.liquidity_level.value,
            "use_case": self.use_case,
            "description": self.description,
            "is_custom": self.is_custom
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Category":
        """从字典创建分类对象"""
        return cls(
            primary_category=data["primary_category"],
            secondary_category=data["secondary_category"],
            risk_level=RiskLevel(data["risk_level"]),
            return_level=ReturnLevel(data["return_level"]),
            liquidity_level=LiquidityLevel(data["liquidity_level"]),
            use_case=data["use_case"],
            description=data.get("description"),
            is_custom=data.get("is_custom", False)
        )


class CategoryManager:
    """分类管理器"""
    
    def __init__(self):
        self._categories: List[Category] = []
        self._load_predefined_categories()
    
    def _load_predefined_categories(self):
        """加载预定义分类"""
        predefined = [
            # 现金及等价物
            Category("现金及等价物", "活期存款", RiskLevel.LOW, ReturnLevel.LOW, 
                    LiquidityLevel.VERY_HIGH, "应急储备、短期资金存放"),
            Category("现金及等价物", "货币基金", RiskLevel.LOW, ReturnLevel.LOW, 
                    LiquidityLevel.VERY_HIGH, "应急储备、短期资金存放"),
            Category("现金及等价物", "短期理财", RiskLevel.LOW, ReturnLevel.LOW, 
                    LiquidityLevel.VERY_HIGH, "应急储备、短期资金存放"),
            
            # 固定收益类 - 暂时移除，使用独立的固定收益类产品管理
            # Category("固定收益类", "定期存款", RiskLevel.MEDIUM_LOW, ReturnLevel.MEDIUM_LOW, 
            #         LiquidityLevel.MEDIUM_HIGH, "稳健保值、低波动需求"),
            # Category("固定收益类", "国债", RiskLevel.MEDIUM_LOW, ReturnLevel.MEDIUM_LOW, 
            #         LiquidityLevel.MEDIUM_HIGH, "稳健保值、低波动需求"),
            # Category("固定收益类", "企业债", RiskLevel.MEDIUM_LOW, ReturnLevel.MEDIUM_LOW, 
            #         LiquidityLevel.MEDIUM_HIGH, "稳健保值、低波动需求"),
            # Category("固定收益类", "债券基金", RiskLevel.MEDIUM_LOW, ReturnLevel.MEDIUM_LOW, 
            #         LiquidityLevel.MEDIUM_HIGH, "稳健保值、低波动需求"),
            
            # 权益类
            Category("权益类", "股票", RiskLevel.HIGH, ReturnLevel.HIGH, 
                    LiquidityLevel.HIGH, "长期增值、承担较高风险"),
            Category("权益类", "股票型基金", RiskLevel.HIGH, ReturnLevel.HIGH, 
                    LiquidityLevel.HIGH, "长期增值、承担较高风险"),
            Category("权益类", "ETF", RiskLevel.HIGH, ReturnLevel.HIGH, 
                    LiquidityLevel.HIGH, "长期增值、承担较高风险"),
            
            # 不动产
            Category("不动产", "住宅", RiskLevel.MEDIUM_HIGH, ReturnLevel.MEDIUM_HIGH, 
                    LiquidityLevel.LOW, "抗通胀、长期资产配置"),
            Category("不动产", "商铺", RiskLevel.MEDIUM_HIGH, ReturnLevel.MEDIUM_HIGH, 
                    LiquidityLevel.LOW, "抗通胀、长期资产配置"),
            Category("不动产", "REITs", RiskLevel.MEDIUM_HIGH, ReturnLevel.MEDIUM_HIGH, 
                    LiquidityLevel.LOW, "抗通胀、长期资产配置"),
            
            # 大宗商品
            Category("大宗商品", "贵金属", RiskLevel.HIGH, ReturnLevel.HIGH, 
                    LiquidityLevel.MEDIUM, "对冲通胀、分散风险"),
        ]
        
        self._categories.extend(predefined)
    
    def get_all_categories(self) -> List[Category]:
        """获取所有分类"""
        return self._categories.copy()
    
    def get_primary_categories(self) -> List[str]:
        """获取所有一级分类"""
        return list(set(cat.primary_category for cat in self._categories))
    
    def get_secondary_categories(self, primary: str) -> List[str]:
        """获取指定一级分类下的二级分类"""
        return [cat.secondary_category for cat in self._categories 
                if cat.primary_category == primary]
    
    def get_category(self, primary: str, secondary: str) -> Optional[Category]:
        """获取指定分类"""
        for cat in self._categories:
            if cat.primary_category == primary and cat.secondary_category == secondary:
                return cat
        return None
    
    def add_custom_category(self, category: Category) -> bool:
        """添加自定义分类"""
        # 检查是否已存在
        if self.get_category(category.primary_category, category.secondary_category):
            return False
        
        category.is_custom = True
        self._categories.append(category)
        return True
    
    def remove_custom_category(self, primary: str, secondary: str) -> bool:
        """删除自定义分类（不能删除预定义分类）"""
        category = self.get_category(primary, secondary)
        if category and category.is_custom:
            self._categories.remove(category)
            return True
        return False 