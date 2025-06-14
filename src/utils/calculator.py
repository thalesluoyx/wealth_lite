"""
财务计算器

提供各种财务计算功能，包括年化回报率、复合增长率等。
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional, Union
import math


class Calculator:
    """财务计算器"""
    
    @staticmethod
    def calculate_annualized_return(
        initial_value: Union[Decimal, float], 
        current_value: Union[Decimal, float], 
        start_date: date, 
        end_date: Optional[date] = None
    ) -> float:
        """
        计算年化回报率
        
        公式：年化回报率 = (当前价值/初始投入)^(1/持有年数) - 1
        
        Args:
            initial_value: 初始投入金额
            current_value: 当前价值
            start_date: 开始日期
            end_date: 结束日期，默认为今天
            
        Returns:
            年化回报率（小数形式，如0.1表示10%）
        """
        if end_date is None:
            end_date = date.today()
        
        # 转换为float进行计算
        initial = float(initial_value)
        current = float(current_value)
        
        if initial <= 0:
            return 0.0
        
        # 计算持有年数
        days = (end_date - start_date).days
        if days <= 0:
            return 0.0
        
        years = days / 365.25
        
        # 计算年化回报率
        return (current / initial) ** (1 / years) - 1
    
    @staticmethod
    def calculate_total_return_rate(
        initial_value: Union[Decimal, float], 
        current_value: Union[Decimal, float]
    ) -> float:
        """
        计算总收益率
        
        Args:
            initial_value: 初始投入金额
            current_value: 当前价值
            
        Returns:
            总收益率（小数形式）
        """
        initial = float(initial_value)
        current = float(current_value)
        
        if initial <= 0:
            return 0.0
        
        return (current - initial) / initial
    
    @staticmethod
    def calculate_compound_annual_growth_rate(
        beginning_value: Union[Decimal, float],
        ending_value: Union[Decimal, float],
        years: float
    ) -> float:
        """
        计算复合年增长率(CAGR)
        
        Args:
            beginning_value: 期初价值
            ending_value: 期末价值
            years: 年数
            
        Returns:
            复合年增长率
        """
        if beginning_value <= 0 or years <= 0:
            return 0.0
        
        beginning = float(beginning_value)
        ending = float(ending_value)
        
        return (ending / beginning) ** (1 / years) - 1
    
    @staticmethod
    def calculate_holding_period_return(
        initial_value: Union[Decimal, float],
        current_value: Union[Decimal, float],
        dividends: Union[Decimal, float] = 0
    ) -> float:
        """
        计算持有期收益率
        
        Args:
            initial_value: 初始投入
            current_value: 当前价值
            dividends: 分红收入
            
        Returns:
            持有期收益率
        """
        initial = float(initial_value)
        current = float(current_value)
        div = float(dividends)
        
        if initial <= 0:
            return 0.0
        
        return (current + div - initial) / initial
    
    @staticmethod
    def calculate_sharpe_ratio(
        portfolio_return: float,
        risk_free_rate: float,
        portfolio_std: float
    ) -> float:
        """
        计算夏普比率
        
        Args:
            portfolio_return: 投资组合收益率
            risk_free_rate: 无风险收益率
            portfolio_std: 投资组合标准差
            
        Returns:
            夏普比率
        """
        if portfolio_std <= 0:
            return 0.0
        
        return (portfolio_return - risk_free_rate) / portfolio_std
    
    @staticmethod
    def calculate_portfolio_return(
        assets_data: List[Dict[str, Union[float, Decimal]]]
    ) -> Dict[str, float]:
        """
        计算投资组合收益率
        
        Args:
            assets_data: 资产数据列表，每个元素包含weight(权重)和return(收益率)
            
        Returns:
            包含加权收益率等信息的字典
        """
        if not assets_data:
            return {"weighted_return": 0.0, "total_weight": 0.0}
        
        weighted_return = 0.0
        total_weight = 0.0
        
        for asset in assets_data:
            weight = float(asset.get("weight", 0))
            return_rate = float(asset.get("return", 0))
            
            weighted_return += weight * return_rate
            total_weight += weight
        
        return {
            "weighted_return": weighted_return,
            "total_weight": total_weight,
            "average_return": weighted_return / total_weight if total_weight > 0 else 0.0
        }
    
    @staticmethod
    def calculate_future_value(
        present_value: Union[Decimal, float],
        annual_rate: float,
        years: float,
        compounding_frequency: int = 1
    ) -> float:
        """
        计算未来价值
        
        Args:
            present_value: 现值
            annual_rate: 年利率
            years: 年数
            compounding_frequency: 复利频率（每年复利次数）
            
        Returns:
            未来价值
        """
        pv = float(present_value)
        
        if compounding_frequency <= 0:
            compounding_frequency = 1
        
        # FV = PV * (1 + r/n)^(n*t)
        rate_per_period = annual_rate / compounding_frequency
        total_periods = compounding_frequency * years
        
        return pv * (1 + rate_per_period) ** total_periods
    
    @staticmethod
    def calculate_present_value(
        future_value: Union[Decimal, float],
        annual_rate: float,
        years: float,
        compounding_frequency: int = 1
    ) -> float:
        """
        计算现值
        
        Args:
            future_value: 未来价值
            annual_rate: 年利率
            years: 年数
            compounding_frequency: 复利频率
            
        Returns:
            现值
        """
        fv = float(future_value)
        
        if compounding_frequency <= 0:
            compounding_frequency = 1
        
        # PV = FV / (1 + r/n)^(n*t)
        rate_per_period = annual_rate / compounding_frequency
        total_periods = compounding_frequency * years
        
        return fv / (1 + rate_per_period) ** total_periods
    
    @staticmethod
    def format_percentage(value: float, decimal_places: int = 2) -> str:
        """
        格式化百分比显示
        
        Args:
            value: 小数值（如0.1表示10%）
            decimal_places: 小数位数
            
        Returns:
            格式化的百分比字符串
        """
        return f"{value * 100:.{decimal_places}f}%"
    
    @staticmethod
    def format_currency(
        value: Union[Decimal, float], 
        currency_symbol: str = "¥", 
        decimal_places: int = 2
    ) -> str:
        """
        格式化货币显示
        
        Args:
            value: 金额
            currency_symbol: 货币符号
            decimal_places: 小数位数
            
        Returns:
            格式化的货币字符串
        """
        amount = float(value)
        return f"{currency_symbol}{amount:,.{decimal_places}f}" 