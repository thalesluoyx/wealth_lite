"""
数据库配置模块

根据环境变量自动选择合适的数据库配置。
支持生产环境、开发环境和测试环境的自动切换。
"""

import os
from pathlib import Path
from typing import Optional


class DatabaseConfig:
    """数据库配置管理器"""
    
    # 环境类型
    PRODUCTION = "production"
    DEVELOPMENT = "development" 
    TEST = "test"
    
    @classmethod
    def get_environment(cls) -> str:
        """获取当前环境"""
        return os.getenv('WEALTH_LITE_ENV', cls.DEVELOPMENT)
    
    @classmethod
    def get_db_path(cls, env: Optional[str] = None) -> str:
        """
        根据环境获取数据库路径
        
        Args:
            env: 环境类型，如果不指定则从环境变量获取
            
        Returns:
            数据库路径字符串
        """
        env = env or cls.get_environment()
        
        if env == cls.TEST:
            # 测试环境使用内存数据库
            return ":memory:"
        elif env == cls.DEVELOPMENT:
            # 开发环境使用开发数据库
            user_data_dir = Path("user_data")
            user_data_dir.mkdir(exist_ok=True)
            return str(user_data_dir / "wealth_lite_dev.db")
        elif env == cls.PRODUCTION:
            # 生产环境使用生产数据库
            user_data_dir = Path("user_data")
            user_data_dir.mkdir(exist_ok=True)
            return str(user_data_dir / "wealth_lite.db")
        else:
            raise ValueError(f"未知的环境类型: {env}")
    
    @classmethod
    def is_memory_db(cls, env: Optional[str] = None) -> bool:
        """判断是否为内存数据库"""
        env = env or cls.get_environment()
        return env == cls.TEST
    
    @classmethod
    def is_test_environment(cls) -> bool:
        """判断是否为测试环境"""
        return cls.get_environment() == cls.TEST
    
    @classmethod
    def is_development_environment(cls) -> bool:
        """判断是否为开发环境"""
        return cls.get_environment() == cls.DEVELOPMENT
    
    @classmethod
    def is_production_environment(cls) -> bool:
        """判断是否为生产环境"""
        return cls.get_environment() == cls.PRODUCTION