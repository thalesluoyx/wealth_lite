"""
WealthLite 数据持久化层

提供SQLite + JSON混合存储方案：
- SQLite：存储结构化数据（资产、交易、快照）
- JSON：存储扩展属性和复杂对象

核心模块：
- database.py: 数据库连接和基础操作
- repositories.py: 数据访问对象（DAO）
- migrations.py: 数据库迁移管理
- backup.py: 数据备份和恢复
"""

from .database import DatabaseManager
from .repositories import (
    AssetRepository, 
    TransactionRepository, 
    PortfolioSnapshotRepository
)

__all__ = [
    'DatabaseManager',
    'AssetRepository',
    'TransactionRepository', 
    'PortfolioSnapshotRepository'
] 