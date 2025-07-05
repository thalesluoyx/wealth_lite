"""
WealthLite 测试配置

包含pytest的全局配置和共享fixture。
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path
from decimal import Decimal
from datetime import date, datetime
from typing import Generator

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from wealth_lite.models import (
    Asset, AssetType, Currency, RiskLevel, LiquidityLevel,
    CashTransaction, TransactionType
)
from wealth_lite.models.enums import AssetSubType
from wealth_lite.services.wealth_service import WealthService


@pytest.fixture(scope="function")
def wealth_service():
    """
    每个测试函数使用独立的WealthService实例（内存数据库）
    
    适用于：单元测试，快速执行，自动清理
    """
    # 设置测试环境变量，确保使用内存数据库
    os.environ['WEALTH_LITE_ENV'] = 'test'
    service = WealthService()
    yield service
    service.close()
    # 清理环境变量
    if 'WEALTH_LITE_ENV' in os.environ:
        del os.environ['WEALTH_LITE_ENV']


@pytest.fixture(scope="session")
def temp_db():
    """
    会话级别的临时文件数据库
    
    适用于：集成测试，跨测试数据共享
    """
    fd, db_path = tempfile.mkstemp(suffix='.db', prefix='wealth_lite_test_')
    os.close(fd)
    
    try:
        # TODO: 当DatabaseManager实现后启用
        # db_manager = DatabaseManager(db_path)
        # db_manager.initialize_schema()
        # yield db_manager
        # db_manager.close()
        
        # 临时返回路径，后续替换
        yield db_path
    finally:
        # 清理临时文件
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def sample_asset() -> Asset:
    """提供测试用的示例资产"""
    return Asset(
        asset_name="测试储蓄账户",
        asset_type=AssetType.CASH,
        asset_subtype=AssetSubType.CHECKING_ACCOUNT,
        currency=Currency.CNY,
        risk_level=RiskLevel.VERY_LOW,
        liquidity_level=LiquidityLevel.VERY_HIGH,
        description="用于测试的储蓄账户"
    )


@pytest.fixture
def sample_cash_transaction(sample_asset) -> CashTransaction:
    """提供测试用的现金交易"""
    return CashTransaction(
        asset_id=sample_asset.asset_id,
        transaction_type=TransactionType.DEPOSIT,
        transaction_date=date(2024, 1, 15),
        amount=Decimal('10000.00'),
        currency=Currency.CNY,
        notes="测试存款",
        interest_rate=Decimal('2.5'),
        account_type="SAVINGS"
    )


@pytest.fixture
def sample_assets_list() -> list[Asset]:
    """提供多个测试资产"""
    return [
        Asset(
            asset_name="招商银行储蓄",
            asset_type=AssetType.CASH,
            asset_subtype=AssetSubType.CHECKING_ACCOUNT,
            currency=Currency.CNY,
            risk_level=RiskLevel.VERY_LOW
        ),
        Asset(
            asset_name="国债ETF",
            asset_type=AssetType.FIXED_INCOME,
            asset_subtype=AssetSubType.GOVERNMENT_BOND,
            currency=Currency.CNY,
            risk_level=RiskLevel.LOW
        ),
        Asset(
            asset_name="沪深300ETF",
            asset_type=AssetType.EQUITY,
            asset_subtype=AssetSubType.DOMESTIC_STOCK,
            currency=Currency.CNY,
            risk_level=RiskLevel.MEDIUM
        )
    ]


@pytest.fixture
def clean_test_data():
    """
    测试数据清理fixture
    
    确保测试之间的数据隔离
    """
    # 测试前的设置
    yield
    # 测试后的清理
    # TODO: 添加数据清理逻辑


# pytest配置
def pytest_configure(config):
    """pytest启动时的配置"""
    # 设置测试环境变量
    os.environ['WEALTH_LITE_ENV'] = 'test'
    
    # 添加自定义标记
    config.addinivalue_line(
        "markers", "unit: 标记单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 标记集成测试"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集行为"""
    # 自动为不同目录的测试添加标记
    for item in items:
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration) 