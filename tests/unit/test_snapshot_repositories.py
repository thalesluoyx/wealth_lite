"""
测试快照相关Repository
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal

from src.wealth_lite.data.database import DatabaseManager
from src.wealth_lite.data.snapshot_repository import SnapshotRepository, AIConfigRepository, AIAnalysisRepository
from src.wealth_lite.models.snapshot import PortfolioSnapshot, AIAnalysisConfig, AIAnalysisResult
from src.wealth_lite.models.enums import SnapshotType, AIType, Currency


@pytest.fixture
def db_manager():
    """创建内存数据库管理器"""
    return DatabaseManager(":memory:")


@pytest.fixture
def snapshot_repo(db_manager):
    """创建快照Repository"""
    return SnapshotRepository(db_manager)


@pytest.fixture
def ai_config_repo(db_manager):
    """创建AI配置Repository"""
    return AIConfigRepository(db_manager)


@pytest.fixture
def ai_analysis_repo(db_manager):
    """创建AI分析Repository"""
    return AIAnalysisRepository(db_manager)


@pytest.fixture
def sample_snapshot():
    """创建测试快照"""
    return PortfolioSnapshot(
        snapshot_id='test-snapshot-1',
        snapshot_date=date(2023, 12, 25),
        snapshot_type=SnapshotType.MANUAL,
        base_currency=Currency.CNY,
        total_value=Decimal('100000'),
        total_cost=Decimal('90000'),
        total_return=Decimal('10000'),
        total_return_rate=Decimal('11.11'),
        cash_value=Decimal('30000'),
        fixed_income_value=Decimal('70000'),
        notes='测试快照'
    )


@pytest.fixture
def sample_ai_config():
    """创建测试AI配置"""
    return AIAnalysisConfig(
        config_id='test-config-1',
        config_name='测试本地AI',
        ai_type=AIType.LOCAL,
        is_default=True,
        local_model_name='llama3.1:8b',
        local_api_port=11434
    )


@pytest.fixture
def sample_ai_result():
    """创建测试AI分析结果"""
    return AIAnalysisResult(
        analysis_id='test-analysis-1',
        snapshot1_id='snap1',
        snapshot2_id='snap2',
        config_id='config1',
        analysis_content='测试分析内容',
        analysis_summary='测试分析摘要',
        analysis_status='SUCCESS',
        processing_time_ms=1500
    )


class TestSnapshotRepository:
    """测试SnapshotRepository"""
    
    def test_save_and_get_snapshot(self, snapshot_repo, sample_snapshot):
        """测试保存和获取快照"""
        # 保存快照
        assert snapshot_repo.save(sample_snapshot) is True
        
        # 根据ID获取快照
        retrieved = snapshot_repo.get_by_id(sample_snapshot.snapshot_id)
        assert retrieved is not None
        assert retrieved.snapshot_id == sample_snapshot.snapshot_id
        assert retrieved.snapshot_type == sample_snapshot.snapshot_type
        assert retrieved.base_currency == sample_snapshot.base_currency
        assert retrieved.total_value == sample_snapshot.total_value
        assert retrieved.notes == sample_snapshot.notes
    
    def test_get_by_date_and_type(self, snapshot_repo, sample_snapshot):
        """测试根据日期和类型获取快照"""
        # 保存快照
        snapshot_repo.save(sample_snapshot)
        
        # 根据日期和类型获取
        retrieved = snapshot_repo.get_by_date_and_type(
            sample_snapshot.snapshot_date, 
            sample_snapshot.snapshot_type
        )
        assert retrieved is not None
        assert retrieved.snapshot_id == sample_snapshot.snapshot_id
        
        # 测试不存在的情况
        non_existent = snapshot_repo.get_by_date_and_type(
            date(2023, 1, 1), 
            SnapshotType.AUTO
        )
        assert non_existent is None
    
    def test_get_by_type(self, snapshot_repo):
        """测试根据类型获取快照列表"""
        # 创建多个快照
        snapshots = [
            PortfolioSnapshot(
                snapshot_id=f'auto-{i}',
                snapshot_date=date(2023, 12, i+1),
                snapshot_type=SnapshotType.AUTO,
                total_value=Decimal(f'{100000+i*1000}')
            ) for i in range(3)
        ]
        
        manual_snapshots = [
            PortfolioSnapshot(
                snapshot_id=f'manual-{i}',
                snapshot_date=date(2023, 12, i+10),
                snapshot_type=SnapshotType.MANUAL,
                total_value=Decimal(f'{200000+i*1000}')
            ) for i in range(2)
        ]
        
        # 保存所有快照
        for snapshot in snapshots + manual_snapshots:
            snapshot_repo.save(snapshot)
        
        # 获取自动快照
        auto_snapshots = snapshot_repo.get_by_type(SnapshotType.AUTO)
        assert len(auto_snapshots) == 3
        assert all(s.snapshot_type == SnapshotType.AUTO for s in auto_snapshots)
        
        # 获取手动快照
        manual_retrieved = snapshot_repo.get_by_type(SnapshotType.MANUAL)
        assert len(manual_retrieved) == 2
        assert all(s.snapshot_type == SnapshotType.MANUAL for s in manual_retrieved)
        
        # 测试分页
        limited = snapshot_repo.get_by_type(SnapshotType.AUTO, limit=2)
        assert len(limited) == 2
    
    def test_get_by_date_range(self, snapshot_repo):
        """测试根据日期范围获取快照"""
        # 创建不同日期的快照
        snapshots = [
            PortfolioSnapshot(
                snapshot_id=f'snapshot-{i}',
                snapshot_date=date(2023, 12, i+1),
                snapshot_type=SnapshotType.MANUAL
            ) for i in range(10)
        ]
        
        for snapshot in snapshots:
            snapshot_repo.save(snapshot)
        
        # 测试日期范围查询
        range_snapshots = snapshot_repo.get_by_date_range(
            date(2023, 12, 3), 
            date(2023, 12, 7)
        )
        assert len(range_snapshots) == 5
        assert all(
            date(2023, 12, 3) <= s.snapshot_date <= date(2023, 12, 7) 
            for s in range_snapshots
        )
    
    def test_get_recent_snapshots(self, snapshot_repo):
        """测试获取最近的快照"""
        # 创建最近的快照
        today = date.today()
        snapshots = []
        for i in range(3):
            snapshots.extend([
                PortfolioSnapshot(
                    snapshot_id=f'recent-auto-{i}',
                    snapshot_date=today,
                    snapshot_type=SnapshotType.AUTO
                ),
                PortfolioSnapshot(
                    snapshot_id=f'recent-manual-{i}',
                    snapshot_date=today,
                    snapshot_type=SnapshotType.MANUAL
                )
            ])
        
        for snapshot in snapshots:
            snapshot_repo.save(snapshot)
        
        recent = snapshot_repo.get_recent_snapshots(days=1)
        assert 'auto' in recent
        assert 'manual' in recent
        assert len(recent['auto']) >= 1
        assert len(recent['manual']) >= 1
    
    def test_delete_snapshot(self, snapshot_repo, sample_snapshot):
        """测试删除快照"""
        # 保存快照
        snapshot_repo.save(sample_snapshot)
        
        # 确认快照存在
        assert snapshot_repo.get_by_id(sample_snapshot.snapshot_id) is not None
        
        # 删除快照
        assert snapshot_repo.delete(sample_snapshot.snapshot_id) is True
        
        # 确认快照已删除
        assert snapshot_repo.get_by_id(sample_snapshot.snapshot_id) is None
        
        # 删除不存在的快照
        assert snapshot_repo.delete('non-existent-id') is False
    
    def test_count_by_type(self, snapshot_repo):
        """测试按类型统计快照数量"""
        # 创建不同类型的快照，使用不同日期避免唯一约束冲突
        auto_snapshots = [
            PortfolioSnapshot(
                snapshot_id=f'auto-count-{i}',
                snapshot_date=date.today() - timedelta(days=i),
                snapshot_type=SnapshotType.AUTO
            ) for i in range(3)
        ]
        
        manual_snapshots = [
            PortfolioSnapshot(
                snapshot_id=f'manual-count-{i}',
                snapshot_date=date.today() - timedelta(days=i+10),
                snapshot_type=SnapshotType.MANUAL
            ) for i in range(2)
        ]
        
        # 保存快照
        for snapshot in auto_snapshots + manual_snapshots:
            snapshot_repo.save(snapshot)
        
        # 统计数量
        auto_count = snapshot_repo.count_by_type(SnapshotType.AUTO)
        manual_count = snapshot_repo.count_by_type(SnapshotType.MANUAL)
        
        assert auto_count == 3
        assert manual_count == 2


class TestAIConfigRepository:
    """测试AIConfigRepository"""
    
    def test_save_and_get_config(self, ai_config_repo, sample_ai_config):
        """测试保存和获取AI配置"""
        # 保存配置
        assert ai_config_repo.save(sample_ai_config) is True
        
        # 根据ID获取配置
        retrieved = ai_config_repo.get_by_id(sample_ai_config.config_id)
        assert retrieved is not None
        assert retrieved.config_id == sample_ai_config.config_id
        assert retrieved.config_name == sample_ai_config.config_name
        assert retrieved.ai_type == sample_ai_config.ai_type
        assert retrieved.is_default == sample_ai_config.is_default
    
    def test_get_default_config(self, ai_config_repo):
        """测试获取默认配置"""
        # 创建配置
        config1 = AIAnalysisConfig(
            config_id='config1',
            config_name='配置1',
            ai_type=AIType.LOCAL,
            is_default=False
        )
        config2 = AIAnalysisConfig(
            config_id='config2',
            config_name='配置2',
            ai_type=AIType.CLOUD,
            is_default=True
        )
        
        ai_config_repo.save(config1)
        ai_config_repo.save(config2)
        
        # 获取默认配置
        default = ai_config_repo.get_default_config()
        assert default is not None
        assert default.config_id == 'config2'
        assert default.is_default is True
    
    def test_get_by_type(self, ai_config_repo):
        """测试根据AI类型获取配置"""
        # 创建不同类型的配置
        local_configs = [
            AIAnalysisConfig(
                config_id=f'local-{i}',
                config_name=f'本地配置{i}',
                ai_type=AIType.LOCAL
            ) for i in range(2)
        ]
        
        cloud_configs = [
            AIAnalysisConfig(
                config_id=f'cloud-{i}',
                config_name=f'云端配置{i}',
                ai_type=AIType.CLOUD
            ) for i in range(3)
        ]
        
        # 保存配置
        for config in local_configs + cloud_configs:
            ai_config_repo.save(config)
        
        # 获取本地AI配置
        local_retrieved = ai_config_repo.get_by_type(AIType.LOCAL)
        assert len(local_retrieved) == 2
        assert all(c.ai_type == AIType.LOCAL for c in local_retrieved)
        
        # 获取云端AI配置
        cloud_retrieved = ai_config_repo.get_by_type(AIType.CLOUD)
        assert len(cloud_retrieved) == 3
        assert all(c.ai_type == AIType.CLOUD for c in cloud_retrieved)
    
    def test_set_default(self, ai_config_repo):
        """测试设置默认配置"""
        # 创建多个配置
        configs = [
            AIAnalysisConfig(
                config_id=f'config-{i}',
                config_name=f'配置{i}',
                ai_type=AIType.LOCAL,
                is_default=(i == 0)
            ) for i in range(3)
        ]
        
        for config in configs:
            ai_config_repo.save(config)
        
        # 设置新的默认配置
        assert ai_config_repo.set_default('config-2') is True
        
        # 验证默认配置已更改
        default = ai_config_repo.get_default_config()
        assert default.config_id == 'config-2'
        
        # 验证其他配置不再是默认
        config0 = ai_config_repo.get_by_id('config-0')
        assert config0.is_default is False
    
    def test_delete_config(self, ai_config_repo, sample_ai_config):
        """测试删除AI配置"""
        # 保存配置
        ai_config_repo.save(sample_ai_config)
        
        # 确认配置存在
        assert ai_config_repo.get_by_id(sample_ai_config.config_id) is not None
        
        # 删除配置
        assert ai_config_repo.delete(sample_ai_config.config_id) is True
        
        # 确认配置已删除
        assert ai_config_repo.get_by_id(sample_ai_config.config_id) is None


class TestAIAnalysisRepository:
    """测试AIAnalysisRepository"""
    
    def test_save_and_get_result(self, ai_analysis_repo, sample_ai_result):
        """测试保存和获取AI分析结果"""
        # 首先创建依赖的快照和配置
        snapshot_repo = SnapshotRepository(ai_analysis_repo.db)
        config_repo = AIConfigRepository(ai_analysis_repo.db)
        
        # 创建快照
        snapshot1 = PortfolioSnapshot(
            snapshot_id='snap1',
            snapshot_date=date.today() - timedelta(days=1),
            snapshot_type=SnapshotType.AUTO,
            total_value=Decimal('100000')
        )
        snapshot2 = PortfolioSnapshot(
            snapshot_id='snap2',
            snapshot_date=date.today() - timedelta(days=2),
            snapshot_type=SnapshotType.MANUAL,
            total_value=Decimal('110000')
        )
        snapshot_repo.save(snapshot1)
        snapshot_repo.save(snapshot2)
        
        # 创建配置
        config = AIAnalysisConfig(
            config_id='config1',
            config_name='test-config',
            ai_type=AIType.LOCAL
        )
        config_repo.save(config)
        
        # 保存结果
        assert ai_analysis_repo.save(sample_ai_result) is True
        
        # 根据ID获取结果
        retrieved = ai_analysis_repo.get_by_id(sample_ai_result.analysis_id)
        assert retrieved is not None
        assert retrieved.analysis_id == sample_ai_result.analysis_id
        assert retrieved.snapshot1_id == sample_ai_result.snapshot1_id
        assert retrieved.snapshot2_id == sample_ai_result.snapshot2_id
        assert retrieved.analysis_content == sample_ai_result.analysis_content
        assert retrieved.analysis_status == sample_ai_result.analysis_status
    
    def test_get_by_snapshots(self, ai_analysis_repo):
        """测试根据快照ID获取分析结果"""
        # 首先创建依赖的快照和配置
        snapshot_repo = SnapshotRepository(ai_analysis_repo.db)
        config_repo = AIConfigRepository(ai_analysis_repo.db)
        
        # 创建快照
        snapshots = [
            PortfolioSnapshot(snapshot_id='snap1', snapshot_date=date.today() - timedelta(days=1), snapshot_type=SnapshotType.AUTO, total_value=Decimal('100000')),
            PortfolioSnapshot(snapshot_id='snap2', snapshot_date=date.today() - timedelta(days=2), snapshot_type=SnapshotType.MANUAL, total_value=Decimal('110000')),
            PortfolioSnapshot(snapshot_id='snap3', snapshot_date=date.today() - timedelta(days=3), snapshot_type=SnapshotType.AUTO, total_value=Decimal('120000')),
            PortfolioSnapshot(snapshot_id='snap4', snapshot_date=date.today() - timedelta(days=4), snapshot_type=SnapshotType.MANUAL, total_value=Decimal('130000'))
        ]
        for snapshot in snapshots:
            snapshot_repo.save(snapshot)
        
        # 创建配置
        config = AIAnalysisConfig(
            config_id='config1',
            config_name='test-config',
            ai_type=AIType.LOCAL
        )
        config_repo.save(config)
        
        # 创建多个分析结果
        results = [
            AIAnalysisResult(
                analysis_id=f'analysis-{i}',
                snapshot1_id='snap1',
                snapshot2_id='snap2',
                config_id='config1',
                analysis_status='SUCCESS'
            ) for i in range(3)
        ]

        # 添加其他快照的结果
        results.append(
            AIAnalysisResult(
                analysis_id='analysis-other',
                snapshot1_id='snap3',
                snapshot2_id='snap4',
                config_id='config1',
                analysis_status='SUCCESS'
            )
        )
        
        # 保存结果
        for result in results:
            ai_analysis_repo.save(result)
        
        # 获取特定快照的分析结果
        snap_results = ai_analysis_repo.get_by_snapshots('snap1', 'snap2')
        assert len(snap_results) == 3
        assert all(r.snapshot1_id == 'snap1' and r.snapshot2_id == 'snap2' for r in snap_results)
    
    def test_get_recent_results(self, ai_analysis_repo):
        """测试获取最近的分析结果"""
        # 首先创建依赖的快照和配置
        snapshot_repo = SnapshotRepository(ai_analysis_repo.db)
        config_repo = AIConfigRepository(ai_analysis_repo.db)
        
        # 创建快照
        snapshot1 = PortfolioSnapshot(snapshot_id='snap1', snapshot_date=date.today() - timedelta(days=1), snapshot_type=SnapshotType.AUTO, total_value=Decimal('100000'))
        snapshot2 = PortfolioSnapshot(snapshot_id='snap2', snapshot_date=date.today() - timedelta(days=2), snapshot_type=SnapshotType.MANUAL, total_value=Decimal('110000'))
        snapshot_repo.save(snapshot1)
        snapshot_repo.save(snapshot2)
        
        # 创建配置
        config = AIAnalysisConfig(
            config_id='config1',
            config_name='test-config',
            ai_type=AIType.LOCAL
        )
        config_repo.save(config)
        
        # 创建多个分析结果
        results = [
            AIAnalysisResult(
                analysis_id=f'recent-{i}',
                snapshot1_id='snap1',
                snapshot2_id='snap2',
                config_id='config1'
            ) for i in range(5)
        ]
        
        # 保存结果
        for result in results:
            ai_analysis_repo.save(result)
        
        # 获取最近的结果
        recent = ai_analysis_repo.get_recent_results(limit=3)
        assert len(recent) == 3
    
    def test_delete_result(self, ai_analysis_repo, sample_ai_result):
        """测试删除AI分析结果"""
        # 首先创建依赖的快照和配置
        snapshot_repo = SnapshotRepository(ai_analysis_repo.db)
        config_repo = AIConfigRepository(ai_analysis_repo.db)
        
        # 创建快照
        snapshot1 = PortfolioSnapshot(
            snapshot_id='snap1',
            snapshot_date=date.today() - timedelta(days=1),
            snapshot_type=SnapshotType.AUTO,
            total_value=Decimal('100000')
        )
        snapshot2 = PortfolioSnapshot(
            snapshot_id='snap2',
            snapshot_date=date.today() - timedelta(days=2),
            snapshot_type=SnapshotType.MANUAL,
            total_value=Decimal('110000')
        )
        snapshot_repo.save(snapshot1)
        snapshot_repo.save(snapshot2)
        
        # 创建配置
        config = AIAnalysisConfig(
            config_id='config1',
            config_name='test-config',
            ai_type=AIType.LOCAL
        )
        config_repo.save(config)
        
        # 保存结果
        ai_analysis_repo.save(sample_ai_result)
        
        # 确认结果存在
        assert ai_analysis_repo.get_by_id(sample_ai_result.analysis_id) is not None
        
        # 删除结果
        assert ai_analysis_repo.delete(sample_ai_result.analysis_id) is True
        
        # 确认结果已删除
        assert ai_analysis_repo.get_by_id(sample_ai_result.analysis_id) is None 