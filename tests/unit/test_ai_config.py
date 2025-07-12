#!/usr/bin/env python3
"""
AI配置和工具单元测试

测试内容：
1. 提示模板系统
2. 环境变量加载
3. AI分析配置模型
4. AI分析结果模型
"""

import os
import uuid
import pytest
from datetime import date, datetime
from decimal import Decimal

from wealth_lite.models.snapshot import AIAnalysisConfig, AIAnalysisResult
from wealth_lite.models.enums import AIType
from wealth_lite.config.env_loader import get_env, load_env_file
from wealth_lite.config.prompt_templates import (
    get_system_prompt, get_user_prompt, get_result_template, 
    format_user_prompt, get_available_prompt_types
)


class TestPromptTemplates:
    """提示模板系统测试"""
    
    def test_system_prompts(self):
        """测试系统提示模板"""
        # 测试所有预定义的系统提示
        prompt_types = get_available_prompt_types()["system_prompts"]
        
        for prompt_type in prompt_types:
            prompt = get_system_prompt(prompt_type)
            assert prompt is not None
            assert isinstance(prompt, str)
            assert len(prompt) > 0
    
    def test_user_prompts(self):
        """测试用户提示模板"""
        # 测试所有预定义的用户提示
        prompt_types = get_available_prompt_types()["user_prompts"]
        
        for prompt_type in prompt_types:
            prompt = get_user_prompt(prompt_type)
            assert prompt is not None
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert "{base_prompt}" in prompt
            assert "{data_text}" in prompt
    
    def test_result_templates(self):
        """测试结果模板"""
        # 测试所有预定义的结果模板
        template_types = get_available_prompt_types()["result_templates"]
        
        for template_type in template_types:
            template = get_result_template(template_type)
            assert template is not None
            assert isinstance(template, dict)
            assert "sections" in template
            assert "summary_keywords" in template
            assert "advice_keywords" in template
            assert "risk_keywords" in template
    
    def test_format_user_prompt(self):
        """测试格式化用户提示"""
        base_prompt = "这是一个测试提示"
        data_text = "这是测试数据"
        
        # 测试所有提示类型的格式化
        prompt_types = get_available_prompt_types()["user_prompts"]
        
        for prompt_type in prompt_types:
            formatted = format_user_prompt(prompt_type, base_prompt, data_text)
            assert formatted is not None
            assert isinstance(formatted, str)
            assert base_prompt in formatted
            assert data_text in formatted
    
    def test_invalid_prompt_types(self):
        """测试无效的提示类型"""
        # 测试不存在的系统提示类型
        default_system = get_system_prompt()
        invalid_system = get_system_prompt("invalid_type")
        assert invalid_system == default_system
        
        # 测试不存在的用户提示类型
        default_user = get_user_prompt()
        invalid_user = get_user_prompt("invalid_type")
        assert invalid_user == default_user
        
        # 测试不存在的结果模板类型
        default_template = get_result_template()
        invalid_template = get_result_template("invalid_type")
        assert invalid_template == default_template


class TestEnvironmentLoader:
    """环境变量加载测试"""
    
    def test_get_env(self):
        """测试获取环境变量"""
        # 设置测试环境变量
        os.environ["TEST_VAR"] = "test_value"
        
        # 测试获取存在的变量
        value = get_env("TEST_VAR")
        assert value == "test_value"
        
        # 测试获取不存在的变量，使用默认值
        value = get_env("NONEXISTENT_VAR", "default")
        assert value == "default"
        
        # 测试获取不存在的变量，不使用默认值
        value = get_env("NONEXISTENT_VAR")
        assert value is None
    
    def test_load_env_file(self):
        """测试加载环境变量文件"""
        # 创建测试环境变量文件
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write("TEST_KEY1=value1\n")
            f.write("TEST_KEY2=value2\n")
            f.write("# This is a comment\n")
            f.write("\n")  # 空行
            f.write("TEST_KEY3 = value3\n")  # 带空格
            temp_path = f.name
        
        try:
            # 测试加载文件
            env_vars = load_env_file(temp_path)
            
            # 验证结果
            assert env_vars is not None
            assert isinstance(env_vars, dict)
            assert len(env_vars) == 3
            assert env_vars["TEST_KEY1"] == "value1"
            assert env_vars["TEST_KEY2"] == "value2"
            assert env_vars["TEST_KEY3"] == "value3"
            
            # 测试加载不存在的文件
            nonexistent_vars = load_env_file("/nonexistent/path")
            assert nonexistent_vars == {}
            
        finally:
            # 清理测试文件
            os.unlink(temp_path)


class TestAIModels:
    """AI模型测试"""
    
    def test_ai_analysis_config(self):
        """测试AI分析配置模型"""
        # 创建配置实例
        config = AIAnalysisConfig(
            config_id="test-id",
            config_name="测试配置",
            ai_type=AIType.CLOUD,
            is_default=True,
            cloud_provider="openrouter",
            cloud_model_name="deepseek/deepseek-chat",
            max_tokens=2000,
            temperature=0.5
        )
        
        # 测试基本属性
        assert config.config_id == "test-id"
        assert config.config_name == "测试配置"
        assert config.ai_type == AIType.CLOUD
        assert config.is_default is True
        assert config.cloud_provider == "openrouter"
        assert config.cloud_model_name == "deepseek/deepseek-chat"
        assert config.max_tokens == 2000
        assert config.temperature == 0.5
        
        # 测试显示名称
        assert "测试配置" in config.display_name
        assert AIType.CLOUD.display_name in config.display_name
        
        # 测试转换为字典
        config_dict = config.to_dict()
        assert config_dict is not None
        assert isinstance(config_dict, dict)
        assert config_dict["config_id"] == "test-id"
        assert config_dict["config_name"] == "测试配置"
        assert config_dict["ai_type"] == AIType.CLOUD.value
        assert config_dict["is_default"] is True
        assert config_dict["cloud_provider"] == "openrouter"
        
        # 测试从字典创建
        new_config = AIAnalysisConfig.from_dict(config_dict)
        assert new_config.config_id == config.config_id
        assert new_config.config_name == config.config_name
        assert new_config.ai_type == config.ai_type
        assert new_config.is_default == config.is_default
    
    def test_ai_analysis_result(self):
        """测试AI分析结果模型"""
        # 创建结果实例
        result = AIAnalysisResult(
            analysis_id="test-id",
            snapshot1_id="snapshot1",
            snapshot2_id="snapshot2",
            config_id="config-id",
            analysis_content="这是分析内容",
            analysis_summary="这是摘要",
            investment_advice="这是投资建议",
            risk_assessment="这是风险评估",
            analysis_type="COMPARISON",
            analysis_status="SUCCESS",
            processing_time_ms=1500,
            metadata={"key": "value"}
        )
        
        # 测试基本属性
        assert result.analysis_id == "test-id"
        assert result.snapshot1_id == "snapshot1"
        assert result.snapshot2_id == "snapshot2"
        assert result.config_id == "config-id"
        assert result.analysis_content == "这是分析内容"
        assert result.analysis_summary == "这是摘要"
        assert result.investment_advice == "这是投资建议"
        assert result.risk_assessment == "这是风险评估"
        assert result.analysis_type == "COMPARISON"
        assert result.analysis_status == "SUCCESS"
        assert result.processing_time_ms == 1500
        assert result.metadata == {"key": "value"}
        
        # 测试计算属性
        assert result.is_success is True
        
        # 测试转换为字典
        result_dict = result.to_dict()
        assert result_dict is not None
        assert isinstance(result_dict, dict)
        assert result_dict["analysis_id"] == "test-id"
        assert result_dict["snapshot1_id"] == "snapshot1"
        assert result_dict["analysis_content"] == "这是分析内容"
        assert result_dict["analysis_status"] == "SUCCESS"
        assert result_dict["is_success"] is True
        
        # 测试从字典创建
        new_result = AIAnalysisResult.from_dict(result_dict)
        assert new_result.analysis_id == result.analysis_id
        assert new_result.snapshot1_id == result.snapshot1_id
        assert new_result.analysis_content == result.analysis_content
        assert new_result.analysis_status == result.analysis_status
        assert new_result.is_success == result.is_success


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 