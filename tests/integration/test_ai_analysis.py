#!/usr/bin/env python3
"""
AI分析功能集成测试

测试内容：
1. AI配置管理
2. AI分析服务
3. OpenRouter接入
4. 提示模板系统
5. 环境变量加载
6. 对话历史管理
"""

import os
import sys
import uuid
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock

# 导入测试目标模块
from wealth_lite.data.database import DatabaseManager
from wealth_lite.services.snapshot_service import AIConfigService
from wealth_lite.services.ai_service import (
    ai_analysis_service, AIAnalysisService, 
    OpenRouterService, LocalAIService
)
from wealth_lite.models.snapshot import (
    AIAnalysisConfig, AIAnalysisResult, PortfolioSnapshot
)
from wealth_lite.models.enums import AIType, Currency, SnapshotType
from wealth_lite.config.env_loader import get_env, load_environment
from wealth_lite.config.prompt_templates import (
    get_system_prompt, get_user_prompt, get_result_template, 
    format_user_prompt, get_available_prompt_types
)


class TestAIConfigService:
    """AI配置服务测试"""
    
    @pytest.fixture(scope="class")
    def db_manager(self):
        """数据库管理器"""
        manager = DatabaseManager()
        yield manager
        manager.close()
    
    @pytest.fixture(scope="class")
    def config_service(self, db_manager):
        """AI配置服务"""
        return AIConfigService(db_manager)
    
    def test_get_default_config(self, config_service):
        """测试获取默认配置"""
        default_config = config_service.get_default_config()
        
        assert default_config is not None
        assert default_config.is_default is True
        assert default_config.config_name != ""
        assert isinstance(default_config.ai_type, AIType)
    
    def test_create_predefined_configs(self, config_service):
        """测试创建预定义配置"""
        configs = config_service.create_predefined_configs()
        
        assert len(configs) > 0
        for config in configs:
            assert isinstance(config, AIAnalysisConfig)
            assert config.config_name != ""
            assert isinstance(config.ai_type, AIType)
    
    def test_get_all_configs(self, config_service):
        """测试获取所有配置"""
        all_configs = config_service.get_all_configs()
        
        assert len(all_configs) > 0
        assert any(config.is_default for config in all_configs)
        
        # 验证配置字段
        for config in all_configs:
            assert isinstance(config, AIAnalysisConfig)
            assert config.config_id != ""
            assert config.config_name != ""
            assert isinstance(config.ai_type, AIType)
            assert isinstance(config.is_active, bool)


class TestPromptTemplates:
    """提示模板系统测试"""
    
    def test_get_system_prompt(self):
        """测试获取系统提示模板"""
        # 测试默认模板
        default_prompt = get_system_prompt()
        assert default_prompt != ""
        assert "金融分析师" in default_prompt
        
        # 测试特定模板
        conservative_prompt = get_system_prompt("conservative")
        assert conservative_prompt != ""
        assert "保守型投资" in conservative_prompt
        
        # 测试不存在的模板
        unknown_prompt = get_system_prompt("nonexistent")
        assert unknown_prompt == get_system_prompt()  # 应返回默认模板
    
    def test_get_user_prompt(self):
        """测试获取用户提示模板"""
        # 测试默认模板
        default_prompt = get_user_prompt()
        assert default_prompt != ""
        assert "{base_prompt}" in default_prompt
        assert "{data_text}" in default_prompt
        
        # 测试特定模板
        risk_prompt = get_user_prompt("risk_focused")
        assert risk_prompt != ""
        assert "风险状况" in risk_prompt
        
        # 测试不存在的模板
        unknown_prompt = get_user_prompt("nonexistent")
        assert unknown_prompt == get_user_prompt()  # 应返回默认模板
    
    def test_format_user_prompt(self):
        """测试格式化用户提示"""
        base_prompt = "测试提示"
        data_text = "测试数据"
        
        # 测试默认格式化
        formatted = format_user_prompt("default", base_prompt, data_text)
        assert base_prompt in formatted
        assert data_text in formatted
        
        # 测试简单格式化
        simple_formatted = format_user_prompt("simple", base_prompt, data_text)
        assert base_prompt in simple_formatted
        assert data_text in simple_formatted
        assert len(simple_formatted) < len(formatted)  # 简单模板应该更短
    
    def test_get_available_prompt_types(self):
        """测试获取可用提示类型"""
        types = get_available_prompt_types()
        
        assert "system_prompts" in types
        assert "user_prompts" in types
        assert "result_templates" in types
        
        assert "default" in types["system_prompts"]
        assert "default" in types["user_prompts"]
        assert "default" in types["result_templates"]


class TestEnvironmentLoader:
    """环境变量加载测试"""
    
    def test_load_environment(self):
        """测试加载环境变量"""
        env_vars = load_environment()
        
        assert isinstance(env_vars, dict)
        # 验证是否有环境名称
        assert "WEALTH_LITE_ENV" in os.environ or "WEALTH_LITE_ENV" in env_vars
    
    def test_get_env(self):
        """测试获取环境变量"""
        # 测试获取存在的变量
        env_name = get_env("WEALTH_LITE_ENV", "development")
        assert env_name is not None
        
        # 测试获取不存在的变量，使用默认值
        nonexistent = get_env("NONEXISTENT_VAR", "default_value")
        assert nonexistent == "default_value"
        
        # 测试OpenRouter API Key
        api_key = get_env("OPENROUTER_API_KEY", "")
        # 不验证具体值，只验证类型
        assert isinstance(api_key, str)


class TestAIAnalysisService:
    """AI分析服务测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟AI配置"""
        return AIAnalysisConfig(
            config_id=str(uuid.uuid4()),
            config_name="测试配置",
            ai_type=AIType.CLOUD,
            cloud_provider="openrouter",
            cloud_api_url="https://openrouter.ai/api/v1",
            cloud_model_name="deepseek/deepseek-chat",
            cloud_api_key="test_key"
        )
        
    @pytest.fixture(autouse=True)
    def patch_openai(self, monkeypatch):
        """修补OpenAI类以避免初始化错误"""
        # 创建模拟的OpenAI类
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # 修补OpenAI类
        monkeypatch.setattr('wealth_lite.services.ai_service.OpenAI', mock_openai)
        
        return mock_client
    
    @pytest.fixture
    def mock_snapshot(self):
        """模拟投资组合快照"""
        return PortfolioSnapshot(
            snapshot_id=str(uuid.uuid4()),
            snapshot_date=date.today(),
            snapshot_type=SnapshotType.MANUAL,
            base_currency=Currency.CNY,
            total_value=Decimal('10000'),
            total_cost=Decimal('9000'),
            total_return=Decimal('1000'),
            total_return_rate=Decimal('11.11'),
            cash_value=Decimal('2000'),
            fixed_income_value=Decimal('3000'),
            equity_value=Decimal('5000'),
            position_snapshots=[
                {
                    'asset_name': '测试资产1',
                    'asset_type': 'EQUITY',
                    'current_value': 5000,
                    'cost_basis': 4500,
                    'total_return': 500,
                    'total_return_rate': 11.11
                }
            ]
        )
    
    def test_get_ai_service(self, mock_config):
        """测试获取AI服务实例"""
        service = AIAnalysisService()
        
        # 测试云端服务
        cloud_config = mock_config
        cloud_service = service.get_ai_service(cloud_config)
        assert isinstance(cloud_service, OpenRouterService)
        
        # 测试本地服务
        local_config = AIAnalysisConfig(
            config_name="本地测试",
            ai_type=AIType.LOCAL,
            local_model_name="llama3.1:8b"
        )
        local_service = service.get_ai_service(local_config)
        assert isinstance(local_service, LocalAIService)
        
        # 测试服务缓存
        cached_service = service.get_ai_service(cloud_config)
        assert cached_service is cloud_service  # 应该是同一个实例
    
    @patch('wealth_lite.services.ai_service.AIAnalysisService._analyze_with_history')
    def test_analyze_snapshot(self, mock_analyze_with_history, mock_config, mock_snapshot):
        """测试快照分析"""
        # 模拟AI分析返回结果
        mock_analyze_with_history.return_value = """
## 投资组合概览
这是一个测试投资组合，总资产价值¥10,000。

## 风险评估
风险较低。

## 投资建议
建议增加股票配置。
"""
        
        service = AIAnalysisService()
        
        # 修补处理时间计算
        with patch('time.time', side_effect=[1000, 1100]):  # 模拟开始和结束时间，相差100秒
            result = service.analyze_snapshot(
                mock_snapshot, 
                mock_config,
                user_prompt="测试分析",
                system_prompt_type="default",
                user_prompt_type="simple"
            )
        
        # 验证分析结果
        assert isinstance(result, AIAnalysisResult)
        assert result.is_success
        assert result.analysis_status == "SUCCESS"
        assert result.snapshot1_id == mock_snapshot.snapshot_id
        assert result.config_id == mock_config.config_id
        assert result.analysis_content != ""
        assert result.analysis_summary != ""
        assert result.investment_advice != ""
        assert result.processing_time_ms > 0  # 现在应该通过，因为我们模拟了时间差
        
        # 验证元数据
        assert "system_prompt_type" in result.metadata
        assert result.metadata["system_prompt_type"] == "default"
        assert result.metadata["user_prompt_type"] == "simple"
    
    @patch('wealth_lite.services.ai_service.AIAnalysisService._analyze_with_history')
    def test_compare_snapshots(self, mock_analyze_with_history, mock_config, mock_snapshot):
        """测试快照对比分析"""
        # 模拟AI分析返回结果
        mock_analyze_with_history.return_value = """
## 投资组合对比
两个快照之间的对比分析。

## 风险变化
风险水平保持稳定。

## 优化建议
建议调整资产配置。
"""
        
        # 创建第二个快照
        snapshot2 = PortfolioSnapshot(
            snapshot_id=str(uuid.uuid4()),
            snapshot_date=date.today(),
            total_value=Decimal('11000'),
            total_cost=Decimal('9000'),
            total_return=Decimal('2000'),
            total_return_rate=Decimal('22.22')
        )
        
        service = AIAnalysisService()
        
        # 修补处理时间计算
        with patch('time.time', side_effect=[1000, 1100]):  # 模拟开始和结束时间，相差100秒
            result = service.compare_snapshots(
                mock_snapshot,
                snapshot2,
                mock_config,
                user_prompt="测试对比分析"
            )
        
        # 验证分析结果
        assert isinstance(result, AIAnalysisResult)
        assert result.is_success
        assert result.analysis_status == "SUCCESS"
        assert result.snapshot1_id == mock_snapshot.snapshot_id
        assert result.snapshot2_id == snapshot2.snapshot_id
        assert result.config_id == mock_config.config_id
        assert result.analysis_content != ""
        assert result.analysis_summary != ""
        assert result.investment_advice != ""
        assert result.processing_time_ms > 0  # 现在应该通过，因为我们模拟了时间差
    
    def test_conversation_management(self, mock_config):
        """测试对话管理功能"""
        service = AIAnalysisService()
        
        # 创建新对话
        conversation_id = str(uuid.uuid4())
        
        # 模拟对话历史
        service._conversation_history[conversation_id] = [
            {"role": "user", "content": "第一条消息"},
            {"role": "assistant", "content": "第一条回复"}
        ]
        
        # 测试获取对话历史
        history = service.get_conversation(conversation_id)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "第一条消息"
        
        # 测试清除对话历史
        success = service.clear_conversation(conversation_id)
        assert success is True
        
        # 验证对话已清除
        assert conversation_id not in service._conversation_history
        
        # 测试清除不存在的对话
        success = service.clear_conversation("nonexistent")
        assert success is False


class TestOpenRouterService:
    """OpenRouter服务测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟AI配置"""
        return AIAnalysisConfig(
            config_name="OpenRouter测试",
            ai_type=AIType.CLOUD,
            cloud_provider="openrouter",
            cloud_api_url="https://openrouter.ai/api/v1",
            cloud_model_name="deepseek/deepseek-chat",
            cloud_api_key=get_env("OPENROUTER_API_KEY", "test_key")
        )
    
    @pytest.fixture
    def patch_openai(self, monkeypatch):
        """修补OpenAI类以避免初始化错误"""
        # 创建模拟的OpenAI类
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # 修补OpenAI类
        monkeypatch.setattr('wealth_lite.services.ai_service.OpenAI', mock_openai)
        
        return mock_client
    
    def test_init_service(self, mock_config, patch_openai):
        """测试服务初始化"""
        # 创建服务
        service = OpenRouterService(mock_config)
        
        # 验证服务属性
        assert service.base_url == mock_config.cloud_api_url
        assert service.model == mock_config.cloud_model_name
        assert service.api_key is not None
    
    def test_build_analysis_prompt(self, mock_config, patch_openai):
        """测试构建分析提示"""
        # 创建服务
        service = OpenRouterService(mock_config)
        
        # 测试单个快照数据
        data = {
            'snapshot': {
                'date': '2023-01-01',
                'total_value': 10000.0,
                'total_cost': 9000.0,
                'total_return': 1000.0,
                'total_return_rate': 11.11,
                'allocation': {
                    'cash': 2000.0,
                    'fixed_income': 3000.0,
                    'equity': 5000.0,
                    'real_estate': 0.0,
                    'commodity': 0.0
                }
            }
        }
        
        prompt = service._build_analysis_prompt(data, "测试分析", "default")
        
        # 验证提示内容
        assert "测试分析" in prompt
        assert "投资组合数据" in prompt
        assert "¥10,000" in prompt  # 检查格式化后的金额，包含货币符号和千位分隔符
        assert "11.11%" in prompt
        
        # 测试不同提示类型
        simple_prompt = service._build_analysis_prompt(data, "测试分析", "simple")
        assert len(simple_prompt) < len(prompt)  # 简单提示应该更短
        
        # 测试对比数据
        compare_data = {
            'snapshot1': data['snapshot'],
            'snapshot2': {
                'date': '2023-02-01',
                'total_value': 11000.0,
                'total_return_rate': 22.22
            }
        }
        
        compare_prompt = service._build_analysis_prompt(compare_data, "测试对比", "default")
        assert "测试对比" in compare_prompt
        assert "变化情况" in compare_prompt
        assert "¥11,000" in compare_prompt  # 检查格式化后的金额


class TestLocalAIService:
    """本地AI服务测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟AI配置"""
        return AIAnalysisConfig(
            config_name="本地AI测试",
            ai_type=AIType.LOCAL,
            local_model_name="llama3.1:8b",
            local_api_port=11434
        )
    
    def test_init_service(self, mock_config):
        """测试服务初始化"""
        service = LocalAIService(mock_config)
        
        # 验证服务属性
        assert service.base_url == f"http://localhost:{mock_config.local_api_port}"
        assert service.model == mock_config.local_model_name
    
    @patch('requests.post')
    def test_analyze(self, mock_post, mock_config):
        """测试本地AI分析"""
        # 模拟请求响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': '这是本地AI的分析结果'
        }
        mock_post.return_value = mock_response
        
        service = LocalAIService(mock_config)
        
        # 测试分析
        data = {'snapshot': {'total_value': 10000.0}}
        result = service.analyze(data, "测试本地AI分析")
        
        # 验证结果
        assert result == '这是本地AI的分析结果'
        
        # 验证请求参数
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == f"{service.base_url}/api/generate"
        assert kwargs['json']['model'] == service.model
        assert kwargs['json']['prompt'] is not None
        assert kwargs['json']['stream'] is False
    
    @patch('requests.get')
    def test_test_connection(self, mock_get, mock_config):
        """测试连接测试功能"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        service = LocalAIService(mock_config)
        
        # 测试连接
        result = service.test_connection()
        
        # 验证结果
        assert result is True
        
        # 模拟失败响应
        mock_response.status_code = 404
        result = service.test_connection()
        
        # 验证结果
        assert result is False


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 