"""
数据验证器

提供各种数据验证功能。
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Union, Optional
import re


class Validator:
    """数据验证器"""
    
    @staticmethod
    def validate_amount(value: Union[str, int, float, Decimal]) -> bool:
        """
        验证金额是否有效
        
        Args:
            value: 待验证的金额
            
        Returns:
            是否为有效金额
        """
        try:
            amount = Decimal(str(value))
            return amount >= 0
        except (InvalidOperation, ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """
        验证日期字符串是否有效
        
        Args:
            date_str: 日期字符串（YYYY-MM-DD格式）
            
        Returns:
            是否为有效日期
        """
        try:
            date.fromisoformat(date_str)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_asset_name(name: str) -> bool:
        """
        验证资产名称是否有效
        
        Args:
            name: 资产名称
            
        Returns:
            是否为有效资产名称
        """
        if not isinstance(name, str):
            return False
        
        # 去除首尾空格后检查
        name = name.strip()
        
        # 名称不能为空，长度在1-100字符之间
        if not name or len(name) > 100:
            return False
        
        # 不能包含特殊字符
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        return not any(char in name for char in invalid_chars) 