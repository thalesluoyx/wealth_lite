"""
测试快照相关服务
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
from decimal import Decimal

from src.wealth_lite.data.database import DatabaseManager
from src.wealth_lite.services.snapshot_service import SnapshotService, AIConfigService, AIAnalysisService
from src.wealth_lite.services.wealth_service import WealthService
from src.wealth_lite.models.snapshot import PortfolioSnapshot, AIAnalysisConfig, AIAnalysisResult
from src.wealth_lite.models.portfolio import Portfolio
from src.wealth_lite.models.enums import SnapshotType, AIType, Currency


@pytest.fixture
def mock_db_manager():
    """创建模拟的数据库管理器"""
    return Mock(spec=DatabaseManager)


@pytest.fixture
def mock_wealth_service():
    """模拟WealthService"""
    mock = Mock()
    mock.get_portfolio = Mock()
    return mock


@pytest.fixture
def mock_portfolio():
    """创建模拟的投资组合"""
    portfolio = Mock(spec=Portfolio)
    portfolio.base_currency = Currency.CNY
    portfolio.total_value = Decimal('100000')
    portfolio.total_cost = Decimal('90000')
    portfolio.calculate_total_return.return_value = Decimal('10000')
    portfolio.calculate_total_return_rate.return_value = 11.11
    portfolio.positions = []
    portfolio.calculate_asset_allocation.return_value = {}
    portfolio.calculate_performance_metrics.return_value = {}
    return portfolio


@pytest.fixture
def snapshot_service(mock_db_manager, mock_wealth_service):
    """创建快照服务"""
    return SnapshotService(mock_db_manager, mock_wealth_service)


@pytest.fixture
def ai_config_service(mock_db_manager):
    """创建AI配置服务"""
    return AIConfigService(mock_db_manager)


@pytest.fixture
def ai_analysis_service(mock_db_manager):
    """创建AI分析服务"""
    return AIAnalysisService(mock_db_manager)


class TestSnapshotService:
    """测试SnapshotService"""
    
    def test_create_startup_snapshot_success(self, snapshot_service, mock_wealth_service, mock_portfolio):
        """测试成功创建启动快照"""
        # 设置模拟
        mock_wealth_service.get_portfolio.return_value = mock_portfolio
        
        with patch.object(snapshot_service.snapshot_repository, 'get_by_date_and_type', return_value=None), \
             patch.object(snapshot_service.snapshot_repository, 'save', return_value=True), \
             patch.object(PortfolioSnapshot, 'from_portfolio') as mock_from_portfolio:
            
            mock_snapshot = Mock(spec=PortfolioSnapshot)
            mock_snapshot.snapshot_id = 'test-snapshot'
            mock_from_portfolio.return_value = mock_snapshot
            
            # 调用方法
            result = snapshot_service.create_startup_snapshot()
            
            # 验证结果
            assert result is not None
            assert result.snapshot_id == 'test-snapshot'
            mock_wealth_service.get_portfolio.assert_called_once()
            mock_from_portfolio.assert_called_once_with(
                mock_portfolio, 
                SnapshotType.AUTO, 
                "系统启动时自动创建"
            )
    
    def test_create_startup_snapshot_no_portfolio(self, snapshot_service, mock_wealth_service):
        """测试无投资组合时创建启动快照"""
        # 设置模拟：无投资组合
        mock_wealth_service.get_portfolio.return_value = None
        
        # 调用方法
        result = snapshot_service.create_startup_snapshot()
        
        # 验证结果
        assert result is None
        mock_wealth_service.get_portfolio.assert_called_once()
    
    def test_create_startup_snapshot_with_existing(self, snapshot_service, mock_wealth_service, mock_portfolio):
        """测试存在旧快照时创建启动快照"""
        # 创建旧快照
        existing_snapshot = Mock(spec=PortfolioSnapshot)
        existing_snapshot.snapshot_id = 'old-snapshot'
        
        mock_wealth_service.get_portfolio.return_value = mock_portfolio
        
        with patch.object(snapshot_service.snapshot_repository, 'get_by_date_and_type', return_value=existing_snapshot), \
             patch.object(snapshot_service.snapshot_repository, 'delete', return_value=True) as mock_delete, \
             patch.object(snapshot_service.snapshot_repository, 'save', return_value=True), \
             patch.object(PortfolioSnapshot, 'from_portfolio') as mock_from_portfolio:
            
            mock_snapshot = Mock(spec=PortfolioSnapshot)
            mock_snapshot.snapshot_id = 'new-snapshot'
            mock_from_portfolio.return_value = mock_snapshot
            
            # 调用方法
            result = snapshot_service.create_startup_snapshot()
            
            # 验证结果
            assert result is not None
            mock_delete.assert_called_once_with('old-snapshot')
    
    def test_create_manual_snapshot_success(self, snapshot_service, mock_wealth_service, mock_portfolio):
        """测试成功创建手动快照"""
        mock_wealth_service.get_portfolio.return_value = mock_portfolio
        
        with patch.object(snapshot_service.snapshot_repository, 'get_by_date_and_type', return_value=None), \
             patch.object(snapshot_service.snapshot_repository, 'save', return_value=True), \
             patch.object(PortfolioSnapshot, 'from_portfolio') as mock_from_portfolio:
            
            mock_snapshot = Mock(spec=PortfolioSnapshot)
            mock_snapshot.snapshot_id = 'manual-snapshot'
            mock_from_portfolio.return_value = mock_snapshot
            
            # 调用方法
            result = snapshot_service.create_manual_snapshot("测试备注")
            
            # 验证结果
            assert result is not None
            assert result.snapshot_id == 'manual-snapshot'
            mock_from_portfolio.assert_called_once_with(
                mock_portfolio, 
                SnapshotType.MANUAL, 
                "测试备注"
            )
    
    def test_get_snapshot_by_id(self, snapshot_service):
        """测试根据ID获取快照"""
        mock_snapshot = Mock(spec=PortfolioSnapshot)
        
        with patch.object(snapshot_service.snapshot_repository, 'get_by_id', return_value=mock_snapshot):
            result = snapshot_service.get_snapshot_by_id('test-id')
            assert result == mock_snapshot
    
    def test_get_snapshots_by_type(self, snapshot_service):
        """测试根据类型获取快照列表"""
        mock_snapshots = [Mock(spec=PortfolioSnapshot) for _ in range(3)]
        
        with patch.object(snapshot_service.snapshot_repository, 'get_by_type', return_value=mock_snapshots):
            result = snapshot_service.get_snapshots_by_type(SnapshotType.AUTO, limit=10)
            assert len(result) == 3
            assert result == mock_snapshots
    
    def test_delete_snapshot_success(self, snapshot_service):
        """测试成功删除快照"""
        mock_snapshot = Mock(spec=PortfolioSnapshot)
        mock_snapshot.is_today = False
        
        with patch.object(snapshot_service.snapshot_repository, 'get_by_id', return_value=mock_snapshot), \
             patch.object(snapshot_service.snapshot_repository, 'delete', return_value=True):
            
            result = snapshot_service.delete_snapshot('test-id')
            assert result is True
    
    def test_delete_snapshot_today_blocked(self, snapshot_service):
        """测试删除今天的快照被阻止"""
        mock_snapshot = Mock(spec=PortfolioSnapshot)
        mock_snapshot.is_today = True
        
        with patch.object(snapshot_service.snapshot_repository, 'get_by_id', return_value=mock_snapshot):
            result = snapshot_service.delete_snapshot('test-id')
            assert result is False
    
    def test_compare_snapshots_success(self, snapshot_service):
        """测试成功对比快照"""
        mock_snapshot1 = Mock(spec=PortfolioSnapshot)
        mock_snapshot2 = Mock(spec=PortfolioSnapshot)
        mock_comparison = {'value_change': {'absolute': 1000}}
        
        mock_snapshot2.compare_with.return_value = mock_comparison
        
        with patch.object(snapshot_service.snapshot_repository, 'get_by_id', side_effect=[mock_snapshot1, mock_snapshot2]):
            result = snapshot_service.compare_snapshots('id1', 'id2')
            assert result == mock_comparison
            mock_snapshot2.compare_with.assert_called_once_with(mock_snapshot1)
    
    def test_compare_snapshots_not_found(self, snapshot_service):
        """测试对比不存在的快照"""
        with patch.object(snapshot_service.snapshot_repository, 'get_by_id', return_value=None):
            result = snapshot_service.compare_snapshots('id1', 'id2')
            assert result is None
    
    def test_get_snapshot_statistics(self, snapshot_service):
        """测试获取快照统计信息"""
        with patch.object(snapshot_service.snapshot_repository, 'count_by_type', side_effect=[5, 3]):
            result = snapshot_service.get_snapshot_statistics()
            
            assert result['auto_count'] == 5
            assert result['manual_count'] == 3
            assert result['total_count'] == 8


class TestAIConfigService:
    """测试AIConfigService"""
    
    def test_get_default_config_exists(self, ai_config_service):
        """测试获取已存在的默认配置"""
        mock_config = Mock(spec=AIAnalysisConfig)
        
        with patch.object(ai_config_service.config_repository, 'get_default_config', return_value=mock_config):
            result = ai_config_service.get_default_config()
            assert result == mock_config
    
    def test_get_default_config_create_new(self, ai_config_service):
        """测试创建新的默认配置"""
        with patch.object(ai_config_service.config_repository, 'get_default_config', return_value=None), \
             patch.object(ai_config_service.config_repository, 'save', return_value=True):
            
            result = ai_config_service.get_default_config()
            
            assert result is not None
            assert result.config_name == "默认本地AI"
            assert result.ai_type == AIType.LOCAL
            assert result.is_default is True
    
    def test_switch_ai_type_success(self, ai_config_service):
        """测试成功切换AI类型"""
        mock_config = Mock(spec=AIAnalysisConfig)
        mock_config.config_id = 'test-config'
        
        with patch.object(ai_config_service.config_repository, 'get_by_type', return_value=[mock_config]), \
             patch.object(ai_config_service.config_repository, 'set_default', return_value=True):
            
            result = ai_config_service.switch_ai_type(AIType.CLOUD)
            assert result == mock_config
    
    def test_switch_ai_type_no_config(self, ai_config_service):
        """测试切换不存在的AI类型"""
        with patch.object(ai_config_service.config_repository, 'get_by_type', return_value=[]):
            result = ai_config_service.switch_ai_type(AIType.CLOUD)
            assert result is None
    
    def test_save_config(self, ai_config_service):
        """测试保存AI配置"""
        mock_config = Mock(spec=AIAnalysisConfig)
        
        with patch.object(ai_config_service.config_repository, 'save', return_value=True):
            result = ai_config_service.save_config(mock_config)
            assert result is True
            # 验证更新时间戳被设置
            assert mock_config.updated_date is not None
    
    def test_delete_config_success(self, ai_config_service):
        """测试成功删除配置"""
        mock_config = Mock(spec=AIAnalysisConfig)
        mock_config.is_default = False
        
        with patch.object(ai_config_service.config_repository, 'get_by_id', return_value=mock_config), \
             patch.object(ai_config_service.config_repository, 'delete', return_value=True):
            
            result = ai_config_service.delete_config('test-id')
            assert result is True
    
    def test_delete_config_default_blocked(self, ai_config_service):
        """测试删除默认配置被阻止"""
        mock_config = Mock(spec=AIAnalysisConfig)
        mock_config.is_default = True
        
        with patch.object(ai_config_service.config_repository, 'get_by_id', return_value=mock_config):
            result = ai_config_service.delete_config('test-id')
            assert result is False


class TestAIAnalysisService:
    """测试AIAnalysisService"""
    
    def test_analyze_snapshots_local_ai_success(self, ai_analysis_service):
        """测试本地AI分析成功"""
        # 创建测试数据
        snapshot1 = PortfolioSnapshot(
            snapshot_id='snap1',
            snapshot_date=date(2023, 12, 1),
            total_value=Decimal('100000')
        )
        snapshot2 = PortfolioSnapshot(
            snapshot_id='snap2',
            snapshot_date=date(2023, 12, 31),
            total_value=Decimal('110000')
        )
        config = AIAnalysisConfig(
            config_id='config1',
            ai_type=AIType.LOCAL,
            local_model_name='llama3.1:8b'
        )
        
        # 模拟AI响应
        mock_ai_response = '{"summary": "测试摘要", "advice": "测试建议", "risk": "测试风险"}'
        
        with patch.object(ai_analysis_service.config_service, 'get_default_config', return_value=config), \
             patch.object(ai_analysis_service, '_call_local_ai', return_value=mock_ai_response), \
             patch.object(ai_analysis_service.analysis_repository, 'save', return_value=True):
            
            result = ai_analysis_service.analyze_snapshots(snapshot1, snapshot2, config)
            
            assert result.analysis_status == 'SUCCESS'
            assert result.analysis_summary == '测试摘要'
            assert result.investment_advice == '测试建议'
            assert result.risk_assessment == '测试风险'
    
    def test_analyze_snapshots_ai_error(self, ai_analysis_service):
        """测试AI分析失败"""
        snapshot1 = PortfolioSnapshot(snapshot_id='snap1')
        snapshot2 = PortfolioSnapshot(snapshot_id='snap2')
        config = AIAnalysisConfig(
            config_id='config1',
            ai_type=AIType.LOCAL
        )
        
        with patch.object(ai_analysis_service.config_service, 'get_default_config', return_value=config), \
             patch.object(ai_analysis_service, '_call_local_ai', side_effect=Exception("AI服务不可用")), \
             patch.object(ai_analysis_service.analysis_repository, 'save', return_value=True):
            
            result = ai_analysis_service.analyze_snapshots(snapshot1, snapshot2, config)
            
            assert result.analysis_status == 'FAILED'
            assert result.error_message == "AI服务不可用"
    
    def test_prepare_analysis_data(self, ai_analysis_service):
        """测试准备分析数据"""
        snapshot1 = PortfolioSnapshot(
            snapshot_date=date(2023, 12, 1),
            total_value=Decimal('100000'),
            total_return=Decimal('5000'),
            cash_value=Decimal('30000'),
            fixed_income_value=Decimal('70000')
        )
        snapshot2 = PortfolioSnapshot(
            snapshot_date=date(2023, 12, 31),
            total_value=Decimal('110000'),
            total_return=Decimal('8000'),
            cash_value=Decimal('25000'),
            fixed_income_value=Decimal('85000')
        )
        
        data = ai_analysis_service._prepare_analysis_data(snapshot1, snapshot2)
        
        assert data['snapshot1']['date'] == '2023-12-01'
        assert data['snapshot1']['total_value'] == 100000.0
        assert data['snapshot1']['allocation']['cash'] == 30000.0
        assert data['snapshot2']['date'] == '2023-12-31'
        assert data['snapshot2']['total_value'] == 110000.0
        assert data['snapshot2']['allocation']['fixed_income'] == 85000.0
    
    def test_build_analysis_prompt(self, ai_analysis_service):
        """测试构建分析提示词"""
        data = {
            'snapshot1': {
                'date': '2023-12-01',
                'total_value': 100000.0,
                'total_return': 5000.0,
                'total_return_rate': 5.0,
                'allocation': {'cash': 30000.0, 'fixed_income': 70000.0, 'equity': 0.0}
            },
            'snapshot2': {
                'date': '2023-12-31',
                'total_value': 110000.0,
                'total_return': 8000.0,
                'total_return_rate': 8.0,
                'allocation': {'cash': 25000.0, 'fixed_income': 85000.0, 'equity': 0.0}
            }
        }
        
        prompt = ai_analysis_service._build_analysis_prompt(data)
        
        assert '2023-12-01' in prompt
        assert '2023-12-31' in prompt
        assert '¥100,000.00' in prompt
        assert '¥110,000.00' in prompt
        assert 'JSON格式' in prompt
    
    def test_parse_ai_response_json(self, ai_analysis_service):
        """测试解析JSON格式的AI响应"""
        response = '这是一些前缀文本 {"summary": "测试摘要", "advice": "测试建议", "risk": "测试风险"} 这是一些后缀文本'
        
        result = ai_analysis_service._parse_ai_response(response)
        
        assert result['summary'] == '测试摘要'
        assert result['advice'] == '测试建议'
        assert result['risk'] == '测试风险'
    
    def test_parse_ai_response_non_json(self, ai_analysis_service):
        """测试解析非JSON格式的AI响应"""
        response = '这是一个纯文本响应，没有JSON格式'
        
        result = ai_analysis_service._parse_ai_response(response)
        
        assert result['summary'] == response
        assert result['advice'] == '请查看完整分析内容'
        assert result['risk'] == '请查看完整分析内容'
    
    @patch('src.wealth_lite.services.snapshot_service.requests.post')
    def test_call_local_ai(self, mock_post, ai_analysis_service):
        """测试调用本地AI"""
        # 设置模拟响应
        mock_response = Mock()
        mock_response.json.return_value = {'response': '测试AI响应'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        config = AIAnalysisConfig(
            ai_type=AIType.LOCAL,
            local_model_name='llama3.1:8b',
            local_api_port=11434,
            temperature=0.7,
            max_tokens=4000
        )

        # 使用正确的数据结构
        data = {
            'snapshot1': {
                'date': '2023-12-01T00:00:00',
                'total_value': 100000.0,
                'total_return': 5000.0,
                'total_return_rate': 5.0,
                'allocation': {
                    'cash': 30000.0,
                    'fixed_income': 50000.0,
                    'equity': 20000.0,
                    'real_estate': 0.0,
                    'commodity': 0.0
                }
            },
            'snapshot2': {
                'date': '2023-12-31T00:00:00',
                'total_value': 110000.0,
                'total_return': 8000.0,
                'total_return_rate': 8.0,
                'allocation': {
                    'cash': 25000.0,
                    'fixed_income': 60000.0,
                    'equity': 25000.0,
                    'real_estate': 0.0,
                    'commodity': 0.0
                }
            }
        }

        result = ai_analysis_service._call_local_ai(data, config)
        
        assert result == '测试AI响应'
        mock_post.assert_called_once()
        
        # 验证请求参数
        call_args = mock_post.call_args
        assert call_args[1]['json']['model'] == 'llama3.1:8b'
        assert call_args[1]['json']['options']['temperature'] == 0.7
    
    def test_call_cloud_ai_unsupported_provider(self, ai_analysis_service):
        """测试调用不支持的云端AI提供商"""
        config = AIAnalysisConfig(
            ai_type=AIType.CLOUD,
            cloud_provider='UNSUPPORTED'
        )
        
        with pytest.raises(ValueError, match="不支持的云端AI提供商"):
            ai_analysis_service._call_cloud_ai({}, config) 