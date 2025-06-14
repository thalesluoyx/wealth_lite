"""
分类管理器单元测试
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.category import CategoryManager, Category, RiskLevel, ReturnLevel, LiquidityLevel


class TestCategoryManager:
    """分类管理器测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.category_manager = CategoryManager()
    
    def test_predefined_categories_loaded(self):
        """测试预定义分类是否正确加载"""
        categories = self.category_manager.get_all_categories()
        assert len(categories) == 14
        
        # 验证包含所有5个一级分类
        primary_categories = self.category_manager.get_primary_categories()
        expected_primary = ["现金及等价物", "固定收益类", "权益类", "不动产", "大宗商品"]
        for category in expected_primary:
            assert category in primary_categories
    
    def test_get_secondary_categories(self):
        """测试获取二级分类"""
        # 测试权益类的二级分类
        equity_secondary = self.category_manager.get_secondary_categories("权益类")
        expected_equity = ["股票", "股票型基金", "ETF"]
        assert set(equity_secondary) == set(expected_equity)
        
        # 测试不存在的一级分类
        non_exist_secondary = self.category_manager.get_secondary_categories("不存在的分类")
        assert non_exist_secondary == []
    
    def test_get_category(self):
        """测试获取指定分类"""
        # 测试获取存在的分类
        category = self.category_manager.get_category("权益类", "股票")
        assert category is not None
        assert category.primary_category == "权益类"
        assert category.secondary_category == "股票"
        assert category.risk_level == RiskLevel.HIGH
        
        # 测试获取不存在的分类
        non_exist_category = self.category_manager.get_category("不存在", "不存在")
        assert non_exist_category is None
    
    def test_add_custom_category(self):
        """测试添加自定义分类"""
        custom_category = Category(
            primary_category="数字货币",
            secondary_category="比特币",
            risk_level=RiskLevel.HIGH,
            return_level=ReturnLevel.HIGH,
            liquidity_level=LiquidityLevel.HIGH,
            use_case="高风险投资"
        )
        
        # 添加自定义分类
        result = self.category_manager.add_custom_category(custom_category)
        assert result is True
        
        # 验证分类已添加
        added_category = self.category_manager.get_category("数字货币", "比特币")
        assert added_category is not None
        assert added_category.is_custom is True
        
        # 尝试添加重复分类
        duplicate_result = self.category_manager.add_custom_category(custom_category)
        assert duplicate_result is False
    
    def test_remove_custom_category(self):
        """测试删除自定义分类"""
        # 先添加一个自定义分类
        custom_category = Category(
            primary_category="测试分类",
            secondary_category="测试子分类",
            risk_level=RiskLevel.LOW,
            return_level=ReturnLevel.LOW,
            liquidity_level=LiquidityLevel.HIGH,
            use_case="测试用途"
        )
        self.category_manager.add_custom_category(custom_category)
        
        # 删除自定义分类
        result = self.category_manager.remove_custom_category("测试分类", "测试子分类")
        assert result is True
        
        # 验证分类已删除
        deleted_category = self.category_manager.get_category("测试分类", "测试子分类")
        assert deleted_category is None
        
        # 尝试删除预定义分类（应该失败）
        predefined_result = self.category_manager.remove_custom_category("权益类", "股票")
        assert predefined_result is False


class TestCategory:
    """分类模型测试类"""
    
    def test_category_to_dict(self):
        """测试分类转换为字典"""
        category = Category(
            primary_category="权益类",
            secondary_category="股票",
            risk_level=RiskLevel.HIGH,
            return_level=ReturnLevel.HIGH,
            liquidity_level=LiquidityLevel.HIGH,
            use_case="长期增值",
            description="股票投资"
        )
        
        category_dict = category.to_dict()
        
        assert category_dict["primary_category"] == "权益类"
        assert category_dict["secondary_category"] == "股票"
        assert category_dict["risk_level"] == "高"
        assert category_dict["return_level"] == "高"
        assert category_dict["liquidity_level"] == "高"
        assert category_dict["use_case"] == "长期增值"
        assert category_dict["description"] == "股票投资"
        assert category_dict["is_custom"] is False
    
    def test_category_from_dict(self):
        """测试从字典创建分类"""
        category_data = {
            "primary_category": "权益类",
            "secondary_category": "股票",
            "risk_level": "高",
            "return_level": "高",
            "liquidity_level": "高",
            "use_case": "长期增值",
            "description": "股票投资",
            "is_custom": True
        }
        
        category = Category.from_dict(category_data)
        
        assert category.primary_category == "权益类"
        assert category.secondary_category == "股票"
        assert category.risk_level == RiskLevel.HIGH
        assert category.return_level == ReturnLevel.HIGH
        assert category.liquidity_level == LiquidityLevel.HIGH
        assert category.use_case == "长期增值"
        assert category.description == "股票投资"
        assert category.is_custom is True 