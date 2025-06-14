"""
资产模型单元测试
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.asset import Asset, AssetTransaction
from datetime import date, datetime
from decimal import Decimal


class TestAssetTransaction:
    """资产交易记录测试类"""
    
    def test_transaction_creation(self):
        """测试交易记录创建"""
        transaction = AssetTransaction(
            transaction_type="买入",
            amount=Decimal("10000"),
            quantity=Decimal("100"),
            price=Decimal("100"),
            description="首次买入"
        )
        
        assert transaction.transaction_type == "买入"
        assert transaction.amount == Decimal("10000")
        assert transaction.quantity == Decimal("100")
        assert transaction.price == Decimal("100")
        assert transaction.description == "首次买入"
        assert transaction.transaction_date == date.today()
    
    def test_transaction_to_dict(self):
        """测试交易记录转换为字典"""
        transaction = AssetTransaction(
            transaction_type="分红",
            amount=Decimal("200"),
            description="年度分红"
        )
        
        transaction_dict = transaction.to_dict()
        
        assert transaction_dict["transaction_type"] == "分红"
        assert transaction_dict["amount"] == "200"
        assert transaction_dict["description"] == "年度分红"
        assert "transaction_id" in transaction_dict
        assert "transaction_date" in transaction_dict
    
    def test_transaction_from_dict(self):
        """测试从字典创建交易记录"""
        transaction_data = {
            "transaction_id": "test-id",
            "transaction_date": "2024-01-01",
            "transaction_type": "买入",
            "amount": "10000",
            "quantity": "100",
            "price": "100",
            "description": "测试买入"
        }
        
        transaction = AssetTransaction.from_dict(transaction_data)
        
        assert transaction.transaction_id == "test-id"
        assert transaction.transaction_date == date(2024, 1, 1)
        assert transaction.transaction_type == "买入"
        assert transaction.amount == Decimal("10000")
        assert transaction.quantity == Decimal("100")
        assert transaction.price == Decimal("100")
        assert transaction.description == "测试买入"


class TestAsset:
    """资产模型测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.asset = Asset(
            asset_name="测试股票",
            primary_category="权益类",
            secondary_category="股票",
            initial_amount=Decimal("10000"),
            current_value=Decimal("12000"),
            start_date=date(2024, 1, 1)
        )
    
    def test_asset_creation(self):
        """测试资产创建"""
        assert self.asset.asset_name == "测试股票"
        assert self.asset.primary_category == "权益类"
        assert self.asset.secondary_category == "股票"
        assert self.asset.initial_amount == Decimal("10000")
        assert self.asset.current_value == Decimal("12000")
        assert self.asset.start_date == date(2024, 1, 1)
    
    def test_calculate_holding_days(self):
        """测试持有天数计算"""
        # 测试到今天的持有天数
        days_to_today = self.asset.calculate_holding_days()
        expected_days = (date.today() - date(2024, 1, 1)).days
        assert days_to_today == expected_days
        
        # 测试到指定日期的持有天数
        end_date = date(2024, 6, 1)
        days_to_end = self.asset.calculate_holding_days(end_date)
        expected_days_to_end = (end_date - date(2024, 1, 1)).days
        assert days_to_end == expected_days_to_end
    
    def test_calculate_holding_years(self):
        """测试持有年数计算"""
        years = self.asset.calculate_holding_years(date(2025, 1, 1))
        assert abs(years - 1.0) < 0.01  # 大约1年
    
    def test_calculate_total_return(self):
        """测试总收益计算"""
        total_return = self.asset.calculate_total_return()
        assert total_return == Decimal("2000")  # 12000 - 10000
    
    def test_calculate_total_return_rate(self):
        """测试总收益率计算"""
        return_rate = self.asset.calculate_total_return_rate()
        assert abs(return_rate - 0.2) < 0.001  # 20%
    
    def test_calculate_annualized_return(self):
        """测试年化回报率计算"""
        # 测试1年期的年化回报率
        annualized_return = self.asset.calculate_annualized_return(date(2025, 1, 1))
        assert abs(annualized_return - 0.2) < 0.01  # 约20%
        
        # 测试初始投入为0的情况
        zero_asset = Asset(initial_amount=Decimal("0"))
        assert zero_asset.calculate_annualized_return() == 0.0
    
    def test_add_transaction(self):
        """测试添加交易记录"""
        initial_transactions = len(self.asset.transactions)
        
        transaction = AssetTransaction(
            transaction_type="分红",
            amount=Decimal("200"),
            description="季度分红"
        )
        
        self.asset.add_transaction(transaction)
        
        # 验证交易记录已添加
        assert len(self.asset.transactions) == initial_transactions + 1
        assert self.asset.transactions[-1] == transaction
        
        # 验证分红已加到当前价值
        assert self.asset.current_value == Decimal("12200")
    
    def test_add_investment_transaction(self):
        """测试添加投资交易记录"""
        initial_amount = self.asset.initial_amount
        
        transaction = AssetTransaction(
            transaction_type="买入",
            amount=Decimal("5000"),
            description="追加投资"
        )
        
        self.asset.add_transaction(transaction)
        
        # 验证初始投入已增加
        assert self.asset.initial_amount == initial_amount + Decimal("5000")
    
    def test_update_current_value(self):
        """测试更新当前价值"""
        new_value = Decimal("15000")
        update_date = date(2024, 6, 1)
        
        self.asset.update_current_value(new_value, update_date)
        
        assert self.asset.current_value == new_value
        assert self.asset.last_update_date == update_date
    
    def test_tag_management(self):
        """测试标签管理"""
        # 添加标签
        self.asset.add_tag("蓝筹股")
        assert "蓝筹股" in self.asset.tags
        
        # 添加重复标签（不应重复添加）
        self.asset.add_tag("蓝筹股")
        assert self.asset.tags.count("蓝筹股") == 1
        
        # 移除标签
        self.asset.remove_tag("蓝筹股")
        assert "蓝筹股" not in self.asset.tags
    
    def test_to_dict(self):
        """测试转换为字典"""
        asset_dict = self.asset.to_dict()
        
        assert asset_dict["asset_name"] == "测试股票"
        assert asset_dict["primary_category"] == "权益类"
        assert asset_dict["secondary_category"] == "股票"
        assert asset_dict["initial_amount"] == "10000"
        assert asset_dict["current_value"] == "12000"
        assert asset_dict["start_date"] == "2024-01-01"
        assert "asset_id" in asset_dict
        assert "transactions" in asset_dict
    
    def test_from_dict(self):
        """测试从字典创建资产"""
        asset_data = {
            "asset_id": "test-id",
            "asset_name": "测试资产",
            "primary_category": "权益类",
            "secondary_category": "股票",
            "initial_amount": "10000",
            "current_value": "12000",
            "start_date": "2024-01-01",
            "last_update_date": "2024-06-01",
            "description": "测试描述",
            "tags": ["测试标签"],
            "transactions": [],
            "created_date": "2024-01-01T00:00:00",
            "updated_date": "2024-06-01T00:00:00"
        }
        
        asset = Asset.from_dict(asset_data)
        
        assert asset.asset_id == "test-id"
        assert asset.asset_name == "测试资产"
        assert asset.primary_category == "权益类"
        assert asset.secondary_category == "股票"
        assert asset.initial_amount == Decimal("10000")
        assert asset.current_value == Decimal("12000")
        assert asset.start_date == date(2024, 1, 1)
        assert asset.description == "测试描述"
        assert asset.tags == ["测试标签"]
    
    def test_get_summary(self):
        """测试获取资产摘要"""
        summary = self.asset.get_summary()
        
        assert summary["asset_name"] == "测试股票"
        assert summary["category"] == "权益类 - 股票"
        assert summary["initial_amount"] == 10000.0
        assert summary["current_value"] == 12000.0
        assert summary["total_return"] == 2000.0
        assert abs(summary["total_return_rate"] - 0.2) < 0.001
        assert "annualized_return" in summary
        assert "holding_days" in summary
        assert "holding_years" in summary 