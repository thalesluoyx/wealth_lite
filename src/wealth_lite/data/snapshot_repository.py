"""
WealthLite 快照数据访问层

提供快照相关的数据访问操作：
- SnapshotRepository: 投资组合快照数据访问
- AIConfigRepository: AI分析配置数据访问
- AIAnalysisRepository: AI分析结果数据访问
"""

import json
import logging
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal

from .database import DatabaseManager
from ..models.snapshot import PortfolioSnapshot, AIAnalysisConfig, AIAnalysisResult
from ..models.enums import SnapshotType, AIType, Currency


class SnapshotRepository:
    """投资组合快照数据访问层"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def save(self, snapshot: PortfolioSnapshot) -> bool:
        """保存快照"""
        try:
            query = """
                INSERT OR REPLACE INTO portfolio_snapshots (
                    snapshot_id, snapshot_date, snapshot_time, snapshot_type, base_currency,
                    total_value, total_cost, total_return, total_return_rate,
                    cash_value, fixed_income_value, equity_value, real_estate_value, commodity_value,
                    annualized_return, volatility, sharpe_ratio, max_drawdown,
                    position_snapshots, asset_allocation, performance_metrics,
                    created_date, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                snapshot.snapshot_id,
                snapshot.snapshot_date.isoformat(),
                snapshot.snapshot_time.isoformat(),
                snapshot.snapshot_type.value,
                snapshot.base_currency.name,
                round(float(snapshot.total_value), 2),
                round(float(snapshot.total_cost), 2),
                round(float(snapshot.total_return), 4),
                round(float(snapshot.total_return_rate), 4),
                round(float(snapshot.cash_value), 2),
                round(float(snapshot.fixed_income_value), 2),
                round(float(snapshot.equity_value), 2),
                round(float(snapshot.real_estate_value), 2),
                round(float(snapshot.commodity_value), 2),
                round(float(snapshot.annualized_return), 4),
                float(snapshot.volatility),
                float(snapshot.sharpe_ratio),
                float(snapshot.max_drawdown),
                json.dumps(snapshot.position_snapshots, default=float),
                json.dumps(snapshot.asset_allocation, default=float),
                json.dumps(snapshot.performance_metrics, default=float),
                snapshot.created_date.isoformat(),
                snapshot.notes
            )
            
            self.db.execute_update(query, params)
            self.logger.info(f"快照保存成功: {snapshot.snapshot_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"快照保存失败: {e}")
            return False
    
    def get_by_id(self, snapshot_id: str) -> Optional[PortfolioSnapshot]:
        """根据ID获取快照"""
        try:
            query = "SELECT * FROM portfolio_snapshots WHERE snapshot_id = ?"
            rows = self.db.execute_query(query, (snapshot_id,))
            
            if rows:
                return self._row_to_snapshot(rows[0])
            return None
            
        except Exception as e:
            self.logger.error(f"获取快照失败: {e}")
            return None
    
    def get_by_date_and_type(self, snapshot_date: date, snapshot_type: SnapshotType) -> Optional[PortfolioSnapshot]:
        """根据日期和类型获取快照"""
        try:
            query = "SELECT * FROM portfolio_snapshots WHERE snapshot_date = ? AND snapshot_type = ?"
            rows = self.db.execute_query(query, (snapshot_date.isoformat(), snapshot_type.value))
            
            if rows:
                return self._row_to_snapshot(rows[0])
            return None
            
        except Exception as e:
            self.logger.error(f"获取快照失败: {e}")
            return None
    
    def get_by_type(self, snapshot_type: SnapshotType, limit: int = 30, offset: int = 0) -> List[PortfolioSnapshot]:
        """按类型获取快照列表"""
        try:
            query = """
                SELECT * FROM portfolio_snapshots 
                WHERE snapshot_type = ? 
                ORDER BY snapshot_date DESC, snapshot_time DESC 
                LIMIT ? OFFSET ?
            """
            rows = self.db.execute_query(query, (snapshot_type.value, limit, offset))
            
            return [self._row_to_snapshot(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"获取快照列表失败: {e}")
            return []
    
    def get_by_date_range(self, start_date: date, end_date: date) -> List[PortfolioSnapshot]:
        """按日期范围获取快照"""
        try:
            query = """
                SELECT * FROM portfolio_snapshots 
                WHERE snapshot_date >= ? AND snapshot_date <= ?
                ORDER BY snapshot_date DESC, snapshot_time DESC
            """
            rows = self.db.execute_query(query, (start_date.isoformat(), end_date.isoformat()))
            
            return [self._row_to_snapshot(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"获取快照列表失败: {e}")
            return []
    
    def get_recent_snapshots(self, days: int = 30) -> Dict[str, List[PortfolioSnapshot]]:
        """获取最近的快照（按类型分组）"""
        try:
            from datetime import timedelta
            start_date = date.today() - timedelta(days=days)
            snapshots = self.get_by_date_range(start_date, date.today())
            
            result = {'auto': [], 'manual': []}
            for snapshot in snapshots:
                if snapshot.snapshot_type == SnapshotType.AUTO:
                    result['auto'].append(snapshot)
                else:
                    result['manual'].append(snapshot)
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取最近快照失败: {e}")
            return {'auto': [], 'manual': []}
    
    def delete(self, snapshot_id: str) -> bool:
        """删除快照"""
        try:
            query = "DELETE FROM portfolio_snapshots WHERE snapshot_id = ?"
            affected_rows = self.db.execute_update(query, (snapshot_id,))
            
            if affected_rows > 0:
                self.logger.info(f"快照删除成功: {snapshot_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"删除快照失败: {e}")
            return False
    
    def count_by_type(self, snapshot_type: SnapshotType) -> int:
        """统计指定类型的快照数量"""
        try:
            query = "SELECT COUNT(*) FROM portfolio_snapshots WHERE snapshot_type = ?"
            rows = self.db.execute_query(query, (snapshot_type.value,))
            
            if rows:
                return rows[0][0]
            return 0
            
        except Exception as e:
            self.logger.error(f"统计快照数量失败: {e}")
            return 0
    
    def _row_to_snapshot(self, row) -> PortfolioSnapshot:
        """将数据库行转换为PortfolioSnapshot对象"""
        return PortfolioSnapshot(
            snapshot_id=row['snapshot_id'],
            snapshot_date=date.fromisoformat(row['snapshot_date']),
            snapshot_time=datetime.fromisoformat(row['snapshot_time']),
            snapshot_type=SnapshotType[row['snapshot_type']],
            base_currency=Currency[row['base_currency']],
            total_value=Decimal(str(row['total_value'])),
            total_cost=Decimal(str(row['total_cost'])),
            total_return=Decimal(str(row['total_return'])),
            total_return_rate=Decimal(str(row['total_return_rate'])),
            cash_value=Decimal(str(row['cash_value'] or 0)),
            fixed_income_value=Decimal(str(row['fixed_income_value'] or 0)),
            equity_value=Decimal(str(row['equity_value'] or 0)),
            real_estate_value=Decimal(str(row['real_estate_value'] or 0)),
            commodity_value=Decimal(str(row['commodity_value'] or 0)),
            annualized_return=Decimal(str(row['annualized_return'] or 0)),
            volatility=Decimal(str(row['volatility'] or 0)),
            sharpe_ratio=Decimal(str(row['sharpe_ratio'] or 0)),
            max_drawdown=Decimal(str(row['max_drawdown'] or 0)),
            position_snapshots=json.loads(row['position_snapshots']) if row['position_snapshots'] else [],
            asset_allocation=json.loads(row['asset_allocation']) if row['asset_allocation'] else {},
            performance_metrics=json.loads(row['performance_metrics']) if row['performance_metrics'] else {},
            created_date=datetime.fromisoformat(row['created_date']),
            notes=row['notes'] or ''
        )


class AIConfigRepository:
    """AI分析配置数据访问层"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def save(self, config: AIAnalysisConfig) -> bool:
        """保存AI配置"""
        try:
            query = """
                INSERT OR REPLACE INTO ai_analysis_configs (
                    config_id, config_name, ai_type, is_default, is_active,
                    local_model_path, local_model_name, local_api_port,
                    cloud_provider, cloud_api_key, cloud_api_url, cloud_model_name,
                    max_tokens, temperature, timeout_seconds,
                    created_date, updated_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                config.config_id,
                config.config_name,
                config.ai_type.value,
                config.is_default,
                config.is_active,
                config.local_model_path,
                config.local_model_name,
                config.local_api_port,
                config.cloud_provider,
                config.cloud_api_key,
                config.cloud_api_url,
                config.cloud_model_name,
                config.max_tokens,
                config.temperature,
                config.timeout_seconds,
                config.created_date.isoformat(),
                config.updated_date.isoformat()
            )
            
            self.db.execute_update(query, params)
            self.logger.info(f"AI配置保存成功: {config.config_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"AI配置保存失败: {e}")
            return False
    
    def get_by_id(self, config_id: str) -> Optional[AIAnalysisConfig]:
        """根据ID获取AI配置"""
        try:
            query = "SELECT * FROM ai_analysis_configs WHERE config_id = ?"
            rows = self.db.execute_query(query, (config_id,))
            
            if rows:
                return self._row_to_config(rows[0])
            return None
            
        except Exception as e:
            self.logger.error(f"获取AI配置失败: {e}")
            return None
    
    def get_default_config(self) -> Optional[AIAnalysisConfig]:
        """获取默认AI配置"""
        try:
            query = "SELECT * FROM ai_analysis_configs WHERE is_default = 1 AND is_active = 1"
            rows = self.db.execute_query(query)
            
            if rows:
                return self._row_to_config(rows[0])
            return None
            
        except Exception as e:
            self.logger.error(f"获取默认AI配置失败: {e}")
            return None
    
    def get_by_type(self, ai_type: AIType) -> List[AIAnalysisConfig]:
        """根据AI类型获取配置列表"""
        try:
            query = "SELECT * FROM ai_analysis_configs WHERE ai_type = ? AND is_active = 1 ORDER BY created_date DESC"
            rows = self.db.execute_query(query, (ai_type.value,))
            
            return [self._row_to_config(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"获取AI配置列表失败: {e}")
            return []
    
    def get_all_active(self) -> List[AIAnalysisConfig]:
        """获取所有活跃的AI配置"""
        try:
            query = "SELECT * FROM ai_analysis_configs WHERE is_active = 1 ORDER BY ai_type, created_date DESC"
            rows = self.db.execute_query(query)
            
            return [self._row_to_config(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"获取AI配置列表失败: {e}")
            return []
    
    def set_default(self, config_id: str) -> bool:
        """设置默认配置"""
        try:
            with self.db.transaction():
                # 清除所有默认配置
                self.db.execute_update("UPDATE ai_analysis_configs SET is_default = 0")
                
                # 设置新的默认配置
                affected_rows = self.db.execute_update(
                    "UPDATE ai_analysis_configs SET is_default = 1 WHERE config_id = ?",
                    (config_id,)
                )
                
                if affected_rows > 0:
                    self.logger.info(f"默认AI配置设置成功: {config_id}")
                    return True
                return False
                
        except Exception as e:
            self.logger.error(f"设置默认AI配置失败: {e}")
            return False
    
    def delete(self, config_id: str) -> bool:
        """删除AI配置"""
        try:
            query = "DELETE FROM ai_analysis_configs WHERE config_id = ?"
            affected_rows = self.db.execute_update(query, (config_id,))
            
            if affected_rows > 0:
                self.logger.info(f"AI配置删除成功: {config_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"删除AI配置失败: {e}")
            return False
    
    def _row_to_config(self, row) -> AIAnalysisConfig:
        """将数据库行转换为AIAnalysisConfig对象"""
        return AIAnalysisConfig(
            config_id=row['config_id'],
            config_name=row['config_name'],
            ai_type=AIType[row['ai_type']],
            is_default=bool(row['is_default']),
            is_active=bool(row['is_active']),
            local_model_path=row['local_model_path'] or '',
            local_model_name=row['local_model_name'] or '',
            local_api_port=row['local_api_port'] or 11434,
            cloud_provider=row['cloud_provider'] or '',
            cloud_api_key=row['cloud_api_key'] or '',
            cloud_api_url=row['cloud_api_url'] or '',
            cloud_model_name=row['cloud_model_name'] or '',
            max_tokens=row['max_tokens'] or 4000,
            temperature=row['temperature'] or 0.7,
            timeout_seconds=row['timeout_seconds'] or 30,
            created_date=datetime.fromisoformat(row['created_date']),
            updated_date=datetime.fromisoformat(row['updated_date'])
        )


class AIAnalysisRepository:
    """AI分析结果数据访问层"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def save(self, result: AIAnalysisResult) -> bool:
        """保存AI分析结果"""
        try:
            query = """
                INSERT OR REPLACE INTO ai_analysis_results (
                    analysis_id, snapshot1_id, snapshot2_id, config_id,
                    analysis_content, analysis_summary, investment_advice, risk_assessment,
                    analysis_type, analysis_status, error_message, processing_time_ms,
                    created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                result.analysis_id,
                result.snapshot1_id,
                result.snapshot2_id,
                result.config_id,
                result.analysis_content,
                result.analysis_summary,
                result.investment_advice,
                result.risk_assessment,
                result.analysis_type,
                result.analysis_status,
                result.error_message,
                result.processing_time_ms,
                result.created_date.isoformat()
            )
            
            self.db.execute_update(query, params)
            self.logger.info(f"AI分析结果保存成功: {result.analysis_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"AI分析结果保存失败: {e}")
            return False
    
    def get_by_id(self, analysis_id: str) -> Optional[AIAnalysisResult]:
        """根据ID获取AI分析结果"""
        try:
            query = "SELECT * FROM ai_analysis_results WHERE analysis_id = ?"
            rows = self.db.execute_query(query, (analysis_id,))
            
            if rows:
                return self._row_to_result(rows[0])
            return None
            
        except Exception as e:
            self.logger.error(f"获取AI分析结果失败: {e}")
            return None
    
    def get_by_snapshots(self, snapshot1_id: str, snapshot2_id: str) -> List[AIAnalysisResult]:
        """根据快照ID获取分析结果"""
        try:
            query = """
                SELECT * FROM ai_analysis_results 
                WHERE snapshot1_id = ? AND snapshot2_id = ?
                ORDER BY created_date DESC
            """
            rows = self.db.execute_query(query, (snapshot1_id, snapshot2_id))
            
            return [self._row_to_result(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"获取AI分析结果失败: {e}")
            return []
    
    def get_recent_results(self, limit: int = 20) -> List[AIAnalysisResult]:
        """获取最近的分析结果"""
        try:
            query = """
                SELECT * FROM ai_analysis_results 
                ORDER BY created_date DESC 
                LIMIT ?
            """
            rows = self.db.execute_query(query, (limit,))
            
            return [self._row_to_result(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"获取最近AI分析结果失败: {e}")
            return []
    
    def delete(self, analysis_id: str) -> bool:
        """删除AI分析结果"""
        try:
            query = "DELETE FROM ai_analysis_results WHERE analysis_id = ?"
            affected_rows = self.db.execute_update(query, (analysis_id,))
            
            if affected_rows > 0:
                self.logger.info(f"AI分析结果删除成功: {analysis_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"删除AI分析结果失败: {e}")
            return False
    
    def _row_to_result(self, row) -> AIAnalysisResult:
        """将数据库行转换为AIAnalysisResult对象"""
        return AIAnalysisResult(
            analysis_id=row['analysis_id'],
            snapshot1_id=row['snapshot1_id'],
            snapshot2_id=row['snapshot2_id'],
            config_id=row['config_id'],
            analysis_content=row['analysis_content'] or '',
            analysis_summary=row['analysis_summary'] or '',
            investment_advice=row['investment_advice'] or '',
            risk_assessment=row['risk_assessment'] or '',
            analysis_type=row['analysis_type'],
            analysis_status=row['analysis_status'],
            error_message=row['error_message'] or '',
            processing_time_ms=row['processing_time_ms'] or 0,
            created_date=datetime.fromisoformat(row['created_date'])
        ) 