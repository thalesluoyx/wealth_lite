"""
配置模块

提供系统配置、环境变量加载等功能。
"""

from .env_loader import get_env, load_environment

__all__ = ['get_env', 'load_environment'] 