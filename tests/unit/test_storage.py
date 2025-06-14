"""
数据存储模块单元测试
"""

import pytest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录和src目录到Python路径
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_dir)

from data.csv_storage import CSVStorage
from data.json_storage import JSONStorage
from data.asset_manager import AssetManager
from models.asset import Asset, AssetTransaction
from datetime import date, datetime
from decimal import Decimal


class TestCSVStorage:
    """CSV存储测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.csv_storage = CSVStorage(self.temp_dir)
        
        # 创建测试资产
        self.test_asset = Asset(
            asset_name="测试股票",
            primary_category="权益类",
            secondary_category="股票",
            initial_amount=Decimal("10000"),
            current_value=Decimal("12000"),
            start_date=date(2024, 1, 1),
            description="测试资产"
        )
        
        # 添加交易记录
        transaction = AssetTransaction(
            transaction_type="买入",
            amount=Decimal("10000"),
            description="初始买入"
        )
        self.test_asset.add_transaction(transaction)
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load_assets(self):
        """测试保存和加载资产"""
        # 保存资产
        assets = [self.test_asset]
        save_result = self.csv_storage.save_assets(assets)
        assert save_result is True
        
        # 验证文件存在
        assert self.csv_storage.assets_file.exists()
        assert self.csv_storage.transactions_file.exists()
        
        # 加载资产
        loaded_assets = self.csv_storage.load_assets()
        assert len(loaded_assets) == 1
        
        loaded_asset = loaded_assets[0]
        assert loaded_asset.asset_name == self.test_asset.asset_name
        assert loaded_asset.primary_category == self.test_asset.primary_category
        assert loaded_asset.initial_amount == self.test_asset.initial_amount
        assert loaded_asset.current_value == self.test_asset.current_value
        assert len(loaded_asset.transactions) == 1
    
    def test_load_empty_files(self):
        """测试加载空文件"""
        # 文件不存在时应返回空列表
        assets = self.csv_storage.load_assets()
        assert assets == []
    
    def test_backup_data(self):
        """测试数据备份"""
        # 先保存一些数据
        assets = [self.test_asset]
        self.csv_storage.save_assets(assets)
        
        # 执行备份
        backup_result = self.csv_storage.backup_data()
        assert backup_result is True
        
        # 验证备份文件存在
        backup_dir = Path(self.temp_dir) / "backups"
        assert backup_dir.exists()
        
        backup_files = list(backup_dir.glob("*.csv"))
        assert len(backup_files) >= 2  # assets和transactions备份文件
    
    def test_get_file_info(self):
        """测试获取文件信息"""
        # 保存数据
        assets = [self.test_asset]
        self.csv_storage.save_assets(assets)
        
        # 获取文件信息
        file_info = self.csv_storage.get_file_info()
        
        assert "assets_file" in file_info
        assert "transactions_file" in file_info
        assert file_info["assets_file"]["exists"] is True
        assert file_info["transactions_file"]["exists"] is True
        assert file_info["assets_file"]["size"] > 0
        assert file_info["transactions_file"]["size"] > 0


class TestJSONStorage:
    """JSON存储测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.json_storage = JSONStorage(self.temp_dir)
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_default_config(self):
        """测试加载默认配置"""
        config = self.json_storage.load_config()
        
        assert config["version"] == "0.1.0"
        assert "backup_settings" in config
        assert "display_settings" in config
        assert config["display_settings"]["currency_symbol"] == "¥"
    
    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        # 修改配置
        config = self.json_storage.load_config()
        config["version"] = "0.2.0"
        config["display_settings"]["currency_symbol"] = "$"
        
        # 保存配置
        save_result = self.json_storage.save_config(config)
        assert save_result is True
        
        # 重新加载配置
        loaded_config = self.json_storage.load_config()
        assert loaded_config["version"] == "0.2.0"
        assert loaded_config["display_settings"]["currency_symbol"] == "$"
    
    def test_load_default_settings(self):
        """测试加载默认设置"""
        settings = self.json_storage.load_settings()
        
        assert "user_preferences" in settings
        assert "window_settings" in settings
        assert settings["user_preferences"]["auto_save"] is True
        assert settings["window_settings"]["width"] == 1200
    
    def test_get_and_set_setting(self):
        """测试获取和设置配置值"""
        # 设置值
        result = self.json_storage.set_setting("user_preferences.theme", "dark")
        assert result is True
        
        # 获取值
        theme = self.json_storage.get_setting("user_preferences.theme")
        assert theme == "dark"
        
        # 获取不存在的值
        non_exist = self.json_storage.get_setting("non.exist.key", "default")
        assert non_exist == "default"
    
    def test_merge_config(self):
        """测试配置合并"""
        default_config = {"a": 1, "b": {"c": 2, "d": 3}}
        user_config = {"b": {"c": 4}, "e": 5}
        
        merged = self.json_storage._merge_config(default_config, user_config)
        
        assert merged["a"] == 1  # 保留默认值
        assert merged["b"]["c"] == 4  # 用户值覆盖
        assert merged["b"]["d"] == 3  # 保留默认值
        assert merged["e"] == 5  # 新增用户值
    
    def test_export_and_import_data(self):
        """测试数据导出和导入"""
        test_data = {"test": "data", "number": 123}
        export_file = Path(self.temp_dir) / "test_export.json"
        
        # 导出数据
        export_result = self.json_storage.export_data(str(export_file), test_data)
        assert export_result is True
        assert export_file.exists()
        
        # 导入数据
        imported_data = self.json_storage.import_data(str(export_file))
        assert imported_data == test_data
    
    def test_reset_to_defaults(self):
        """测试重置为默认值"""
        # 修改一些设置
        self.json_storage.set_setting("user_preferences.theme", "custom")
        
        # 重置为默认值
        reset_result = self.json_storage.reset_to_defaults()
        assert reset_result is True
        
        # 创建新的JSONStorage实例来验证重置
        new_storage = JSONStorage(self.temp_dir)
        theme = new_storage.get_setting("user_preferences.theme")
        assert theme == "default"


class TestAssetManager:
    """资产管理器测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.asset_manager = AssetManager(self.temp_dir)
        
        # 创建测试资产
        self.test_asset = Asset(
            asset_name="测试资产",
            primary_category="权益类",
            secondary_category="股票",
            initial_amount=Decimal("10000"),
            current_value=Decimal("12000"),
            start_date=date(2024, 1, 1)
        )
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_and_get_asset(self):
        """测试添加和获取资产"""
        # 添加资产
        add_result = self.asset_manager.add_asset(self.test_asset)
        assert add_result is True
        
        # 根据ID获取资产
        retrieved_asset = self.asset_manager.get_asset_by_id(self.test_asset.asset_id)
        assert retrieved_asset is not None
        assert retrieved_asset.asset_name == self.test_asset.asset_name
        
        # 根据名称获取资产
        retrieved_by_name = self.asset_manager.get_asset_by_name(self.test_asset.asset_name)
        assert retrieved_by_name is not None
        assert retrieved_by_name.asset_id == self.test_asset.asset_id
    
    def test_add_duplicate_asset(self):
        """测试添加重复资产"""
        # 添加第一个资产
        self.asset_manager.add_asset(self.test_asset)
        
        # 尝试添加同名资产
        duplicate_asset = Asset(
            asset_name=self.test_asset.asset_name,  # 同名
            primary_category="现金及等价物",
            secondary_category="活期存款",
            initial_amount=Decimal("5000"),
            current_value=Decimal("5000")
        )
        
        add_result = self.asset_manager.add_asset(duplicate_asset)
        assert add_result is False  # 应该失败
    
    def test_update_asset(self):
        """测试更新资产"""
        # 添加资产
        self.asset_manager.add_asset(self.test_asset)
        
        # 更新资产
        update_result = self.asset_manager.update_asset(
            self.test_asset.asset_id,
            current_value=Decimal("15000"),
            description="更新后的描述"
        )
        assert update_result is True
        
        # 验证更新
        updated_asset = self.asset_manager.get_asset_by_id(self.test_asset.asset_id)
        assert updated_asset.current_value == Decimal("15000")
        assert updated_asset.description == "更新后的描述"
    
    def test_delete_asset(self):
        """测试删除资产"""
        # 添加资产
        self.asset_manager.add_asset(self.test_asset)
        
        # 删除资产
        delete_result = self.asset_manager.delete_asset(self.test_asset.asset_id)
        assert delete_result is True
        
        # 验证已删除
        deleted_asset = self.asset_manager.get_asset_by_id(self.test_asset.asset_id)
        assert deleted_asset is None
    
    def test_get_assets_by_category(self):
        """测试按分类获取资产"""
        # 添加不同分类的资产
        self.asset_manager.add_asset(self.test_asset)
        
        cash_asset = Asset(
            asset_name="现金资产",
            primary_category="现金及等价物",
            secondary_category="活期存款",
            initial_amount=Decimal("5000"),
            current_value=Decimal("5000")
        )
        self.asset_manager.add_asset(cash_asset)
        
        # 按一级分类获取
        equity_assets = self.asset_manager.get_assets_by_category("权益类")
        assert len(equity_assets) == 1
        assert equity_assets[0].asset_name == "测试资产"
        
        # 按二级分类获取
        stock_assets = self.asset_manager.get_assets_by_category("权益类", "股票")
        assert len(stock_assets) == 1
        
        deposit_assets = self.asset_manager.get_assets_by_category("现金及等价物", "活期存款")
        assert len(deposit_assets) == 1
    
    def test_portfolio_summary(self):
        """测试投资组合摘要"""
        # 添加多个资产
        self.asset_manager.add_asset(self.test_asset)
        
        cash_asset = Asset(
            asset_name="现金资产",
            primary_category="现金及等价物",
            secondary_category="活期存款",
            initial_amount=Decimal("5000"),
            current_value=Decimal("5100")
        )
        self.asset_manager.add_asset(cash_asset)
        
        # 获取组合摘要
        summary = self.asset_manager.get_portfolio_summary()
        
        assert summary["total_assets"] == 2
        assert summary["total_initial_amount"] == 15000.0  # 10000 + 5000
        assert summary["total_current_value"] == 17100.0   # 12000 + 5100
        assert summary["total_return"] == 2100.0           # 17100 - 15000
        assert abs(summary["total_return_rate"] - 0.14) < 0.01  # 14%
        
        # 验证分类统计
        assert len(summary["category_breakdown"]) == 2
    
    def test_search_assets(self):
        """测试搜索资产"""
        # 添加资产
        self.test_asset.description = "银行股票投资"
        self.test_asset.add_tag("蓝筹股")
        self.asset_manager.add_asset(self.test_asset)
        
        # 按名称搜索
        results = self.asset_manager.search_assets("测试")
        assert len(results) == 1
        
        # 按描述搜索
        results = self.asset_manager.search_assets("银行")
        assert len(results) == 1
        
        # 按标签搜索
        results = self.asset_manager.search_assets("蓝筹")
        assert len(results) == 1
        
        # 搜索不存在的关键词
        results = self.asset_manager.search_assets("不存在")
        assert len(results) == 0
    
    def test_save_and_load_data(self):
        """测试保存和加载数据"""
        # 添加资产
        self.asset_manager.add_asset(self.test_asset)
        
        # 保存数据
        save_result = self.asset_manager.save_data()
        assert save_result is True
        
        # 创建新的管理器实例（模拟重启）
        new_manager = AssetManager(self.temp_dir)
        
        # 验证数据已加载
        loaded_assets = new_manager.get_all_assets()
        assert len(loaded_assets) == 1
        assert loaded_assets[0].asset_name == self.test_asset.asset_name
    
    def test_get_data_statistics(self):
        """测试获取数据统计"""
        # 添加资产和交易
        transaction = AssetTransaction(
            transaction_type="买入",
            amount=Decimal("10000")
        )
        self.test_asset.add_transaction(transaction)
        self.asset_manager.add_asset(self.test_asset)
        
        # 获取统计信息
        stats = self.asset_manager.get_data_statistics()
        
        assert stats["assets_count"] == 1
        assert stats["transactions_count"] == 1
        assert stats["categories_count"] == 14  # 预定义分类数量
        assert stats["data_loaded"] is True