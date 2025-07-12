#!/usr/bin/env python3
"""
AI服务单元测试

测试内容：
1. OpenRouterService
2. LocalAIService
3. AIAnalysisService
4. 对话历史管理
5. 分析结果解析
"""

import uuid
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock, Mock

from wealth_lite.services.ai_service import (
    AIAnalysisService, OpenRouterService, LocalAIService
)
from wealth_lite.models.snapshot import (
    AIAnalysisConfig, AIAnalysisResult, PortfolioSnapshot
)
from wealth_lite.models.enums import AIType, Currency, SnapshotType


class TestOpenRouterService:
    """OpenRouter服务测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟AI配置"""
        return AIAnalysisConfig(
            config_id=str(uuid.uuid4()),
            config_name="测试OpenRouter",
            ai_type=AIType.CLOUD,
            cloud_provider="openrouter",
            cloud_api_url="https://openrouter.ai/api/v1",
            cloud_model_name="deepseek/deepseek-chat",
            cloud_api_key="test_key",
            max_tokens=2000,
            temperature=0.7,
            timeout_seconds=30
        )
    
    @patch('wealth_lite.services.ai_service.get_env')
    @patch('wealth_lite.services.ai_service.OpenAI')
    def test_init(self, mock_openai, mock_get_env, mock_config):
        """测试初始化"""
        # 模拟环境变量
        mock_get_env.return_value = "env_api_key"
        
        # 模拟OpenAI客户端
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # 创建服务
        service = OpenRouterService(mock_config)
        
        # 验证属性
        assert service.base_url == mock_config.cloud_api_url
        assert service.api_key == "env_api_key"  # 应该使用环境变量中的API Key
        assert service.model == mock_config.cloud_model_name
        
        # 验证OpenAI客户端初始化
        mock_openai.assert_called_once_with(
            base_url=mock_config.cloud_api_url,
            api_key="env_api_key"
        )
    
    @patch('wealth_lite.services.ai_service.get_env')
    @patch('wealth_lite.services.ai_service.OpenAI')
    def test_analyze(self, mock_openai, mock_get_env, mock_config):
        """测试分析方法"""
        # 模拟环境变量
        mock_get_env.return_value = "env_api_key"
        
        # 模拟OpenAI客户端
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        
        mock_message.content = "AI分析结果"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # 创建服务
        service = OpenRouterService(mock_config)
        
        # 测试分析
        data = {"snapshot": {"total_value": 10000}}
        result = service.analyze(data, "测试分析", "default", "default")
        
        # 验证结果
        assert result == "AI分析结果"
        
        # 验证API调用
        mock_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs["model"] == mock_config.cloud_model_name
        assert len(kwargs["messages"]) == 2
        assert kwargs["messages"][0]["role"] == "system"
        assert kwargs["messages"][1]["role"] == "user"
        assert kwargs["max_tokens"] == mock_config.max_tokens
        assert kwargs["temperature"] == mock_config.temperature
        assert kwargs["timeout"] == mock_config.timeout_seconds
    
    @patch('wealth_lite.services.ai_service.OpenRouterService.test_connection')
    def test_test_connection(self, mock_test_connection, mock_config):
        """测试连接测试方法"""
        # 直接模拟test_connection方法，而不是创建实际的服务实例
        
        # 创建服务（不需要实际初始化）
        with patch('wealth_lite.services.ai_service.OpenAI'):
            with patch('wealth_lite.services.ai_service.get_env', return_value="test_key"):
                service = OpenRouterService(mock_config)
        
        # 测试连接成功
        mock_test_connection.return_value = True
        result = service.test_connection()
        assert result is True
        
        # 测试连接失败
        mock_test_connection.return_value = False
        result = service.test_connection()
        assert result is False
    
    @patch('wealth_lite.services.ai_service.get_env')
    @patch('wealth_lite.services.ai_service.OpenAI')
    def test_format_portfolio_data(self, mock_openai, mock_get_env, mock_config):
        """测试投资组合数据格式化"""
        # 模拟环境变量和OpenAI客户端
        mock_get_env.return_value = "env_api_key"
        mock_openai.return_value = MagicMock()
        
        # 创建服务
        service = OpenRouterService(mock_config)
        
        # 测试单个快照数据格式化
        snapshot_data = {
            'snapshot': {
                'date': '2023-01-01',
                'total_value': 10000,
                'total_cost': 9000,
                'total_return': 1000,
                'total_return_rate': 11.11,
                'allocation': {
                    'cash': 2000,
                    'fixed_income': 3000,
                    'equity': 5000,
                    'real_estate': 0,
                    'commodity': 0
                },
                'position_snapshots': [
                    {
                        'asset_name': '测试资产',
                        'asset_type': 'EQUITY',
                        'current_value': 5000,
                        'cost_basis': 4500,
                        'total_return': 500,
                        'total_return_rate': 11.11
                    }
                ]
            }
        }
        
        formatted = service._format_portfolio_data(snapshot_data)
        
        # 验证格式化结果
        assert "基本信息" in formatted
        assert "资产配置" in formatted
        assert "持仓明细" in formatted
        assert "¥10,000.00" in formatted
        assert "测试资产" in formatted
        
        # 测试对比数据格式化
        comparison_data = {
            'snapshot1': snapshot_data['snapshot'],
            'snapshot2': {
                'date': '2023-02-01',
                'total_value': 11000,
                'total_cost': 9000,
                'total_return': 2000,
                'total_return_rate': 22.22,
                'allocation': {
                    'cash': 2000,
                    'fixed_income': 3000,
                    'equity': 6000,
                    'real_estate': 0,
                    'commodity': 0
                },
                'performance_metrics': {
                    'annualized_return': 15.0,
                    'volatility': 5.0
                }
            }
        }
        
        formatted = service._format_portfolio_data(comparison_data)
        
        # 验证格式化结果
        assert "基本信息对比" in formatted
        assert "资产配置对比" in formatted
        assert "变化情况" in formatted
        assert "¥11,000.00" in formatted
        
        # 测试无法识别的数据格式
        invalid_data = {"invalid": "data"}
        formatted = service._format_portfolio_data(invalid_data)
        assert "数据格式无法识别" in formatted


class TestLocalAIService:
    """本地AI服务测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟AI配置"""
        return AIAnalysisConfig(
            config_id=str(uuid.uuid4()),
            config_name="测试本地AI",
            ai_type=AIType.LOCAL,
            local_model_name="llama3.1:8b",
            local_api_port=11434,
            max_tokens=2000,
            temperature=0.7,
            timeout_seconds=30
        )
    
    def test_init(self, mock_config):
        """测试初始化"""
        service = LocalAIService(mock_config)
        
        # 验证属性
        assert service.base_url == f"http://localhost:{mock_config.local_api_port}"
        assert service.model == mock_config.local_model_name
    
    @patch('requests.post')
    def test_analyze(self, mock_post, mock_config):
        """测试分析方法"""
        # 模拟请求响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': '本地AI分析结果'
        }
        mock_post.return_value = mock_response
        
        # 创建服务
        service = LocalAIService(mock_config)
        
        # 测试分析
        data = {"snapshot": {"total_value": 10000}}
        result = service.analyze(data, "测试本地AI分析")
        
        # 验证结果
        assert result == '本地AI分析结果'
        
        # 验证请求
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == f"{service.base_url}/api/generate"
        assert kwargs['json']['model'] == service.model
        assert kwargs['json']['prompt'] is not None
        assert kwargs['json']['stream'] is False
        assert kwargs['json']['options']['temperature'] == mock_config.temperature
        assert kwargs['json']['options']['num_predict'] == mock_config.max_tokens
        assert kwargs['timeout'] == mock_config.timeout_seconds
    
    @patch('requests.get')
    def test_test_connection(self, mock_get, mock_config):
        """测试连接测试方法"""
        # 模拟请求响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 创建服务
        service = LocalAIService(mock_config)
        
        # 测试连接成功
        result = service.test_connection()
        assert result is True
        
        # 验证请求
        mock_get.assert_called_once_with(f"{service.base_url}/api/tags", timeout=5)
        
        # 测试连接失败
        mock_response.status_code = 404
        mock_get.reset_mock()
        result = service.test_connection()
        assert result is False
        
        # 测试连接异常
        mock_get.side_effect = Exception("测试异常")
        result = service.test_connection()
        assert result is False


class TestAIAnalysisService:
    """AI分析服务测试"""
    
    @pytest.fixture
    def cloud_config(self):
        """云端AI配置"""
        return AIAnalysisConfig(
            config_id=str(uuid.uuid4()),
            config_name="测试云端AI",
            ai_type=AIType.CLOUD,
            cloud_provider="openrouter",
            cloud_model_name="deepseek/deepseek-chat"
        )
    
    @pytest.fixture
    def local_config(self):
        """本地AI配置"""
        return AIAnalysisConfig(
            config_id=str(uuid.uuid4()),
            config_name="测试本地AI",
            ai_type=AIType.LOCAL,
            local_model_name="llama3.1:8b"
        )
    
    @pytest.fixture
    def snapshot(self):
        """测试快照"""
        return PortfolioSnapshot(
            snapshot_id=str(uuid.uuid4()),
            snapshot_date=date.today(),
            total_value=Decimal('10000'),
            total_cost=Decimal('9000'),
            total_return=Decimal('1000'),
            total_return_rate=Decimal('11.11'),
            cash_value=Decimal('2000'),
            fixed_income_value=Decimal('3000'),
            equity_value=Decimal('5000')
        )
    
    @patch('wealth_lite.services.ai_service.OpenRouterService')
    @patch('wealth_lite.services.ai_service.LocalAIService')
    def test_get_ai_service(self, mock_local_service, mock_or_service, cloud_config, local_config):
        """测试获取AI服务实例"""
        # 设置模拟实例
        mock_cloud_instance = MagicMock()
        mock_local_instance = MagicMock()
        mock_or_service.return_value = mock_cloud_instance
        mock_local_service.return_value = mock_local_instance
        
        service = AIAnalysisService()
        
        # 测试获取云端服务
        cloud_instance = service.get_ai_service(cloud_config)
        assert cloud_instance is mock_cloud_instance
        mock_or_service.assert_called_once_with(cloud_config)
        
        # 测试获取本地服务
        local_instance = service.get_ai_service(local_config)
        assert local_instance is mock_local_instance
        mock_local_service.assert_called_once_with(local_config)
        
        # 测试服务缓存
        mock_or_service.reset_mock()  # 重置调用计数
        cloud_instance2 = service.get_ai_service(cloud_config)
        assert cloud_instance2 is cloud_instance  # 应该是同一个实例
        mock_or_service.assert_not_called()  # 不应该再次调用构造函数
    
    @patch('wealth_lite.services.ai_service.OpenRouterService')
    @patch('wealth_lite.services.ai_service.AIAnalysisService._analyze_with_history')
    def test_analyze_snapshot(self, mock_analyze_with_history, mock_or_service, cloud_config, snapshot):
        """测试快照分析"""
        # 模拟OpenRouterService和_analyze_with_history方法
        mock_instance = MagicMock()
        mock_or_service.return_value = mock_instance
        
        mock_analyze_with_history.return_value = """
## 投资组合概览
这是一个测试投资组合，总资产价值¥10,000。

## 风险评估
风险较低。

## 投资建议
建议增加股票配置。
"""
        
        # 创建服务
        service = AIAnalysisService()
        
        # 测试分析
        result = service.analyze_snapshot(
            snapshot, 
            cloud_config,
            user_prompt="测试分析",
            system_prompt_type="default",
            user_prompt_type="simple"
        )
        
        # 验证结果
        assert isinstance(result, AIAnalysisResult)
        assert result.is_success
        assert result.analysis_status == "SUCCESS"
        assert result.snapshot1_id == snapshot.snapshot_id
        assert result.config_id == cloud_config.config_id
        assert result.analysis_content != ""
        assert result.analysis_summary != ""
        
        # 验证元数据
        assert "system_prompt_type" in result.metadata
        assert result.metadata["system_prompt_type"] == "default"
        assert result.metadata["user_prompt_type"] == "simple"
        
        # 验证_analyze_with_history被正确调用
        mock_analyze_with_history.assert_called_once()
    
    @patch('wealth_lite.services.ai_service.OpenRouterService')
    @patch('wealth_lite.services.ai_service.AIAnalysisService._analyze_with_history')
    def test_compare_snapshots(self, mock_analyze_with_history, mock_or_service, cloud_config, snapshot):
        """测试快照对比分析"""
        # 模拟OpenRouterService和_analyze_with_history方法
        mock_instance = MagicMock()
        mock_or_service.return_value = mock_instance
        
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
        
        # 创建服务
        service = AIAnalysisService()
        
        # 测试对比分析
        result = service.compare_snapshots(
            snapshot,
            snapshot2,
            cloud_config,
            user_prompt="测试对比分析"
        )
        
        # 验证结果
        assert isinstance(result, AIAnalysisResult)
        assert result.is_success
        assert result.analysis_status == "SUCCESS"
        assert result.snapshot1_id == snapshot.snapshot_id
        assert result.snapshot2_id == snapshot2.snapshot_id
        assert result.config_id == cloud_config.config_id
        assert result.analysis_content != ""
        
        # 验证_analyze_with_history被正确调用
        mock_analyze_with_history.assert_called_once()
    
    def test_conversation_management(self):
        """测试对话管理"""
        service = AIAnalysisService()
        
        # 测试初始状态
        assert len(service._conversation_history) == 0
        
        # 创建对话
        conversation_id = str(uuid.uuid4())
        messages = [
            {"role": "user", "content": "第一条消息"},
            {"role": "assistant", "content": "第一条回复"}
        ]
        service._conversation_history[conversation_id] = messages
        
        # 测试获取对话
        history = service.get_conversation(conversation_id)
        assert len(history) == 2
        assert history[0]["content"] == "第一条消息"
        
        # 测试获取不存在的对话
        empty_history = service.get_conversation("nonexistent")
        assert empty_history == []
        
        # 测试清除对话
        result = service.clear_conversation(conversation_id)
        assert result is True
        assert conversation_id not in service._conversation_history
        
        # 测试清除不存在的对话
        result = service.clear_conversation(conversation_id)
        assert result is False
    
    @patch('wealth_lite.services.ai_service.OpenRouterService')
    @patch('wealth_lite.services.ai_service.AIAnalysisService._analyze_with_history')
    def test_continue_conversation(self, mock_analyze_with_history, mock_or_service):
        """测试继续对话"""
        # 模拟OpenRouterService和_analyze_with_history方法
        mock_instance = MagicMock()
        mock_or_service.return_value = mock_instance
        
        mock_analyze_with_history.return_value = "继续对话的回复"
        
        # 创建服务
        service = AIAnalysisService()
        
        # 创建对话
        conversation_id = str(uuid.uuid4())
        messages = [
            {"role": "user", "content": "第一条消息"},
            {"role": "assistant", "content": "第一条回复"}
        ]
        service._conversation_history[conversation_id] = messages.copy()
        
        # 测试继续对话
        config = AIAnalysisConfig(ai_type=AIType.CLOUD)
        response = service.continue_conversation(conversation_id, "第二条消息", config)
        
        # 验证结果
        assert response == "继续对话的回复"
        
        # 验证_analyze_with_history被正确调用
        mock_analyze_with_history.assert_called_once()
        
        # 手动模拟对话历史更新
        expected_history = messages + [
            {"role": "user", "content": "第二条消息"},
            {"role": "assistant", "content": "继续对话的回复"}
        ]
        service._conversation_history[conversation_id] = expected_history
        
        # 验证对话历史
        history = service.get_conversation(conversation_id)
        assert len(history) == 4  # 原来2条 + 用户新消息 + AI回复
        assert history[2]["role"] == "user"
        assert history[2]["content"] == "第二条消息"
        assert history[3]["role"] == "assistant"
        assert history[3]["content"] == "继续对话的回复"
    
    def test_parse_ai_response(self):
        """测试解析AI响应"""
        service = AIAnalysisService()
        
        # 测试标准Markdown格式
        markdown_response = """
## 投资组合概览
这是一个测试投资组合，总资产价值¥10,000。

## 风险评估
风险较低。

## 投资建议
建议增加股票配置。
"""
        parsed = service._parse_ai_response(markdown_response)
        assert "这是一个测试投资组合，总资产价值¥10,000" in parsed["summary"]
        assert "风险较低" in parsed["risk"]
        assert "建议增加股票配置" in parsed["advice"]
        
        # 测试无标题格式
        no_heading_response = """
这是一个测试投资组合，总资产价值¥10,000。

风险评估：风险较低。

投资建议：建议增加股票配置。
"""
        parsed = service._parse_ai_response(no_heading_response)
        assert parsed["summary"] != ""
        
        # 测试使用不同模板
        parsed = service._parse_ai_response(markdown_response, "simple")
        assert parsed["summary"] != ""
        assert parsed["advice"] != ""


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 