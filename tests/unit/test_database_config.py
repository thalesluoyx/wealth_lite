"""
测试数据库配置功能
"""

import pytest
import os
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wealth_lite.config.database_config import DatabaseConfig


class TestDatabaseConfig:
    """测试数据库配置"""
    
    def test_default_environment_is_development(self):
        """测试默认环境是开发环境"""
        # 清理环境变量
        if 'WEALTH_LITE_ENV' in os.environ:
            del os.environ['WEALTH_LITE_ENV']
        
        assert DatabaseConfig.get_environment() == DatabaseConfig.DEVELOPMENT
        assert DatabaseConfig.is_development_environment() == True
        assert DatabaseConfig.is_test_environment() == False
        assert DatabaseConfig.is_production_environment() == False
    
    def test_test_environment_uses_memory_db(self):
        """测试测试环境使用内存数据库"""
        os.environ['WEALTH_LITE_ENV'] = 'test'
        
        try:
            assert DatabaseConfig.get_environment() == DatabaseConfig.TEST
            assert DatabaseConfig.get_db_path() == ":memory:"
            assert DatabaseConfig.is_memory_db() == True
            assert DatabaseConfig.is_test_environment() == True
        finally:
            del os.environ['WEALTH_LITE_ENV']
    
    def test_development_environment_uses_dev_db(self):
        """测试开发环境使用开发数据库"""
        os.environ['WEALTH_LITE_ENV'] = 'development'
        
        try:
            assert DatabaseConfig.get_environment() == DatabaseConfig.DEVELOPMENT
            db_path = DatabaseConfig.get_db_path()
            assert "wealth_lite_dev.db" in db_path
            assert DatabaseConfig.is_memory_db() == False
            assert DatabaseConfig.is_development_environment() == True
        finally:
            del os.environ['WEALTH_LITE_ENV']
    
    def test_production_environment_uses_prod_db(self):
        """测试生产环境使用生产数据库"""
        os.environ['WEALTH_LITE_ENV'] = 'production'
        
        try:
            assert DatabaseConfig.get_environment() == DatabaseConfig.PRODUCTION
            db_path = DatabaseConfig.get_db_path()
            assert "wealth_lite.db" in db_path
            assert "wealth_lite_dev.db" not in db_path
            assert DatabaseConfig.is_memory_db() == False
            assert DatabaseConfig.is_production_environment() == True
        finally:
            del os.environ['WEALTH_LITE_ENV']
    
    def test_explicit_environment_parameter(self):
        """测试显式传入环境参数"""
        # 设置一个环境变量
        os.environ['WEALTH_LITE_ENV'] = 'development'
        
        try:
            # 显式传入test环境，应该覆盖环境变量
            assert DatabaseConfig.get_db_path(env='test') == ":memory:"
            assert DatabaseConfig.is_memory_db(env='test') == True
            
            # 显式传入production环境
            prod_path = DatabaseConfig.get_db_path(env='production')
            assert "wealth_lite.db" in prod_path
            assert DatabaseConfig.is_memory_db(env='production') == False
        finally:
            del os.environ['WEALTH_LITE_ENV']
    
    def test_invalid_environment_raises_error(self):
        """测试无效环境抛出错误"""
        with pytest.raises(ValueError, match="未知的环境类型"):
            DatabaseConfig.get_db_path(env='invalid_env')