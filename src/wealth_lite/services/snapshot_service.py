"""
WealthLite 快照服务层

提供快照相关的业务逻辑：
- SnapshotService: 投资组合快照业务逻辑
- AIConfigService: AI分析配置业务逻辑
- AIAnalysisService: AI分析业务逻辑
"""

import json
import time
import logging
import requests
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any

from ..data.database import DatabaseManager
from ..data.snapshot_repository import SnapshotRepository, AIConfigRepository, AIAnalysisRepository
from ..models.snapshot import PortfolioSnapshot, AIAnalysisConfig, AIAnalysisResult
from ..models.enums import SnapshotType, AIType
from ..services.wealth_service import WealthService


class SnapshotService:
    """投资组合快照服务"""
    
    def __init__(self, db_manager: DatabaseManager, wealth_service: WealthService):
        self.db = db_manager
        self.wealth_service = wealth_service
        self.snapshot_repository = SnapshotRepository(db_manager)
        self.logger = logging.getLogger(__name__)
    
    def create_startup_snapshot(self) -> Optional[PortfolioSnapshot]:
        """服务启动时创建自动快照"""
        try:
            # 1. 检查今天是否已有自动快照
            today = date.today()
            existing_snapshot = self.snapshot_repository.get_by_date_and_type(
                today, SnapshotType.AUTO
            )
            
            # 2. 如果存在，删除旧快照
            if existing_snapshot:
                self.snapshot_repository.delete(existing_snapshot.snapshot_id)
                self.logger.info(f"删除旧的自动快照: {existing_snapshot.snapshot_id}")
            
            # 3. 计算当前投资组合状态
            current_portfolio = self.wealth_service.get_portfolio()
            if not current_portfolio:
                self.logger.warning("无法获取当前投资组合，跳过自动快照创建")
                return None
            
            # 4. 创建新快照
            snapshot = PortfolioSnapshot.from_portfolio(
                current_portfolio, 
                SnapshotType.AUTO,
                "系统启动时自动创建"
            )
            
            # 5. 保存快照
            if self.snapshot_repository.save(snapshot):
                self.logger.info(f"创建自动快照成功: {snapshot.snapshot_id}")
                return snapshot
            else:
                self.logger.error("自动快照保存失败")
                return None
                
        except Exception as e:
            self.logger.error(f"创建自动快照失败: {e}")
            return None
    
    def create_manual_snapshot(self, notes: str = "") -> Optional[PortfolioSnapshot]:
        """用户手动创建快照"""
        try:
            # 1. 检查今天是否已有手动快照
            today = date.today()
            existing_snapshot = self.snapshot_repository.get_by_date_and_type(
                today, SnapshotType.MANUAL
            )
            
            # 2. 如果存在，删除旧快照（前端会处理确认逻辑）
            if existing_snapshot:
                self.snapshot_repository.delete(existing_snapshot.snapshot_id)
                self.logger.info(f"删除旧的手动快照: {existing_snapshot.snapshot_id}")
            
            # 3. 计算当前投资组合状态
            current_portfolio = self.wealth_service.get_portfolio()
            if not current_portfolio:
                self.logger.error("无法获取当前投资组合")
                return None
            
            # 4. 创建新快照
            snapshot = PortfolioSnapshot.from_portfolio(
                current_portfolio, 
                SnapshotType.MANUAL,
                notes
            )
            
            # 5. 保存快照
            if self.snapshot_repository.save(snapshot):
                self.logger.info(f"创建手动快照成功: {snapshot.snapshot_id}")
                return snapshot
            else:
                self.logger.error("手动快照保存失败")
                return None
                
        except Exception as e:
            self.logger.error(f"创建手动快照失败: {e}")
            return None
    
    def get_snapshot_by_id(self, snapshot_id: str) -> Optional[PortfolioSnapshot]:
        """根据ID获取快照"""
        return self.snapshot_repository.get_by_id(snapshot_id)
    
    def get_snapshot_by_date_and_type(self, snapshot_date, snapshot_type):
        """根据日期和类型获取快照"""
        return self.snapshot_repository.get_by_date_and_type(snapshot_date, snapshot_type)
    
    def get_snapshots_by_type(self, snapshot_type: SnapshotType, limit: int = 30, offset: int = 0) -> List[PortfolioSnapshot]:
        """按类型查询快照列表"""
        return self.snapshot_repository.get_by_type(snapshot_type, limit, offset)
    
    def get_recent_snapshots(self, days: int = 30) -> Dict[str, List[PortfolioSnapshot]]:
        """获取最近的快照（按类型分组）"""
        return self.snapshot_repository.get_recent_snapshots(days)
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照"""
        # 检查是否为今天的快照
        snapshot = self.snapshot_repository.get_by_id(snapshot_id)
        if snapshot and snapshot.is_today:
            self.logger.warning(f"不能删除今天的快照: {snapshot_id}")
            return False
        
        return self.snapshot_repository.delete(snapshot_id)
    
    def compare_snapshots(self, snapshot1_id: str, snapshot2_id: str) -> Optional[Dict[str, Any]]:
        """对比两个快照"""
        try:
            snapshot1 = self.snapshot_repository.get_by_id(snapshot1_id)
            snapshot2 = self.snapshot_repository.get_by_id(snapshot2_id)
            
            if not snapshot1 or not snapshot2:
                self.logger.error("快照不存在")
                return None
            
            return snapshot2.compare_with(snapshot1)
            
        except Exception as e:
            self.logger.error(f"快照对比失败: {e}")
            return None
    
    def get_snapshot_statistics(self) -> Dict[str, Any]:
        """获取快照统计信息"""
        try:
            auto_count = self.snapshot_repository.count_by_type(SnapshotType.AUTO)
            manual_count = self.snapshot_repository.count_by_type(SnapshotType.MANUAL)
            
            return {
                'auto_count': auto_count,
                'manual_count': manual_count,
                'total_count': auto_count + manual_count
            }
            
        except Exception as e:
            self.logger.error(f"获取快照统计失败: {e}")
            return {'auto_count': 0, 'manual_count': 0, 'total_count': 0}


class AIConfigService:
    """AI分析配置服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.config_repository = AIConfigRepository(db_manager)
        self.logger = logging.getLogger(__name__)
    
    def get_default_config(self) -> AIAnalysisConfig:
        """获取默认AI配置"""
        config = self.config_repository.get_default_config()
        if not config:
            # 创建默认本地AI配置
            config = AIAnalysisConfig(
                config_name="默认本地AI",
                ai_type=AIType.LOCAL,
                is_default=True,
                local_model_name="llama3.1:8b",
                local_api_port=11434
            )
            self.config_repository.save(config)
            self.logger.info("创建默认AI配置")
        return config
    
    def get_config_by_id(self, config_id: str) -> Optional[AIAnalysisConfig]:
        """根据ID获取AI配置"""
        return self.config_repository.get_by_id(config_id)
    
    def get_all_configs(self) -> List[AIAnalysisConfig]:
        """获取所有活跃的AI配置"""
        return self.config_repository.get_all_active()
    
    def get_configs_by_type(self, ai_type: AIType) -> List[AIAnalysisConfig]:
        """根据AI类型获取配置"""
        return self.config_repository.get_by_type(ai_type)
    
    def switch_ai_type(self, ai_type: AIType) -> Optional[AIAnalysisConfig]:
        """切换AI类型"""
        try:
            configs = self.config_repository.get_by_type(ai_type)
            if not configs:
                self.logger.error(f"未找到{ai_type.display_name}配置")
                return None
            
            # 设置为默认配置
            config = configs[0]
            if self.config_repository.set_default(config.config_id):
                self.logger.info(f"切换到{ai_type.display_name}: {config.config_name}")
                return config
            return None
            
        except Exception as e:
            self.logger.error(f"切换AI类型失败: {e}")
            return None
    
    def save_config(self, config: AIAnalysisConfig) -> bool:
        """保存AI配置"""
        try:
            # 更新时间戳
            config.updated_date = datetime.now()
            return self.config_repository.save(config)
            
        except Exception as e:
            self.logger.error(f"保存AI配置失败: {e}")
            return False
    
    def delete_config(self, config_id: str) -> bool:
        """删除AI配置"""
        try:
            # 检查是否为默认配置
            config = self.config_repository.get_by_id(config_id)
            if config and config.is_default:
                self.logger.warning("不能删除默认配置")
                return False
            
            return self.config_repository.delete(config_id)
            
        except Exception as e:
            self.logger.error(f"删除AI配置失败: {e}")
            return False


class AIAnalysisService:
    """AI分析服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.config_service = AIConfigService(db_manager)
        self.analysis_repository = AIAnalysisRepository(db_manager)
        self.logger = logging.getLogger(__name__)
    
    def analyze_snapshots(self, snapshot1: PortfolioSnapshot, snapshot2: PortfolioSnapshot, 
                         config: Optional[AIAnalysisConfig] = None) -> AIAnalysisResult:
        """AI分析两个快照的对比"""
        
        if not config:
            config = self.config_service.get_default_config()
        
        # 创建分析结果记录
        result = AIAnalysisResult(
            snapshot1_id=snapshot1.snapshot_id,
            snapshot2_id=snapshot2.snapshot_id,
            config_id=config.config_id,
            analysis_type="COMPARISON",
            analysis_status="PENDING"
        )
        
        try:
            start_time = time.time()
            
            # 准备分析数据
            analysis_data = self._prepare_analysis_data(snapshot1, snapshot2)
            
            # 调用AI分析
            if config.ai_type == AIType.LOCAL:
                analysis_content = self._call_local_ai(analysis_data, config)
            else:
                analysis_content = self._call_cloud_ai(analysis_data, config)
            
            # 解析AI响应
            parsed_result = self._parse_ai_response(analysis_content)
            
            # 更新结果
            result.analysis_content = analysis_content
            result.analysis_summary = parsed_result.get('summary', '')
            result.investment_advice = parsed_result.get('advice', '')
            result.risk_assessment = parsed_result.get('risk', '')
            result.analysis_status = "SUCCESS"
            result.processing_time_ms = int((time.time() - start_time) * 1000)
            
        except Exception as e:
            result.analysis_status = "FAILED"
            result.error_message = str(e)
            self.logger.error(f"AI分析失败: {e}")
        
        # 保存结果
        self.analysis_repository.save(result)
        return result
    
    def get_analysis_by_id(self, analysis_id: str) -> Optional[AIAnalysisResult]:
        """根据ID获取AI分析结果"""
        return self.analysis_repository.get_by_id(analysis_id)
    
    def get_analysis_by_snapshots(self, snapshot1_id: str, snapshot2_id: str) -> List[AIAnalysisResult]:
        """根据快照ID获取分析结果"""
        return self.analysis_repository.get_by_snapshots(snapshot1_id, snapshot2_id)
    
    def get_recent_analysis(self, limit: int = 20) -> List[AIAnalysisResult]:
        """获取最近的分析结果"""
        return self.analysis_repository.get_recent_results(limit)
    
    def _prepare_analysis_data(self, snapshot1: PortfolioSnapshot, snapshot2: PortfolioSnapshot) -> Dict[str, Any]:
        """准备分析数据"""
        return {
            'snapshot1': {
                'date': snapshot1.snapshot_date.isoformat(),
                'total_value': float(snapshot1.total_value),
                'total_return': float(snapshot1.total_return),
                'total_return_rate': float(snapshot1.total_return_rate),
                'allocation': {
                    'cash': float(snapshot1.cash_value),
                    'fixed_income': float(snapshot1.fixed_income_value),
                    'equity': float(snapshot1.equity_value),
                    'real_estate': float(snapshot1.real_estate_value),
                    'commodity': float(snapshot1.commodity_value)
                }
            },
            'snapshot2': {
                'date': snapshot2.snapshot_date.isoformat(),
                'total_value': float(snapshot2.total_value),
                'total_return': float(snapshot2.total_return),
                'total_return_rate': float(snapshot2.total_return_rate),
                'allocation': {
                    'cash': float(snapshot2.cash_value),
                    'fixed_income': float(snapshot2.fixed_income_value),
                    'equity': float(snapshot2.equity_value),
                    'real_estate': float(snapshot2.real_estate_value),
                    'commodity': float(snapshot2.commodity_value)
                }
            }
        }
    
    def _call_local_ai(self, data: Dict[str, Any], config: AIAnalysisConfig) -> str:
        """调用本地AI"""
        url = f"http://localhost:{config.local_api_port}/api/generate"
        prompt = self._build_analysis_prompt(data)
        
        payload = {
            "model": config.local_model_name,
            "prompt": prompt,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens
            }
        }
        
        response = requests.post(
            url, 
            json=payload, 
            timeout=config.timeout_seconds
        )
        response.raise_for_status()
        
        return response.json().get('response', '')
    
    def _call_cloud_ai(self, data: Dict[str, Any], config: AIAnalysisConfig) -> str:
        """调用云端AI"""
        # 根据不同的云端提供商实现
        if config.cloud_provider == "OPENAI":
            return self._call_openai(data, config)
        elif config.cloud_provider == "CLAUDE":
            return self._call_claude(data, config)
        else:
            raise ValueError(f"不支持的云端AI提供商: {config.cloud_provider}")
    
    def _call_openai(self, data: Dict[str, Any], config: AIAnalysisConfig) -> str:
        """调用OpenAI API"""
        # 简化实现，实际应用中需要完整的OpenAI API调用
        raise NotImplementedError("OpenAI API集成待实现")
    
    def _call_claude(self, data: Dict[str, Any], config: AIAnalysisConfig) -> str:
        """调用Claude API"""
        # 简化实现，实际应用中需要完整的Claude API调用
        raise NotImplementedError("Claude API集成待实现")
    
    def _build_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """构建分析提示词"""
        return f"""
        作为专业的投资顾问，请分析以下两个投资组合快照的变化：

        快照1 ({data['snapshot1']['date']}):
        - 总价值: ¥{data['snapshot1']['total_value']:,.2f}
        - 总收益: ¥{data['snapshot1']['total_return']:,.2f}
        - 收益率: {data['snapshot1']['total_return_rate']:.2f}%
        - 资产配置: 现金¥{data['snapshot1']['allocation']['cash']:,.2f}, 固收¥{data['snapshot1']['allocation']['fixed_income']:,.2f}, 权益¥{data['snapshot1']['allocation']['equity']:,.2f}

        快照2 ({data['snapshot2']['date']}):
        - 总价值: ¥{data['snapshot2']['total_value']:,.2f}
        - 总收益: ¥{data['snapshot2']['total_return']:,.2f}
        - 收益率: {data['snapshot2']['total_return_rate']:.2f}%
        - 资产配置: 现金¥{data['snapshot2']['allocation']['cash']:,.2f}, 固收¥{data['snapshot2']['allocation']['fixed_income']:,.2f}, 权益¥{data['snapshot2']['allocation']['equity']:,.2f}

        请从以下角度进行分析：
        1. 投资业绩变化分析
        2. 资产配置变化分析
        3. 风险评估
        4. 投资建议

        请用JSON格式返回分析结果：
        {{
            "summary": "整体分析摘要",
            "advice": "投资建议",
            "risk": "风险评估"
        }}
        """
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析AI响应"""
        try:
            # 尝试解析JSON格式的响应
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                return json.loads(json_str)
            
            # 如果不是JSON格式，返回原始文本
            return {
                'summary': response[:500] if len(response) > 500 else response,
                'advice': '请查看完整分析内容',
                'risk': '请查看完整分析内容'
            }
            
        except Exception as e:
            self.logger.warning(f"解析AI响应失败: {e}")
            return {
                'summary': '分析完成，但解析结果时出现问题',
                'advice': '请查看完整分析内容',
                'risk': '请查看完整分析内容'
            } 