"""
WealthLite 投资组合模型

包含Portfolio（当前投资组合）和PortfolioSnapshot（组合快照）两个类：
- Portfolio: 基于所有交易记录实时计算的投资组合状态
- PortfolioSnapshot: 记录特定时间点的不可变历史状态
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .position import Position
from .enums import Currency


@dataclass
class Portfolio:
    """
    当前投资组合类（实时计算）
    
    职责：
    - 提供当前投资组合的实时状态
    - 基于所有Position实时计算各项指标
    - 会受到新增交易（包括回溯交易）影响
    - 不需要持久化存储，每次使用时重新计算
    """
    
    positions: List[Position] = field(default_factory=list)
    base_currency: Currency = Currency.CNY
    calculation_date: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """初始化后处理"""
        # 按资产名称排序
        self.positions.sort(key=lambda p: p.asset_name)

    @property
    def position_count(self) -> int:
        """持仓数量"""
        return len(self.positions)

    @property
    def active_position_count(self) -> int:
        """活跃持仓数量"""
        from .enums import PositionStatus
        return len([p for p in self.positions if p.status == PositionStatus.ACTIVE])

    @property
    def total_value(self) -> Decimal:
        """总价值（基础货币）"""
        return sum(p.calculate_current_value() for p in self.positions)

    @property
    def total_cost(self) -> Decimal:
        """总成本（基础货币）"""
        return sum(p.principal_amount for p in self.positions)

    @property
    def total_invested(self) -> Decimal:
        """总投入（基础货币）"""
        return sum(p.total_invested for p in self.positions)

    @property
    def total_withdrawn(self) -> Decimal:
        """总取出（基础货币）"""
        return sum(p.total_withdrawn for p in self.positions)

    @property
    def total_income(self) -> Decimal:
        """总收入（基础货币）"""
        return sum(p.total_income for p in self.positions)

    @property
    def total_fees(self) -> Decimal:
        """总费用（基础货币）"""
        return sum(p.total_fees for p in self.positions)

    @property
    def net_invested(self) -> Decimal:
        """净投入（基础货币）"""
        return sum(p.net_invested for p in self.positions)

    def calculate_total_return(self) -> Decimal:
        """计算总收益（基础货币）"""
        return self.total_value - self.total_cost

    def calculate_total_return_rate(self) -> float:
        """计算总收益率（百分比）"""
        if self.total_cost <= 0:
            return 0.0
        
        total_return = self.calculate_total_return()
        return float(total_return / self.total_cost * 100)

    def calculate_asset_allocation(self) -> Dict[str, Dict[str, Any]]:
        """
        计算资产配置
        
        Returns:
            按资产类型分组的配置信息
        """
        allocation = {}
        
        for position in self.positions:
            asset_type = position.asset_type
            position_value = position.calculate_current_value()
            
            if asset_type not in allocation:
                allocation[asset_type] = {
                    'value': Decimal('0'),
                    'percentage': 0.0,
                    'count': 0,
                    'positions': []
                }
            
            allocation[asset_type]['value'] += position_value
            allocation[asset_type]['count'] += 1
            allocation[asset_type]['positions'].append({
                'asset_name': position.asset_name,
                'value': position_value,
                'percentage': 0.0  # 将在下面计算
            })
        
        # 计算百分比
        total_value = self.total_value
        if total_value > 0:
            for asset_type, info in allocation.items():
                info['percentage'] = float(info['value'] / total_value * 100)
                
                # 计算每个持仓在该资产类型中的占比
                type_value = info['value']
                if type_value > 0:
                    for pos in info['positions']:
                        pos['percentage'] = float(pos['value'] / type_value * 100)
        
        return allocation

    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """
        计算业绩指标
        
        Returns:
            包含各种业绩指标的字典
        """
        metrics = {
            'total_return': str(self.calculate_total_return()),
            'total_return_rate': self.calculate_total_return_rate(),
            'position_count': self.position_count,
            'active_position_count': self.active_position_count,
            'best_performer': None,
            'worst_performer': None,
            'average_return_rate': 0.0,
            'risk_metrics': self._calculate_risk_metrics()
        }
        
        # 找出最佳和最差表现者
        if self.positions:
            sorted_by_return = sorted(
                self.positions,
                key=lambda p: p.calculate_total_return_rate(),
                reverse=True
            )
            
            if sorted_by_return:
                best = sorted_by_return[0]
                worst = sorted_by_return[-1]
                
                metrics['best_performer'] = {
                    'asset_name': best.asset_name,
                    'return_rate': best.calculate_total_return_rate()
                }
                
                metrics['worst_performer'] = {
                    'asset_name': worst.asset_name,
                    'return_rate': worst.calculate_total_return_rate()
                }
            
            # 计算平均收益率
            return_rates = [p.calculate_total_return_rate() for p in self.positions]
            if return_rates:
                metrics['average_return_rate'] = sum(return_rates) / len(return_rates)
        
        return metrics

    def _calculate_risk_metrics(self) -> Dict[str, Any]:
        """计算风险指标"""
        risk_metrics = {
            'average_risk_score': 0.0,
            'risk_distribution': {},
            'concentration_risk': 0.0
        }
        
        if not self.positions:
            return risk_metrics
        
        # 平均风险评分
        risk_scores = [p.asset.risk_score for p in self.positions]
        risk_metrics['average_risk_score'] = sum(risk_scores) / len(risk_scores)
        
        # 风险分布
        from .enums import RiskLevel
        for risk_level in RiskLevel:
            count = len([p for p in self.positions if p.asset.risk_level == risk_level])
            if count > 0:
                risk_metrics['risk_distribution'][risk_level.display_name] = count
        
        # 集中度风险（最大持仓占比）
        if self.total_value > 0:
            max_position_value = max(p.calculate_current_value() for p in self.positions)
            risk_metrics['concentration_risk'] = float(max_position_value / self.total_value * 100)
        
        return risk_metrics

    def get_positions_by_asset_type(self, asset_type: str) -> List[Position]:
        """获取指定资产类型的持仓"""
        return [p for p in self.positions if p.asset_type == asset_type]

    def get_position_by_asset_id(self, asset_id: str) -> Optional[Position]:
        """根据资产ID获取持仓"""
        for position in self.positions:
            if position.asset.asset_id == asset_id:
                return position
        return None

    def add_position(self, position: Position) -> None:
        """添加持仓"""
        # 检查是否已存在相同资产的持仓
        existing = self.get_position_by_asset_id(position.asset.asset_id)
        if existing:
            raise ValueError(f"资产 {position.asset_name} 的持仓已存在")
        
        self.positions.append(position)
        # 重新排序
        self.positions.sort(key=lambda p: p.asset_name)

    def remove_position(self, asset_id: str) -> bool:
        """删除持仓"""
        for i, position in enumerate(self.positions):
            if position.asset.asset_id == asset_id:
                del self.positions[i]
                return True
        return False

    def create_snapshot(self, description: str = "") -> 'PortfolioSnapshot':
        """创建投资组合快照"""
        return PortfolioSnapshot.from_portfolio(self, description)

    def to_dict(self, include_positions: bool = True) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            'base_currency': self.base_currency.name,
            'calculation_date': self.calculation_date.isoformat(),
            'position_count': self.position_count,
            'active_position_count': self.active_position_count,
            'total_value': round(float(self.total_value), 2),
            'total_cost': round(float(self.total_cost), 2),
            'total_invested': round(float(self.total_invested), 2),
            'total_withdrawn': round(float(self.total_withdrawn), 2),
            'total_income': round(float(self.total_income), 2),
            'total_fees': round(float(self.total_fees), 2),
            'net_invested': round(float(self.net_invested), 2),
            'total_return': round(float(self.calculate_total_return()), 4),
            'total_return_rate': round(self.calculate_total_return_rate(), 4),
            'asset_allocation': self.calculate_asset_allocation(),
            'performance_metrics': self.calculate_performance_metrics()
        }
        if include_positions:
            result['positions'] = [p.to_dict(include_transactions=False) for p in self.positions]
        return result

    def __str__(self) -> str:
        """字符串表示"""
        return f"Portfolio({self.position_count} positions, {self.base_currency.symbol}{self.total_value:,.2f})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"Portfolio(positions={self.position_count}, "
                f"total_value={self.total_value}, currency={self.base_currency.name})")


@dataclass
class PortfolioSnapshot:
    """
    投资组合快照类（不可变历史状态）
    
    职责：
    - 记录特定时间点投资组合的不可变历史状态
    - 一旦创建，不受后续任何交易影响
    - 用于历史对比、业绩评估、合规记录
    """
    
    # 基础信息
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    snapshot_date: datetime = field(default_factory=datetime.now)
    base_currency: Currency = Currency.CNY
    description: str = ""
    
    # 快照时的不可变数据
    total_value: Decimal = Decimal('0')
    total_cost: Decimal = Decimal('0')
    total_return: Decimal = Decimal('0')
    return_rate: float = 0.0
    
    # JSON格式存储的复杂数据
    asset_allocation: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    position_snapshots: List[Dict[str, Any]] = field(default_factory=list)
    
    # 元数据
    created_date: datetime = field(default_factory=datetime.now)
    is_immutable: bool = True

    @classmethod
    def from_portfolio(cls, portfolio: Portfolio, description: str = "") -> 'PortfolioSnapshot':
        """从Portfolio创建快照;"""
        return cls(
            snapshot_date=datetime.now(),
            base_currency=portfolio.base_currency,
            description=description,
            total_value=portfolio.total_value,
            total_cost=portfolio.total_cost,
            total_return=portfolio.calculate_total_return(),
            return_rate=portfolio.calculate_total_return_rate(),
            asset_allocation=portfolio.calculate_asset_allocation(),
            performance_metrics=portfolio.calculate_performance_metrics(),
            position_snapshots=[p.to_dict(include_transactions=False) for p in portfolio.positions]
        )

    @property
    def position_count(self) -> int:
        """快照中的持仓数量"""
        return len(self.position_snapshots)

    @property
    def display_return(self) -> str:
        """格式化的收益显示"""
        return f"{self.base_currency.symbol}{self.total_return:,.2f} ({self.return_rate:.2f}%)"

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
        
        comparison = {
            'time_span_days': (self.snapshot_date - other_snapshot.snapshot_date).days,
            'value_change': self.total_value - other_snapshot.total_value,
            'value_change_rate': 0.0,
            'return_change': self.total_return - other_snapshot.total_return,
            'return_rate_change': self.return_rate - other_snapshot.return_rate,
            'position_count_change': self.position_count - other_snapshot.position_count
        }
        
        # 计算价值变化率
        if other_snapshot.total_value > 0:
            comparison['value_change_rate'] = float(
                comparison['value_change'] / other_snapshot.total_value * 100
            )
        
        return comparison

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'snapshot_id': self.snapshot_id,
            'snapshot_date': self.snapshot_date.isoformat(),
            'base_currency': self.base_currency.name,
            'description': self.description,
            'total_value': round(float(self.total_value), 2),
            'total_cost': round(float(self.total_cost), 2),
            'total_return': round(float(self.total_return), 4),
            'return_rate': round(self.return_rate, 4),
            'asset_allocation': self.asset_allocation,
            'performance_metrics': self.performance_metrics,
            'position_snapshots': self.position_snapshots,
            'created_date': self.created_date.isoformat(),
            'is_immutable': self.is_immutable,
            'position_count': self.position_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PortfolioSnapshot':
        """从字典创建PortfolioSnapshot实例"""
        base_currency = Currency[data.get('base_currency', 'CNY')]
        snapshot_date = datetime.fromisoformat(data.get('snapshot_date', datetime.now().isoformat()))
        created_date = datetime.fromisoformat(data.get('created_date', datetime.now().isoformat()))
        
        return cls(
            snapshot_id=data.get('snapshot_id', str(uuid.uuid4())),
            snapshot_date=snapshot_date,
            base_currency=base_currency,
            description=data.get('description', ''),
            total_value=Decimal(data.get('total_value', '0')),
            total_cost=Decimal(data.get('total_cost', '0')),
            total_return=Decimal(data.get('total_return', '0')),
            return_rate=float(data.get('return_rate', 0.0)),
            asset_allocation=data.get('asset_allocation', {}),
            performance_metrics=data.get('performance_metrics', {}),
            position_snapshots=data.get('position_snapshots', []),
            created_date=created_date,
            is_immutable=data.get('is_immutable', True)
        )

    def __str__(self) -> str:
        """字符串表示"""
        return f"PortfolioSnapshot({self.snapshot_date.strftime('%Y-%m-%d')}, {self.display_return})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"PortfolioSnapshot(id={self.snapshot_id[:8]}..., "
                f"date={self.snapshot_date.strftime('%Y-%m-%d')}, "
                f"value={self.total_value})")

    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, PortfolioSnapshot):
            return False
        return self.snapshot_id == other.snapshot_id

    def __hash__(self) -> int:
        """哈希值"""
        return hash(self.snapshot_id) 