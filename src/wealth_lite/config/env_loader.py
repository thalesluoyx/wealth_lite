"""
环境变量加载工具

提供从.env文件加载环境变量的功能，支持开发和生产环境。
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def load_env_file(file_path: str) -> Dict[str, str]:
    """
    从.env文件加载环境变量
    
    Args:
        file_path: .env文件路径
        
    Returns:
        环境变量字典
    """
    env_vars = {}
    
    if not os.path.exists(file_path):
        logger.warning(f"环境配置文件不存在: {file_path}")
        return env_vars
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith("#"):
                    continue
                    
                # 解析KEY=VALUE格式
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        logger.error(f"加载环境配置文件失败: {e}")
    
    return env_vars

def load_environment() -> Dict[str, str]:
    """
    根据当前环境加载对应的.env文件
    
    Returns:
        环境变量字典
    """
    # 获取项目根目录
    root_dir = Path(__file__).parent.parent.parent.parent
    
    # 首先加载基础.env文件
    base_env_path = os.path.join(root_dir, ".env")
    env_vars = load_env_file(base_env_path)
    
    # 根据WEALTH_LITE_ENV确定环境
    env_name = os.environ.get("WEALTH_LITE_ENV") or env_vars.get("WEALTH_LITE_ENV", "development")
    
    # 加载特定环境的.env文件
    env_file_path = os.path.join(root_dir, f".env.{env_name}")
    specific_env_vars = load_env_file(env_file_path)
    
    # 合并环境变量，特定环境的变量优先级更高
    env_vars.update(specific_env_vars)
    
    # 将环境变量设置到os.environ
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
    
    logger.info(f"已加载{env_name}环境配置")
    return env_vars

def get_env(key: str, default: Any = None) -> Optional[str]:
    """
    获取环境变量值
    
    Args:
        key: 环境变量名
        default: 默认值
        
    Returns:
        环境变量值或默认值
    """
    return os.environ.get(key, default)

# 在模块导入时自动加载环境变量
environment = load_environment() 