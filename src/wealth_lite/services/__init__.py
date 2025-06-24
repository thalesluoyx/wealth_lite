"""
服务层 - 业务逻辑层

该层封装核心业务逻辑，协调数据访问层和应用层之间的交互。
提供高层次的业务操作接口，确保业务规则的一致性。
"""

from .wealth_service import WealthService

__all__ = ['WealthService'] 