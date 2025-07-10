"""
测试快照相关模型
"""

import pytest
from datetime import date, datetime
from decimal import Decimal

from src.wealth_lite.models.snapshot import PortfolioSnapshot, AIAnalysisConfig, AIAnalysisResult
from src.wealth_lite.models.enums import SnapshotType, AIType, Currency


class TestPortfolioSnapshot:
    """测试PortfolioSnapshot模型"""
    
    def test_create_snapshot(self):
        """测试创建快照"""
        snapshot = PortfolioSnapshot(
            snapshot_type=SnapshotType.MANUAL,
            base_currency=Currency.CNY,
            total_value=Decimal('100000'),
            total_cost=Decimal('90000'),
            total_return=Decimal('10000'),
            total_return_rate=Decimal('11.11'),
            notes="测试快照"
        )
        
        assert snapshot.snapshot_type == SnapshotType.MANUAL
        assert snapshot.base_currency == Currency.CNY
        assert snapshot.total_value == Decimal('100000')
        assert snapshot.total_cost == Decimal('90000')
        assert snapshot.total_return == Decimal('10000')
        assert snapshot.total_return_rate == Decimal('11.11')
        assert snapshot.notes == "测试快照"
        assert snapshot.position_count == 0
        assert "手动快照" in snapshot.display_name
    
    def test_is_today_property(self):
        """测试is_today属性"""
        today_snapshot = PortfolioSnapshot(snapshot_date=date.today())
        assert today_snapshot.is_today is True
        
        yesterday_snapshot = PortfolioSnapshot(snapshot_date=date(2023, 1, 1))
        assert yesterday_snapshot.is_today is False
    
    def test_display_name_property(self):
        """测试display_name属性"""
        auto_snapshot = PortfolioSnapshot(
            snapshot_type=SnapshotType.AUTO,
            snapshot_date=date(2023, 12, 25)
        )
        assert auto_snapshot.display_name == "2023-12-25 自动快照"
        
        manual_snapshot = PortfolioSnapshot(
            snapshot_type=SnapshotType.MANUAL,
            snapshot_date=date(2023, 12, 25)
        )
        assert manual_snapshot.display_name == "2023-12-25 手动快照"
    
    def test_display_return_property(self):
        """测试display_return属性"""
        snapshot = PortfolioSnapshot(
            base_currency=Currency.CNY,
            total_return=Decimal('12345.67'),
            total_return_rate=Decimal('15.25')
        )
        assert snapshot.display_return == "¥12,345.67 (15.25%)"
    
    def test_compare_with_same_currency(self):
        """测试同币种快照对比"""
        snapshot1 = PortfolioSnapshot(
            snapshot_date=date(2023, 12, 1),
            base_currency=Currency.CNY,
            total_value=Decimal('100000'),
            cash_value=Decimal('30000'),
            fixed_income_value=Decimal('70000')
        )
        
        snapshot2 = PortfolioSnapshot(
            snapshot_date=date(2023, 12, 31),
            base_currency=Currency.CNY,
            total_value=Decimal('110000'),
            cash_value=Decimal('25000'),
            fixed_income_value=Decimal('85000')
        )
        
        comparison = snapshot2.compare_with(snapshot1)
        
        assert comparison['period']['days'] == 30
        assert comparison['value_change']['absolute'] == Decimal('10000')
        assert comparison['value_change']['rate'] == Decimal('0.1')  # 10%
        assert comparison['type_changes']['cash']['change'] == Decimal('-5000')
        assert comparison['type_changes']['fixed_income']['change'] == Decimal('15000')
    
    def test_compare_with_different_currency(self):
        """测试不同币种快照对比应该抛出异常"""
        snapshot1 = PortfolioSnapshot(base_currency=Currency.CNY)
        snapshot2 = PortfolioSnapshot(base_currency=Currency.USD)
        
        with pytest.raises(ValueError, match="无法比较不同基础货币的快照"):
            snapshot2.compare_with(snapshot1)
    
    def test_to_dict(self):
        """测试转换为字典"""
        snapshot = PortfolioSnapshot(
            snapshot_type=SnapshotType.AUTO,
            base_currency=Currency.CNY,
            total_value=Decimal('100000'),
            notes="测试"
        )
        
        data = snapshot.to_dict()
        
        assert data['snapshot_type'] == 'AUTO'
        assert data['base_currency'] == 'CNY'
        assert data['total_value'] == '100000'
        assert data['notes'] == "测试"
        assert 'display_name' in data
        assert 'position_count' in data
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            'snapshot_id': 'test-id',
            'snapshot_date': '2023-12-25',
            'snapshot_time': '2023-12-25T10:00:00',
            'snapshot_type': 'MANUAL',
            'base_currency': 'CNY',
            'total_value': '100000',
            'total_cost': '90000',
            'notes': '测试快照'
        }
        
        snapshot = PortfolioSnapshot.from_dict(data)
        
        assert snapshot.snapshot_id == 'test-id'
        assert snapshot.snapshot_date == date(2023, 12, 25)
        assert snapshot.snapshot_type == SnapshotType.MANUAL
        assert snapshot.base_currency == Currency.CNY
        assert snapshot.total_value == Decimal('100000')
        assert snapshot.total_cost == Decimal('90000')
        assert snapshot.notes == '测试快照'
    
    def test_equality_and_hash(self):
        """测试相等性和哈希"""
        snapshot1 = PortfolioSnapshot(snapshot_id='test-id')
        snapshot2 = PortfolioSnapshot(snapshot_id='test-id')
        snapshot3 = PortfolioSnapshot(snapshot_id='different-id')
        
        assert snapshot1 == snapshot2
        assert snapshot1 != snapshot3
        assert hash(snapshot1) == hash(snapshot2)
        assert hash(snapshot1) != hash(snapshot3)


class TestAIAnalysisConfig:
    """测试AIAnalysisConfig模型"""
    
    def test_create_local_config(self):
        """测试创建本地AI配置"""
        config = AIAnalysisConfig(
            config_name="本地AI",
            ai_type=AIType.LOCAL,
            local_model_name="llama3.1:8b",
            local_api_port=11434
        )
        
        assert config.config_name == "本地AI"
        assert config.ai_type == AIType.LOCAL
        assert config.local_model_name == "llama3.1:8b"
        assert config.local_api_port == 11434
        assert config.display_name == "本地AI (本地AI)"
    
    def test_create_cloud_config(self):
        """测试创建云端AI配置"""
        config = AIAnalysisConfig(
            config_name="OpenAI",
            ai_type=AIType.CLOUD,
            cloud_provider="OPENAI",
            cloud_model_name="gpt-4",
            cloud_api_key="test-key"
        )
        
        assert config.config_name == "OpenAI"
        assert config.ai_type == AIType.CLOUD
        assert config.cloud_provider == "OPENAI"
        assert config.cloud_model_name == "gpt-4"
        assert config.cloud_api_key == "test-key"
        assert config.display_name == "OpenAI (云端AI)"
    
    def test_to_dict(self):
        """测试转换为字典"""
        config = AIAnalysisConfig(
            config_name="测试配置",
            ai_type=AIType.LOCAL,
            is_default=True
        )
        
        data = config.to_dict()
        
        assert data['config_name'] == "测试配置"
        assert data['ai_type'] == 'LOCAL'
        assert data['is_default'] is True
        assert 'display_name' in data
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            'config_id': 'test-config',
            'config_name': '测试配置',
            'ai_type': 'CLOUD',
            'is_default': True,
            'cloud_provider': 'OPENAI'
        }
        
        config = AIAnalysisConfig.from_dict(data)
        
        assert config.config_id == 'test-config'
        assert config.config_name == '测试配置'
        assert config.ai_type == AIType.CLOUD
        assert config.is_default is True
        assert config.cloud_provider == 'OPENAI'


class TestAIAnalysisResult:
    """测试AIAnalysisResult模型"""
    
    def test_create_result(self):
        """测试创建分析结果"""
        result = AIAnalysisResult(
            snapshot1_id='snap1',
            snapshot2_id='snap2',
            config_id='config1',
            analysis_content='分析内容',
            analysis_summary='分析摘要',
            analysis_status='SUCCESS',
            processing_time_ms=1500
        )
        
        assert result.snapshot1_id == 'snap1'
        assert result.snapshot2_id == 'snap2'
        assert result.config_id == 'config1'
        assert result.analysis_content == '分析内容'
        assert result.analysis_summary == '分析摘要'
        assert result.analysis_status == 'SUCCESS'
        assert result.processing_time_ms == 1500
        assert result.is_success is True
    
    def test_is_success_property(self):
        """测试is_success属性"""
        success_result = AIAnalysisResult(analysis_status='SUCCESS')
        assert success_result.is_success is True
        
        failed_result = AIAnalysisResult(analysis_status='FAILED')
        assert failed_result.is_success is False
        
        pending_result = AIAnalysisResult(analysis_status='PENDING')
        assert pending_result.is_success is False
    
    def test_display_name_property(self):
        """测试display_name属性"""
        result = AIAnalysisResult(
            created_date=datetime(2023, 12, 25, 14, 30, 0)
        )
        assert result.display_name == "AI分析 - 2023-12-25 14:30"
    
    def test_to_dict(self):
        """测试转换为字典"""
        result = AIAnalysisResult(
            analysis_status='SUCCESS',
            analysis_summary='测试摘要',
            processing_time_ms=2000
        )
        
        data = result.to_dict()
        
        assert data['analysis_status'] == 'SUCCESS'
        assert data['analysis_summary'] == '测试摘要'
        assert data['processing_time_ms'] == 2000
        assert data['is_success'] is True
        assert 'display_name' in data
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            'analysis_id': 'test-analysis',
            'snapshot1_id': 'snap1',
            'snapshot2_id': 'snap2',
            'analysis_status': 'FAILED',
            'error_message': '测试错误',
            'created_date': '2023-12-25T10:00:00'
        }
        
        result = AIAnalysisResult.from_dict(data)
        
        assert result.analysis_id == 'test-analysis'
        assert result.snapshot1_id == 'snap1'
        assert result.snapshot2_id == 'snap2'
        assert result.analysis_status == 'FAILED'
        assert result.error_message == '测试错误'
        assert result.created_date == datetime(2023, 12, 25, 10, 0, 0)
        assert result.is_success is False 