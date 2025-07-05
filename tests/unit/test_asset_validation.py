"""
测试资产名称验证功能
"""

import pytest
import os
import sys
from pathlib import Path
from decimal import Decimal

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wealth_lite.services.wealth_service import WealthService
from wealth_lite.models.enums import AssetType, Currency


class TestAssetNameValidation:
    """测试资产名称验证"""
    
    @pytest.fixture
    def wealth_service(self):
        """创建测试用的WealthService实例"""
        # 设置测试环境，确保使用内存数据库
        os.environ['WEALTH_LITE_ENV'] = 'test'
        service = WealthService()
        yield service
        service.close()
        # 清理环境变量
        if 'WEALTH_LITE_ENV' in os.environ:
            del os.environ['WEALTH_LITE_ENV']
    
    def test_create_asset_with_valid_name(self, wealth_service):
        """测试创建具有有效名称的资产"""
        asset = wealth_service.create_asset(
            asset_name="测试资产",
            asset_type=AssetType.CASH,
            primary_category="现金及等价物",
            secondary_category="储蓄存款",
            currency=Currency.CNY
        )
        
        assert asset.asset_name == "测试资产"
        assert asset.asset_type == AssetType.CASH
    
    def test_create_asset_with_empty_name(self, wealth_service):
        """测试创建空名称资产应该失败"""
        with pytest.raises(ValueError, match="资产名称不能为空"):
            wealth_service.create_asset(
                asset_name="",
                asset_type=AssetType.CASH,
                primary_category="现金及等价物",
                secondary_category="储蓄存款",
                currency=Currency.CNY
            )
    
    def test_create_asset_with_whitespace_name(self, wealth_service):
        """测试创建只有空格的名称资产应该失败"""
        with pytest.raises(ValueError, match="资产名称不能为空"):
            wealth_service.create_asset(
                asset_name="   ",
                asset_type=AssetType.CASH,
                primary_category="现金及等价物",
                secondary_category="储蓄存款",
                currency=Currency.CNY
            )
    
    def test_create_asset_with_duplicate_name(self, wealth_service):
        """测试创建重复名称的资产应该失败"""
        # 先创建一个资产
        wealth_service.create_asset(
            asset_name="测试资产",
            asset_type=AssetType.CASH,
            primary_category="现金及等价物",
            secondary_category="储蓄存款",
            currency=Currency.CNY
        )
        
        # 再次创建同名资产应该失败
        with pytest.raises(ValueError, match="资产名称已存在: 测试资产"):
            wealth_service.create_asset(
                asset_name="测试资产",
                asset_type=AssetType.FIXED_INCOME,
                primary_category="固定收益类",
                secondary_category="政府债券",
                currency=Currency.CNY
            )
    
    def test_create_asset_with_trimmed_duplicate_name(self, wealth_service):
        """测试创建带空格的重复名称资产应该失败"""
        # 先创建一个资产
        wealth_service.create_asset(
            asset_name="测试资产",
            asset_type=AssetType.CASH,
            primary_category="现金及等价物",
            secondary_category="储蓄存款",
            currency=Currency.CNY
        )
        
        # 创建带空格的同名资产应该失败
        with pytest.raises(ValueError, match="资产名称已存在:   测试资产  "):
            wealth_service.create_asset(
                asset_name="  测试资产  ",
                asset_type=AssetType.FIXED_INCOME,
                primary_category="固定收益类",
                secondary_category="政府债券",
                currency=Currency.CNY
            )
    
    def test_create_asset_name_trimmed_correctly(self, wealth_service):
        """测试资产名称正确去除空格"""
        asset = wealth_service.create_asset(
            asset_name="  测试资产  ",
            asset_type=AssetType.CASH,
            primary_category="现金及等价物",
            secondary_category="储蓄存款",
            currency=Currency.CNY
        )
        
        assert asset.asset_name == "测试资产"
    
    def test_create_multiple_assets_with_different_names(self, wealth_service):
        """测试创建多个不同名称的资产"""
        asset1 = wealth_service.create_asset(
            asset_name="测试资产1",
            asset_type=AssetType.CASH,
            primary_category="现金及等价物",
            secondary_category="储蓄存款",
            currency=Currency.CNY
        )
        
        asset2 = wealth_service.create_asset(
            asset_name="测试资产2",
            asset_type=AssetType.FIXED_INCOME,
            primary_category="固定收益类",
            secondary_category="政府债券",
            currency=Currency.CNY
        )
        
        assert asset1.asset_name == "测试资产1"
        assert asset2.asset_name == "测试资产2"
        assert asset1.asset_id != asset2.asset_id