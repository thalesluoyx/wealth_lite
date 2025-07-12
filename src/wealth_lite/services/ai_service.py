"""
AI分析服务模块

提供云端AI分析功能，支持多种AI平台：
- OpenRouter (首期支持)
- OpenAI (后续支持)
- 本地Ollama (后续支持)
"""

import json
import logging
import time
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests
from openai import OpenAI
import uuid # Added for conversation_id

from ..models.snapshot import AIAnalysisConfig, AIAnalysisResult, PortfolioSnapshot
from src.wealth_lite.config.env_loader import get_env
from src.wealth_lite.config.prompt_templates import (
    get_system_prompt, get_user_prompt, get_result_template, 
    format_user_prompt, get_available_prompt_types
)


class CloudAIService:
    """云端AI服务基类"""
    
    def __init__(self, config: AIAnalysisConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def analyze(self, data: Dict[str, Any], prompt: str) -> str:
        """执行AI分析 - 子类需要实现"""
        raise NotImplementedError("子类必须实现analyze方法")
    
    def test_connection(self) -> bool:
        """测试连接 - 子类需要实现"""
        raise NotImplementedError("子类必须实现test_connection方法")


class OpenRouterService(CloudAIService):
    """OpenRouter AI服务"""
    
    def __init__(self, config: AIAnalysisConfig):
        super().__init__(config)
        self.base_url = config.cloud_api_url or "https://openrouter.ai/api/v1"
        
        # 优先使用环境变量中的API Key，如果没有则使用配置中的
        self.api_key = get_env("OPENROUTER_API_KEY") or config.cloud_api_key
        
        # 如果API Key为空，记录警告
        if not self.api_key:
            logging.warning("OpenRouter API Key未设置，请在.env.development中配置OPENROUTER_API_KEY")
            
        self.model = config.cloud_model_name or "deepseek/deepseek-chat-v3-0324:free:online"
        
        # 记录初始化信息
        logging.info(f"初始化OpenRouter服务，base_url={self.base_url}, model={self.model}, api_key={self.api_key[:5]}...")
    
    def analyze(self, data: Dict[str, Any], prompt: str, system_prompt_type: str = "default", user_prompt_type: str = "default") -> str:
        """
        使用OpenRouter执行AI分析
        
        Args:
            data: 分析数据
            prompt: 用户提示
            system_prompt_type: 系统提示类型，可选值：default, conservative, aggressive, educational
            user_prompt_type: 用户提示类型，可选值：default, simple, detailed, risk_focused
            
        Returns:
            AI分析结果
        """
        try:
            # 构建完整的分析prompt
            user_prompt = self._build_analysis_prompt(data, prompt, user_prompt_type)
            
            # 获取系统提示
            system_prompt = get_system_prompt(system_prompt_type)
            
            # 准备消息
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": user_prompt
                }
            ]
            
            # 使用requests库直接调用API
            return self._analyze_with_requests(messages)
                
        except Exception as e:
            self.logger.error(f"OpenRouter分析失败: {e}")
            raise
    
    def _analyze_with_requests(self, messages: List[Dict[str, str]]) -> str:
        """使用requests库直接调用OpenRouter API"""
        import requests
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            # "model": self.model,
            # TODO 临时使用deepseek/deepseek-chat-v3-0324:free:online模型，后续需要根据配置使用
            "model": "deepseek/deepseek-chat-v3-0324:free:online",
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        
        # 打印当前使用的prompt
        system_prompt = next((m["content"] for m in messages if m["role"] == "system"), None)
        user_prompt = next((m["content"] for m in messages if m["role"] == "user"), None)
        
        self.logger.info(f"系统提示: {system_prompt[:100]}..." if system_prompt else "无系统提示")
        self.logger.info(f"用户提示: {user_prompt[:100]}..." if user_prompt else "无用户提示")
        self.logger.info(f"使用模型: {self.model}, 温度: {self.config.temperature}, 最大token: {self.config.max_tokens}")
        
        self.logger.info(f"使用requests库发送请求到: {url}")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            self.logger.info(f"使用requests库分析完成，模型: {self.model}")
            self.logger.info(f"分析结果: {content}")
            return content
        else:
            raise Exception("API返回空响应")
    
    def test_connection(self) -> bool:
        """测试OpenRouter连接"""
        try:
            logging.info(f"测试OpenRouter连接，模型: {self.model}")
            
            # 使用requests库
            messages = [{"role": "user", "content": "Hello"}]
            try:
                content = self._analyze_with_requests(messages)
                result = bool(content)
            except Exception as e:
                logging.error(f"连接测试失败: {str(e)}")
                result = False
            
            logging.info(f"OpenRouter连接测试结果: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"OpenRouter连接测试失败: {e}")
            return False
    
    def _build_analysis_prompt(self, data: Dict[str, Any], base_prompt: str, prompt_type: str = "default") -> str:
        """
        构建分析prompt
        
        Args:
            data: 分析数据
            base_prompt: 基础提示
            prompt_type: 提示类型，可选值：default, simple, detailed, risk_focused
            
        Returns:
            格式化后的用户提示
        """
        # 格式化投资组合数据
        data_text = self._format_portfolio_data(data)
        
        # 使用标准化的提示模板
        return format_user_prompt(prompt_type, base_prompt, data_text)
    
    def _format_portfolio_data(self, data: Dict[str, Any]) -> str:
        """格式化投资组合数据为可读文本"""
        if 'snapshot' in data:
            # 单个快照分析
            snapshot = data['snapshot']
            
            # 基本信息
            basic_info = f"""
## 基本信息
快照日期: {snapshot.get('date', 'N/A')}
总资产价值: ¥{snapshot.get('total_value', 0):,.2f}
总投入成本: ¥{snapshot.get('total_cost', 0):,.2f}
总收益: ¥{snapshot.get('total_return', 0):,.2f}
总收益率: {snapshot.get('total_return_rate', 0):.2f}%
"""

            # 资产配置
            cash_value = snapshot.get('allocation', {}).get('cash', 0)
            fixed_income_value = snapshot.get('allocation', {}).get('fixed_income', 0)
            equity_value = snapshot.get('allocation', {}).get('equity', 0)
            real_estate_value = snapshot.get('allocation', {}).get('real_estate', 0)
            commodity_value = snapshot.get('allocation', {}).get('commodity', 0)
            
            total_value = snapshot.get('total_value', 0)
            if total_value > 0:
                cash_percent = cash_value / total_value * 100
                fixed_income_percent = fixed_income_value / total_value * 100
                equity_percent = equity_value / total_value * 100
                real_estate_percent = real_estate_value / total_value * 100
                commodity_percent = commodity_value / total_value * 100
            else:
                cash_percent = fixed_income_percent = equity_percent = real_estate_percent = commodity_percent = 0
            
            allocation_info = f"""
## 资产配置
- 现金及等价物: ¥{cash_value:,.2f} ({cash_percent:.2f}%)
- 固定收益类: ¥{fixed_income_value:,.2f} ({fixed_income_percent:.2f}%)
- 权益类: ¥{equity_value:,.2f} ({equity_percent:.2f}%)
- 房地产: ¥{real_estate_value:,.2f} ({real_estate_percent:.2f}%)
- 大宗商品: ¥{commodity_value:,.2f} ({commodity_percent:.2f}%)
"""

            # 持仓明细
            position_info = ""
            if 'position_snapshots' in snapshot and snapshot['position_snapshots']:
                position_info = "\n## 持仓明细\n"
                for i, pos in enumerate(snapshot['position_snapshots'][:100]):  # 最多显示100个持仓
                    pos_name = pos.get('asset_name', f"资产{i+1}")
                    pos_type = pos.get('asset_type', 'N/A')
                    pos_value = pos.get('current_value', 0)
                    pos_cost = pos.get('cost_basis', 0)
                    pos_return = pos.get('total_return', 0)
                    pos_return_rate = pos.get('total_return_rate', 0)
                    
                    position_info += f"- {pos_name} ({pos_type}): ¥{pos_value:,.2f}, 收益率: {pos_return_rate:.2f}%\n"
                
                if len(snapshot['position_snapshots']) > 100:
                    position_info += f"- ... 以及其他 {len(snapshot['position_snapshots']) - 100} 个持仓\n"
            
            # 业绩指标
            metrics_info = ""
            if 'performance_metrics' in snapshot and snapshot['performance_metrics']:
                metrics = snapshot['performance_metrics']
                metrics_info = f"""
## 业绩指标
- 年化收益率: {metrics.get('annualized_return', 0):.2f}%
- 波动率: {metrics.get('volatility', 0):.2f}%
- 夏普比率: {metrics.get('sharpe_ratio', 0):.2f}
- 最大回撤: {metrics.get('max_drawdown', 0):.2f}%
"""
            
            return basic_info + allocation_info + position_info + metrics_info
            
        elif 'snapshot1' in data and 'snapshot2' in data:
            # 快照对比分析
            s1 = data['snapshot1']
            s2 = data['snapshot2']
            
            # 计算时间间隔
            try:
                from datetime import datetime
                date1 = datetime.fromisoformat(s1.get('date', datetime.now().isoformat()))
                date2 = datetime.fromisoformat(s2.get('date', datetime.now().isoformat()))
                days_diff = abs((date2 - date1).days)
                period_info = f"时间间隔: {days_diff} 天"
            except:
                period_info = "时间间隔: 未知"
            
            # 基本信息对比
            basic_comparison = f"""
## 基本信息对比
{period_info}

### 快照1 ({s1.get('date', 'N/A')})
- 总资产价值: ¥{s1.get('total_value', 0):,.2f}
- 总投入成本: ¥{s1.get('total_cost', 0):,.2f}
- 总收益: ¥{s1.get('total_return', 0):,.2f}
- 总收益率: {s1.get('total_return_rate', 0):.2f}%

### 快照2 ({s2.get('date', 'N/A')})
- 总资产价值: ¥{s2.get('total_value', 0):,.2f}
- 总投入成本: ¥{s2.get('total_cost', 0):,.2f}
- 总收益: ¥{s2.get('total_return', 0):,.2f}
- 总收益率: {s2.get('total_return_rate', 0):.2f}%

### 变化情况
- 资产价值变化: ¥{s2.get('total_value', 0) - s1.get('total_value', 0):,.2f}
- 投入成本变化: ¥{s2.get('total_cost', 0) - s1.get('total_cost', 0):,.2f}
- 收益变化: ¥{s2.get('total_return', 0) - s1.get('total_return', 0):,.2f}
- 收益率变化: {s2.get('total_return_rate', 0) - s1.get('total_return_rate', 0):.2f}%
"""

            # 资产配置对比
            allocation1 = s1.get('allocation', {})
            allocation2 = s2.get('allocation', {})
            
            allocation_comparison = """
## 资产配置对比
"""
            for asset_type in ['cash', 'fixed_income', 'equity', 'real_estate', 'commodity']:
                value1 = allocation1.get(asset_type, 0)
                value2 = allocation2.get(asset_type, 0)
                change = value2 - value1
                change_text = f"增加 ¥{change:,.2f}" if change >= 0 else f"减少 ¥{abs(change):,.2f}"
                
                asset_name = {
                    'cash': '现金及等价物',
                    'fixed_income': '固定收益类',
                    'equity': '权益类',
                    'real_estate': '房地产',
                    'commodity': '大宗商品'
                }.get(asset_type, asset_type)
                
                allocation_comparison += f"- {asset_name}: ¥{value1:,.2f} → ¥{value2:,.2f} ({change_text})\n"
            
            # 业绩指标对比
            metrics1 = s1.get('performance_metrics', {})
            metrics2 = s2.get('performance_metrics', {})
            
            if metrics1 and metrics2:
                metrics_comparison = """
## 业绩指标对比
"""
                for metric_name, display_name in [
                    ('annualized_return', '年化收益率'),
                    ('volatility', '波动率'),
                    ('sharpe_ratio', '夏普比率'),
                    ('max_drawdown', '最大回撤')
                ]:
                    value1 = metrics1.get(metric_name, 0)
                    value2 = metrics2.get(metric_name, 0)
                    change = value2 - value1
                    change_text = f"提高 {change:.2f}" if change >= 0 else f"下降 {abs(change):.2f}"
                    
                    metrics_comparison += f"- {display_name}: {value1:.2f} → {value2:.2f} ({change_text})\n"
            else:
                metrics_comparison = ""
            
            return basic_comparison + allocation_comparison + metrics_comparison
            
        else:
            return "数据格式无法识别"


class LocalAIService(CloudAIService):
    """本地AI服务（Ollama）"""
    
    def __init__(self, config: AIAnalysisConfig):
        super().__init__(config)
        self.base_url = f"http://localhost:{config.local_api_port}"
        self.model = config.local_model_name or "llama3.1:8b"
    
    def analyze(self, data: Dict[str, Any], prompt: str) -> str:
        """使用本地Ollama执行AI分析"""
        try:
            url = f"{self.base_url}/api/generate"
            full_prompt = self._build_analysis_prompt(data, prompt)
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                },
                "stream": False
            }
            
            response = requests.post(
                url, 
                json=payload, 
                timeout=self.config.timeout_seconds
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '本地AI分析完成，但未返回内容')
            
        except Exception as e:
            self.logger.error(f"本地AI分析失败: {e}")
            raise
    
    def test_connection(self) -> bool:
        """测试本地AI连接"""
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"本地AI连接测试失败: {e}")
            return False
    
    def _build_analysis_prompt(self, data: Dict[str, Any], base_prompt: str, prompt_type: str = "default") -> str:
        """构建分析prompt（本地AI版本）
        
        Args:
            data: 分析数据
            base_prompt: 基础提示
            prompt_type: 提示类型，可选值：default, simple, detailed, risk_focused
            
        Returns:
            格式化后的用户提示
        """
        # 本地AI可能需要更简洁的prompt
        data_text = self._format_portfolio_data(data)
        
        return f"""
{base_prompt}

投资组合数据：
{data_text}

请分析投资组合的表现、风险和优化建议。用中文回复。
"""
    
    def _format_portfolio_data(self, data: Dict[str, Any]) -> str:
        """格式化投资组合数据（简化版）"""
        if 'snapshot' in data:
            snapshot = data['snapshot']
            return f"总价值¥{snapshot.get('total_value', 0):,.0f}，收益率{snapshot.get('total_return_rate', 0):.1f}%"
        elif 'snapshot1' in data and 'snapshot2' in data:
            s1, s2 = data['snapshot1'], data['snapshot2']
            return f"期间价值从¥{s1.get('total_value', 0):,.0f}变为¥{s2.get('total_value', 0):,.0f}"
        else:
            return "数据不可用"


class AIAnalysisService:
    """AI分析服务主类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._services_cache = {}
        self._conversation_history = {}  # 存储对话历史，key为conversation_id
    
    def get_ai_service(self, config: AIAnalysisConfig) -> CloudAIService:
        """根据配置获取AI服务实例"""
        cache_key = f"{config.ai_type.name}_{config.config_id}"
        
        if cache_key not in self._services_cache:
            if config.ai_type.name == "CLOUD":
                # 根据云端提供商选择服务
                provider = config.cloud_provider.lower()
                if provider in ['openrouter', 'or']:
                    self._services_cache[cache_key] = OpenRouterService(config)
                else:
                    # 默认使用OpenRouter
                    self._services_cache[cache_key] = OpenRouterService(config)
            elif config.ai_type.name == "LOCAL":
                self._services_cache[cache_key] = LocalAIService(config)
            else:
                raise ValueError(f"不支持的AI类型: {config.ai_type}")
        
        return self._services_cache[cache_key]
    
    def analyze_snapshot(self, snapshot: PortfolioSnapshot, config: AIAnalysisConfig, 
                        user_prompt: str = "", conversation_id: str = None,
                        system_prompt_type: str = "default", user_prompt_type: str = "default",
                        result_template_type: str = "default") -> AIAnalysisResult:
        """
        分析单个快照
        
        Args:
            snapshot: 投资组合快照
            config: AI配置
            user_prompt: 用户提示
            conversation_id: 对话ID
            system_prompt_type: 系统提示类型
            user_prompt_type: 用户提示类型
            result_template_type: 结果模板类型
            
        Returns:
            AI分析结果
        """
        result = AIAnalysisResult(
            snapshot1_id=snapshot.snapshot_id,
            config_id=config.config_id,
            analysis_type="SINGLE_SNAPSHOT"
        )
        
        try:
            start_time = time.time()
            
            # 准备分析数据
            data = {
                'snapshot': {
                    'date': snapshot.snapshot_date.isoformat(),
                    'total_value': float(snapshot.total_value),
                    'total_cost': float(snapshot.total_cost),
                    'total_return': float(snapshot.total_return),
                    'total_return_rate': float(snapshot.total_return_rate),
                    'allocation': {
                        'cash': float(snapshot.cash_value),
                        'fixed_income': float(snapshot.fixed_income_value),
                        'equity': float(snapshot.equity_value),
                        'real_estate': float(snapshot.real_estate_value),
                        'commodity': float(snapshot.commodity_value)
                    },
                    'position_snapshots': snapshot.position_snapshots,
                    'performance_metrics': snapshot.performance_metrics
                }
            }
            
            # 构建prompt
            base_prompt = user_prompt or "请分析这个投资组合的表现和风险状况，并提供优化建议。"
            
            # 获取AI服务
            ai_service = self.get_ai_service(config)
            
            # 获取对话历史
            if conversation_id:
                messages = self._get_conversation_history(conversation_id)
                # 添加用户新的提问
                messages.append({"role": "user", "content": base_prompt})
            else:
                # 创建新的对话
                conversation_id = str(uuid.uuid4())
                messages = [{"role": "user", "content": base_prompt}]
            
            # 执行分析
            analysis_content = self._analyze_with_history(
                ai_service, data, messages, conversation_id,
                system_prompt_type, user_prompt_type
            )
            
            # 解析结果
            parsed_result = self._parse_ai_response(analysis_content, result_template_type)
            
            # 更新结果
            result.analysis_content = analysis_content
            result.analysis_summary = parsed_result.get('summary', '')
            result.investment_advice = parsed_result.get('advice', '')
            result.risk_assessment = parsed_result.get('risk', '')
            result.analysis_status = "SUCCESS"
            result.processing_time_ms = int((time.time() - start_time) * 1000)
            
            # 记录使用的prompt类型
            result.metadata = {
                'system_prompt_type': system_prompt_type,
                'user_prompt_type': user_prompt_type,
                'result_template_type': result_template_type
            }
            
            self.logger.info(f"快照分析完成: {snapshot.snapshot_id[:8]}...")
            
        except Exception as e:
            result.analysis_status = "FAILED"
            result.error_message = str(e)
            self.logger.error(f"快照分析失败: {e}")
        
        return result
    
    def compare_snapshots(self, snapshot1: PortfolioSnapshot, snapshot2: PortfolioSnapshot,
                         config: AIAnalysisConfig, user_prompt: str = "", conversation_id: str = None,
                         system_prompt_type: str = "default", user_prompt_type: str = "default",
                         result_template_type: str = "default") -> AIAnalysisResult:
        """
        对比分析两个快照
        
        Args:
            snapshot1: 第一个投资组合快照
            snapshot2: 第二个投资组合快照
            config: AI配置
            user_prompt: 用户提示
            conversation_id: 对话ID
            system_prompt_type: 系统提示类型
            user_prompt_type: 用户提示类型
            result_template_type: 结果模板类型
            
        Returns:
            AI分析结果
        """
        result = AIAnalysisResult(
            snapshot1_id=snapshot1.snapshot_id,
            snapshot2_id=snapshot2.snapshot_id,
            config_id=config.config_id,
            analysis_type="COMPARISON"
        )
        
        try:
            start_time = time.time()
            
            # 准备分析数据
            data = {
                'snapshot1': {
                    'date': snapshot1.snapshot_date.isoformat(),
                    'total_value': float(snapshot1.total_value),
                    'total_cost': float(snapshot1.total_cost),
                    'total_return': float(snapshot1.total_return),
                    'total_return_rate': float(snapshot1.total_return_rate),
                    'allocation': {
                        'cash': float(snapshot1.cash_value),
                        'fixed_income': float(snapshot1.fixed_income_value),
                        'equity': float(snapshot1.equity_value),
                        'real_estate': float(snapshot1.real_estate_value),
                        'commodity': float(snapshot1.commodity_value)
                    },
                    'position_snapshots': snapshot1.position_snapshots,
                    'performance_metrics': snapshot1.performance_metrics
                },
                'snapshot2': {
                    'date': snapshot2.snapshot_date.isoformat(),
                    'total_value': float(snapshot2.total_value),
                    'total_cost': float(snapshot2.total_cost),
                    'total_return': float(snapshot2.total_return),
                    'total_return_rate': float(snapshot2.total_return_rate),
                    'allocation': {
                        'cash': float(snapshot2.cash_value),
                        'fixed_income': float(snapshot2.fixed_income_value),
                        'equity': float(snapshot2.equity_value),
                        'real_estate': float(snapshot2.real_estate_value),
                        'commodity': float(snapshot2.commodity_value)
                    },
                    'position_snapshots': snapshot2.position_snapshots,
                    'performance_metrics': snapshot2.performance_metrics
                }
            }
            
            # 构建prompt
            base_prompt = user_prompt or "请对比分析这两个投资组合快照的变化，评估投资表现并提供优化建议。"
            
            # 获取AI服务
            ai_service = self.get_ai_service(config)
            
            # 获取对话历史
            if conversation_id:
                messages = self._get_conversation_history(conversation_id)
                # 添加用户新的提问
                messages.append({"role": "user", "content": base_prompt})
            else:
                # 创建新的对话
                conversation_id = str(uuid.uuid4())
                messages = [{"role": "user", "content": base_prompt}]
            
            # 执行分析
            analysis_content = self._analyze_with_history(
                ai_service, data, messages, conversation_id,
                system_prompt_type, user_prompt_type
            )
            
            # 解析结果
            parsed_result = self._parse_ai_response(analysis_content, result_template_type)
            
            # 更新结果
            result.analysis_content = analysis_content
            result.analysis_summary = parsed_result.get('summary', '')
            result.investment_advice = parsed_result.get('advice', '')
            result.risk_assessment = parsed_result.get('risk', '')
            result.analysis_status = "SUCCESS"
            result.processing_time_ms = int((time.time() - start_time) * 1000)
            
            # 记录使用的prompt类型
            result.metadata = {
                'system_prompt_type': system_prompt_type,
                'user_prompt_type': user_prompt_type,
                'result_template_type': result_template_type
            }
            
            self.logger.info(f"快照对比分析完成: {snapshot1.snapshot_id[:8]}... vs {snapshot2.snapshot_id[:8]}...")
            
        except Exception as e:
            result.analysis_status = "FAILED"
            result.error_message = str(e)
            self.logger.error(f"快照对比分析失败: {e}")
        
        return result
    
    def continue_conversation(self, conversation_id: str, user_message: str, config: AIAnalysisConfig) -> str:
        """继续已有的对话"""
        try:
            if not conversation_id or conversation_id not in self._conversation_history:
                raise ValueError(f"对话ID不存在: {conversation_id}")
            
            # 获取对话历史
            messages = self._get_conversation_history(conversation_id)
            
            # 添加用户新的消息
            messages.append({"role": "user", "content": user_message})
            
            # 获取AI服务
            ai_service = self.get_ai_service(config)
            
            # 执行分析（无需数据，仅基于对话历史）
            response = self._analyze_with_history(ai_service, None, messages, conversation_id)
            
            return response
            
        except Exception as e:
            self.logger.error(f"继续对话失败: {e}")
            raise
    
    def _analyze_with_history(self, ai_service: CloudAIService, data: Dict[str, Any], 
                             messages: List[Dict[str, str]], conversation_id: str,
                             system_prompt_type: str = "default", user_prompt_type: str = "default") -> str:
        """
        使用对话历史进行分析
        
        Args:
            ai_service: AI服务实例
            data: 分析数据
            messages: 对话历史消息
            conversation_id: 对话ID
            system_prompt_type: 系统提示类型
            user_prompt_type: 用户提示类型
            
        Returns:
            AI分析结果
        """
        try:
            # 获取系统提示
            system_prompt = get_system_prompt(system_prompt_type)
            
            # 如果有数据，构建数据提示
            if data:
                user_prompt = messages[-1]["content"]  # 获取最新的用户消息
                data_prompt = ai_service._build_analysis_prompt(data, user_prompt, user_prompt_type)
                
                # 替换最新的用户消息为带数据的提示
                messages[-1]["content"] = data_prompt
            
            # 添加系统消息
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            
            # 调用AI服务
            if isinstance(ai_service, OpenRouterService):
                logging.info(f"使用OpenRouterService进行分析，模型: {ai_service.model}")
                
                try:
                    # 使用_analyze_with_requests方法直接调用API
                    content = ai_service._analyze_with_requests(full_messages)
                    
                    # 更新对话历史
                    messages.append({"role": "assistant", "content": content})
                    self._conversation_history[conversation_id] = messages
                    
                    return content or "AI分析完成，但未返回内容"
                except Exception as e:
                    logging.error(f"使用OpenRouterService分析失败: {e}")
                    raise
            else:
                # 对于其他AI服务，使用简化的调用方式
                prompt = "\n".join([m["content"] for m in full_messages])
                content = ai_service.analyze(data, prompt)
                
                # 更新对话历史
                messages.append({"role": "assistant", "content": content})
                self._conversation_history[conversation_id] = messages
                
                return content
                
        except Exception as e:
            self.logger.error(f"使用对话历史分析失败: {e}")
            raise
    
    def _get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """获取对话历史"""
        if conversation_id in self._conversation_history:
            # 复制一份，避免直接修改原始历史
            return self._conversation_history[conversation_id].copy()
        else:
            return []
    
    def get_conversation(self, conversation_id: str) -> List[Dict[str, str]]:
        """获取完整对话历史"""
        return self._get_conversation_history(conversation_id)
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """清除对话历史"""
        if conversation_id in self._conversation_history:
            del self._conversation_history[conversation_id]
            return True
        return False
        
    def test_ai_config(self, config: AIAnalysisConfig) -> Dict[str, Any]:
        """测试AI配置"""
        try:
            ai_service = self.get_ai_service(config)
            is_connected = ai_service.test_connection()
            
            return {
                'success': is_connected,
                'message': '连接成功' if is_connected else '连接失败',
                'config_name': config.config_name,
                'ai_type': config.ai_type.display_name
            }
            
        except Exception as e:
            self.logger.error(f"AI配置测试失败: {e}")
            return {
                'success': False,
                'message': f'测试失败: {str(e)}',
                'config_name': config.config_name,
                'ai_type': config.ai_type.display_name
            }
    
    def _parse_ai_response(self, response: str, result_template_type: str = "default") -> Dict[str, str]:
        """
        解析AI响应内容，提取结构化信息
        
        Args:
            response: AI响应内容
            result_template_type: 结果模板类型，可选值：default, simple, detailed
            
        Returns:
            解析后的结构化信息
        """
        # 获取结果模板
        template = get_result_template(result_template_type)
        
        # 初始化结果部分
        sections = {
            'summary': '',
            'advice': '',
            'risk': ''
        }
        
        current_section = 'summary'  # 默认添加到摘要
        
        # 获取关键词列表
        summary_keywords = template.get('summary_keywords', ['概览', '总结', '摘要', '投资组合概览'])
        advice_keywords = template.get('advice_keywords', ['建议', '优化', '推荐', '投资建议'])
        risk_keywords = template.get('risk_keywords', ['风险', '评估', '注意', '风险评估'])
        
        # 尝试使用Markdown标题解析
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检查是否是Markdown标题
            if line.startswith('## ') or line.startswith('# '):
                title = line.lstrip('#').strip().lower()
                
                if any(keyword in title for keyword in summary_keywords):
                    current_section = 'summary'
                    continue
                elif any(keyword in title for keyword in advice_keywords):
                    current_section = 'advice'
                    continue
                elif any(keyword in title for keyword in risk_keywords):
                    current_section = 'risk'
                    continue
            
            # 根据当前段落添加内容
            sections[current_section] += line + "\n"
        
        # 如果没有提取到内容，使用关键词搜索
        if not sections['summary'].strip() and not sections['advice'].strip() and not sections['risk'].strip():
            current_section = 'summary'
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 识别段落标题
                if any(keyword in line.lower() for keyword in summary_keywords):
                    current_section = 'summary'
                    continue
                elif any(keyword in line.lower() for keyword in advice_keywords):
                    current_section = 'advice'
                    continue
                elif any(keyword in line.lower() for keyword in risk_keywords):
                    current_section = 'risk'
                    continue
                
                # 根据当前段落添加内容
                sections[current_section] += line + "\n"
        
        # 如果仍然没有提取到内容，使用整个响应
        if not sections['summary'].strip():
            sections['summary'] = response[:200] + "..." if len(response) > 200 else response
        
        return {
            'summary': sections['summary'].strip(),
            'advice': sections['advice'].strip(),
            'risk': sections['risk'].strip()
        }


# 创建全局AI分析服务实例
ai_analysis_service = AIAnalysisService() 