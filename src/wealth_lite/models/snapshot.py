"""
WealthLite 投资组合快照模型

包含扩展的快照功能和AI分析功能相关的数据模型：
- PortfolioSnapshot: 扩展的投资组合快照类
- AIAnalysisConfig: AI分析配置类
- AIAnalysisResult: AI分析结果类
"""

import uuid
import time
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .enums import Currency, SnapshotType, AIType


@dataclass
class PortfolioSnapshot:
    """
    投资组合快照（扩展版本）
    
    职责：
    - 记录特定时间点投资组合的完整状态
    - 支持自动快照和手动快照两种类型
    - 提供丰富的业绩指标和分析数据
    - 支持快照对比和AI分析
    """
    
    # 基础信息
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    snapshot_date: date = field(default_factory=date.today)
    snapshot_time: datetime = field(default_factory=datetime.now)
    snapshot_type: SnapshotType = SnapshotType.MANUAL
    base_currency: Currency = Currency.CNY
    
    # 组合概览
    total_value: Decimal = Decimal('0')
    total_cost: Decimal = Decimal('0')
    total_return: Decimal = Decimal('0')
    total_return_rate: Decimal = Decimal('0')
    
    # 分类统计
    cash_value: Decimal = Decimal('0')
    fixed_income_value: Decimal = Decimal('0')
    equity_value: Decimal = Decimal('0')
    real_estate_value: Decimal = Decimal('0')
    commodity_value: Decimal = Decimal('0')
    
    # 业绩指标
    annualized_return: Decimal = Decimal('0')
    volatility: Decimal = Decimal('0')
    sharpe_ratio: Decimal = Decimal('0')
    max_drawdown: Decimal = Decimal('0')
    
    # 详细数据
    position_snapshots: List[Dict[str, Any]] = field(default_factory=list)
    asset_allocation: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    created_date: datetime = field(default_factory=datetime.now)
    notes: str = ""
    
    @property
    def is_today(self) -> bool:
        """判断是否为今天的快照"""
        return self.snapshot_date == date.today()
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        type_name = "自动" if self.snapshot_type == SnapshotType.AUTO else "手动"
        return f"{self.snapshot_date.strftime('%Y-%m-%d')} {type_name}快照"
    
    @property
    def position_count(self) -> int:
        """快照中的持仓数量"""
        return len(self.position_snapshots)
    
    @property
    def display_return(self) -> str:
        """格式化的收益显示"""
        return f"{self.base_currency.symbol}{self.total_return:,.2f} ({self.total_return_rate:.2f}%)"
    
    @classmethod
    def from_portfolio(cls, portfolio, snapshot_type: SnapshotType = SnapshotType.MANUAL, notes: str = "") -> 'PortfolioSnapshot':
        """从Portfolio创建快照"""
        # 计算分类统计
        type_values = cls._calculate_asset_type_values(portfolio.positions)
        # 计算业绩指标
        performance_metrics = cls._calculate_performance_metrics(portfolio)
        # 资产配置只保留金额映射
        raw_allocation = portfolio.calculate_asset_allocation()
        allocation_amounts = {k: float(v["value"]) for k, v in raw_allocation.items()}
        # 创建快照
        snapshot = cls(
            snapshot_type=snapshot_type,
            base_currency=portfolio.base_currency,
            total_value=portfolio.total_value,
            total_cost=portfolio.total_cost,
            total_return=portfolio.calculate_total_return(),
            total_return_rate=Decimal(str(portfolio.calculate_total_return_rate())),
            cash_value=type_values.get('CASH', Decimal('0')),
            fixed_income_value=type_values.get('FIXED_INCOME', Decimal('0')),
            equity_value=type_values.get('EQUITY', Decimal('0')),
            real_estate_value=type_values.get('REAL_ESTATE', Decimal('0')),
            commodity_value=type_values.get('COMMODITY', Decimal('0')),
            annualized_return=performance_metrics.get('annualized_return', Decimal('0')),
            volatility=performance_metrics.get('volatility', Decimal('0')),
            sharpe_ratio=performance_metrics.get('sharpe_ratio', Decimal('0')),
            max_drawdown=performance_metrics.get('max_drawdown', Decimal('0')),
            position_snapshots=[p.to_dict(include_transactions=False) for p in portfolio.positions],
            asset_allocation=allocation_amounts,
            performance_metrics=performance_metrics,
            notes=notes
        )
        return snapshot
    
    @classmethod
    def _calculate_asset_type_values(cls, positions) -> Dict[str, Decimal]:
        """计算各资产类型的价值"""
        type_values = {}
        
        for position in positions:
            asset_type = position.asset_type
            position_value = position.calculate_current_value()
            
            if asset_type not in type_values:
                type_values[asset_type] = Decimal('0')
            
            type_values[asset_type] += position_value
        
        return type_values
    
    @classmethod
    def _calculate_performance_metrics(cls, portfolio) -> Dict[str, Any]:
        """计算业绩指标"""
        # 这里是简化版本，实际应用中需要更复杂的计算
        return {
            'annualized_return': Decimal('0'),
            'volatility': Decimal('0'),
            'sharpe_ratio': Decimal('0'),
            'max_drawdown': Decimal('0'),
            'total_return': str(portfolio.calculate_total_return()),
            'total_return_rate': portfolio.calculate_total_return_rate(),
            'position_count': len(portfolio.positions),
            'active_position_count': portfolio.active_position_count
        }
    
    def compare_with(self, other_snapshot: 'PortfolioSnapshot') -> Dict[str, Any]:
        """
        与另一个快照比较
        
        Args:
            other_snapshot: 要比较的另一个快照
            
        Returns:
            比较结果字典
        """
        if self.base_currency != other_snapshot.base_currency:
            raise ValueError("无法比较不同基础货币的快照")
        
        # 基础数据对比
        value_change = self.total_value - other_snapshot.total_value
        value_change_rate = value_change / other_snapshot.total_value if other_snapshot.total_value > 0 else 0
        
        # 分类数据对比
        type_changes = {}
        for asset_type in ['cash', 'fixed_income', 'equity', 'real_estate', 'commodity']:
            old_value = getattr(other_snapshot, f'{asset_type}_value')
            new_value = getattr(self, f'{asset_type}_value')
            type_changes[asset_type] = {
                'old_value': old_value,
                'new_value': new_value,
                'change': new_value - old_value,
                'change_rate': (new_value - old_value) / old_value if old_value > 0 else 0
            }
        
        # 业绩指标对比
        performance_changes = {
            'annualized_return': {
                'old': other_snapshot.annualized_return,
                'new': self.annualized_return,
                'change': self.annualized_return - other_snapshot.annualized_return
            },
            'volatility': {
                'old': other_snapshot.volatility,
                'new': self.volatility,
                'change': self.volatility - other_snapshot.volatility
            }
        }
        
        return {
            'period': {
                'start_date': other_snapshot.snapshot_date,
                'end_date': self.snapshot_date,
                'days': (self.snapshot_date - other_snapshot.snapshot_date).days
            },
            'value_change': {
                'absolute': value_change,
                'rate': value_change_rate
            },
            'type_changes': type_changes,
            'performance_changes': performance_changes
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，所有Decimal字段转为float，保证可JSON序列化"""
        return {
            'snapshot_id': self.snapshot_id,
            'snapshot_date': self.snapshot_date.isoformat(),
            'snapshot_time': self.snapshot_time.isoformat(),
            'snapshot_type': self.snapshot_type.value,
            'base_currency': self.base_currency.name,
            'total_value': round(float(self.total_value), 2),
            'total_cost': round(float(self.total_cost), 2),
            'total_return': round(float(self.total_return), 4),
            'total_return_rate': round(float(self.total_return_rate), 4),
            'cash_value': round(float(self.cash_value), 2),
            'fixed_income_value': round(float(self.fixed_income_value), 2),
            'equity_value': round(float(self.equity_value), 2),
            'real_estate_value': round(float(self.real_estate_value), 2),
            'commodity_value': round(float(self.commodity_value), 2),
            'annualized_return': round(float(self.annualized_return), 4),
            'volatility': float(self.volatility),
            'sharpe_ratio': float(self.sharpe_ratio),
            'max_drawdown': float(self.max_drawdown),
            'position_snapshots': self.position_snapshots,
            'asset_allocation': self.asset_allocation,
            'performance_metrics': self.performance_metrics,
            'created_date': self.created_date.isoformat(),
            'notes': self.notes,
            'display_name': self.display_name,
            'position_count': self.position_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PortfolioSnapshot':
        """从字典创建PortfolioSnapshot实例"""
        base_currency = Currency[data.get('base_currency', 'CNY')]
        snapshot_type = SnapshotType[data.get('snapshot_type', 'MANUAL')]
        snapshot_date = date.fromisoformat(data.get('snapshot_date', date.today().isoformat()))
        snapshot_time = datetime.fromisoformat(data.get('snapshot_time', datetime.now().isoformat()))
        created_date = datetime.fromisoformat(data.get('created_date', datetime.now().isoformat()))
        
        return cls(
            snapshot_id=data.get('snapshot_id', str(uuid.uuid4())),
            snapshot_date=snapshot_date,
            snapshot_time=snapshot_time,
            snapshot_type=snapshot_type,
            base_currency=base_currency,
            total_value=Decimal(data.get('total_value', '0')),
            total_cost=Decimal(data.get('total_cost', '0')),
            total_return=Decimal(data.get('total_return', '0')),
            total_return_rate=Decimal(data.get('total_return_rate', '0')),
            cash_value=Decimal(data.get('cash_value', '0')),
            fixed_income_value=Decimal(data.get('fixed_income_value', '0')),
            equity_value=Decimal(data.get('equity_value', '0')),
            real_estate_value=Decimal(data.get('real_estate_value', '0')),
            commodity_value=Decimal(data.get('commodity_value', '0')),
            annualized_return=Decimal(data.get('annualized_return', '0')),
            volatility=Decimal(data.get('volatility', '0')),
            sharpe_ratio=Decimal(data.get('sharpe_ratio', '0')),
            max_drawdown=Decimal(data.get('max_drawdown', '0')),
            position_snapshots=data.get('position_snapshots', []),
            asset_allocation=data.get('asset_allocation', {}),
            performance_metrics=data.get('performance_metrics', {}),
            created_date=created_date,
            notes=data.get('notes', '')
        )
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"PortfolioSnapshot({self.display_name}, {self.display_return})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"PortfolioSnapshot(id={self.snapshot_id[:8]}..., "
                f"date={self.snapshot_date.strftime('%Y-%m-%d')}, "
                f"type={self.snapshot_type.value}, "
                f"value={self.total_value})")
    
    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, PortfolioSnapshot):
            return False
        return self.snapshot_id == other.snapshot_id
    
    def __hash__(self) -> int:
        """哈希值"""
        return hash(self.snapshot_id)


@dataclass
class AIAnalysisConfig:
    """AI分析配置"""
    
    # 基础信息
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config_name: str = ""
    ai_type: AIType = AIType.LOCAL
    is_default: bool = False
    is_active: bool = True
    
    # 本地AI配置
    local_model_path: str = ""
    local_model_name: str = ""
    local_api_port: int = 11434  # Ollama默认端口
    
    # 云端AI配置
    cloud_provider: str = ""
    cloud_api_key: str = ""
    cloud_api_url: str = ""
    cloud_model_name: str = ""
    
    # 通用配置
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout_seconds: int = 30
    
    # 元数据
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        return f"{self.config_name} ({self.ai_type.display_name})"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'config_id': self.config_id,
            'config_name': self.config_name,
            'ai_type': self.ai_type.value,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'local_model_path': self.local_model_path,
            'local_model_name': self.local_model_name,
            'local_api_port': self.local_api_port,
            'cloud_provider': self.cloud_provider,
            'cloud_api_key': self.cloud_api_key,
            'cloud_api_url': self.cloud_api_url,
            'cloud_model_name': self.cloud_model_name,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'timeout_seconds': self.timeout_seconds,
            'created_date': self.created_date.isoformat(),
            'updated_date': self.updated_date.isoformat(),
            'display_name': self.display_name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIAnalysisConfig':
        """从字典创建AIAnalysisConfig实例"""
        ai_type = AIType[data.get('ai_type', 'LOCAL')]
        created_date = datetime.fromisoformat(data.get('created_date', datetime.now().isoformat()))
        updated_date = datetime.fromisoformat(data.get('updated_date', datetime.now().isoformat()))
        
        return cls(
            config_id=data.get('config_id', str(uuid.uuid4())),
            config_name=data.get('config_name', ''),
            ai_type=ai_type,
            is_default=data.get('is_default', False),
            is_active=data.get('is_active', True),
            local_model_path=data.get('local_model_path', ''),
            local_model_name=data.get('local_model_name', ''),
            local_api_port=data.get('local_api_port', 11434),
            cloud_provider=data.get('cloud_provider', ''),
            cloud_api_key=data.get('cloud_api_key', ''),
            cloud_api_url=data.get('cloud_api_url', ''),
            cloud_model_name=data.get('cloud_model_name', ''),
            max_tokens=data.get('max_tokens', 4000),
            temperature=data.get('temperature', 0.7),
            timeout_seconds=data.get('timeout_seconds', 30),
            created_date=created_date,
            updated_date=updated_date
        )


@dataclass
class AIAnalysisResult:
    """AI分析结果"""
    
    # 基础信息
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    snapshot1_id: str = ""
    snapshot2_id: str = ""
    config_id: str = ""
    
    # 分析结果
    analysis_content: str = ""
    analysis_summary: str = ""
    investment_advice: str = ""
    risk_assessment: str = ""
    
    # 分析元数据
    analysis_type: str = "COMPARISON"
    analysis_status: str = "PENDING"
    error_message: str = ""
    processing_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 时间戳
    created_date: datetime = field(default_factory=datetime.now)
    
    @property
    def is_success(self) -> bool:
        """判断分析是否成功"""
        return self.analysis_status == "SUCCESS"
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        return f"AI分析 - {self.created_date.strftime('%Y-%m-%d %H:%M')}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'analysis_id': self.analysis_id,
            'snapshot1_id': self.snapshot1_id,
            'snapshot2_id': self.snapshot2_id,
            'config_id': self.config_id,
            'analysis_content': self.analysis_content,
            'analysis_summary': self.analysis_summary,
            'investment_advice': self.investment_advice,
            'risk_assessment': self.risk_assessment,
            'analysis_type': self.analysis_type,
            'analysis_status': self.analysis_status,
            'error_message': self.error_message,
            'processing_time_ms': self.processing_time_ms,
            'metadata': self.metadata,
            'created_date': self.created_date.isoformat(),
            'is_success': self.is_success,
            'display_name': self.display_name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIAnalysisResult':
        """从字典创建AIAnalysisResult实例"""
        created_date = datetime.fromisoformat(data.get('created_date', datetime.now().isoformat()))
        
        return cls(
            analysis_id=data.get('analysis_id', str(uuid.uuid4())),
            snapshot1_id=data.get('snapshot1_id', ''),
            snapshot2_id=data.get('snapshot2_id', ''),
            config_id=data.get('config_id', ''),
            analysis_content=data.get('analysis_content', ''),
            analysis_summary=data.get('analysis_summary', ''),
            investment_advice=data.get('investment_advice', ''),
            risk_assessment=data.get('risk_assessment', ''),
            analysis_type=data.get('analysis_type', 'COMPARISON'),
            analysis_status=data.get('analysis_status', 'PENDING'),
            error_message=data.get('error_message', ''),
            processing_time_ms=data.get('processing_time_ms', 0),
            metadata=data.get('metadata', {}),
            created_date=created_date
        ) 