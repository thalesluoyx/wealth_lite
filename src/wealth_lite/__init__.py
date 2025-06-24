"""
WealthLite - 个人财富管理系统

一个专注于投资组合管理的轻量级工具，采用交易驱动的架构设计。
"""

__version__ = "0.2.0"
__author__ = "WealthLite Team"
__description__ = "Personal Wealth Management System - Transaction-Driven Architecture"

# 导出主要模块
from . import models
from . import config
from . import data
from . import utils

__all__ = ["models", "config", "data", "utils"] 