"""
数据访问对象 (Repository) - 实现数据持久化的具体操作

该模块实现Repository模式，为业务层提供清晰的数据访问接口，
封装所有数据库操作细节，支持事务管理和数据一致性。
"""

import json
import sqlite3
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
import logging

from ..models.asset import Asset
from ..models.transaction import (
    BaseTransaction, CashTransaction, FixedIncomeTransaction,
    EquityTransaction, RealEstateTransaction
)
from ..models.position import Position
from ..models.portfolio import Portfolio, PortfolioSnapshot
from ..models.enums import AssetType, TransactionType, Currency, AssetSubType
from .database import DatabaseManager


class AssetRepository:
    """资产数据访问对象"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create(self, asset: Asset) -> bool:
        """创建资产记录"""
        try:
            query = """
                INSERT INTO assets (
                    asset_id, asset_name, asset_type, asset_subtype,
                    currency, description, issuer, 
                    credit_rating, extended_attributes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                asset.asset_id,
                asset.asset_name,
                asset.asset_type.name,  # 使用英文名称而不是中文值
                asset.asset_subtype.name if asset.asset_subtype else None,
                asset.currency.name,    # 使用英文名称而不是中文值
                asset.description,
                asset.issuer,
                asset.credit_rating,
                json.dumps(asset.extended_attributes) if asset.extended_attributes else None
            )
            logging.debug(f"[AssetRepository.create] SQL: {query.strip()} | params: {params}")
            self.db.execute_insert(query, params)
            logging.info(f"[AssetRepository.create] 资产插入成功: {asset.asset_id}")
            return True
        except Exception as e:
            logging.error(f"[AssetRepository.create] 创建资产失败: {e}", exc_info=True)
            return False
    
    def get_by_id(self, asset_id: str) -> Optional[Asset]:
        """根据ID获取资产"""
        query = "SELECT * FROM assets WHERE asset_id = ?"
        results = self.db.execute_query(query, (asset_id,))
        
        if not results:
            return None
            
        row = results[0]
        return self._row_to_asset(row)
    
    def get_by_type(self, asset_type: AssetType) -> List[Asset]:
        """根据资产类型获取资产列表"""
        query = "SELECT * FROM assets WHERE asset_type = ? ORDER BY asset_name"
        results = self.db.execute_query(query, (asset_type.name,))  # 使用英文名称
        
        return [self._row_to_asset(row) for row in results]
    
    def get_by_name(self, asset_name: str) -> Optional[Asset]:
        """根据资产名称获取资产"""
        query = "SELECT * FROM assets WHERE asset_name = ?"
        results = self.db.execute_query(query, (asset_name,))
        
        if not results:
            return None
            
        row = results[0]
        return self._row_to_asset(row)
    
    def exists_by_name(self, asset_name: str) -> bool:
        """检查资产名称是否已存在"""
        query = "SELECT COUNT(*) as count FROM assets WHERE asset_name = ?"
        results = self.db.execute_query(query, (asset_name,))
        return results[0]['count'] > 0
    
    def get_all(self) -> List[Asset]:
        """获取所有资产"""
        query = "SELECT * FROM assets ORDER BY asset_type, asset_name"
        results = self.db.execute_query(query)
        
        return [self._row_to_asset(row) for row in results]
    
    def update(self, asset: Asset) -> bool:
        """更新资产信息"""
        try:
            query = """
                UPDATE assets SET 
                    asset_name = ?, asset_type = ?, asset_subtype = ?,
                    currency = ?, description = ?,
                    issuer = ?, credit_rating = ?, extended_attributes = ?,
                    updated_date = CURRENT_TIMESTAMP
                WHERE asset_id = ?
            """
            params = (
                asset.asset_name,
                asset.asset_type.name,  # 使用英文名称而不是中文值
                asset.asset_subtype.name if asset.asset_subtype else None,
                asset.currency.name,    # 使用英文名称而不是中文值
                asset.description,
                asset.issuer,
                asset.credit_rating,
                json.dumps(asset.extended_attributes) if asset.extended_attributes else None,
                asset.asset_id
            )
            
            rows_affected = self.db.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            print(f"更新资产失败: {e}")
            return False
    
    def delete(self, asset_id: str) -> bool:
        """删除资产（软删除，检查是否有关联交易）"""
        # 检查是否有关联的交易记录
        check_query = "SELECT COUNT(*) as count FROM transactions WHERE asset_id = ?"
        result = self.db.execute_query(check_query, (asset_id,))
        
        if result[0]['count'] > 0:
            print(f"无法删除资产 {asset_id}：存在关联的交易记录")
            return False
        
        try:
            query = "DELETE FROM assets WHERE asset_id = ?"
            rows_affected = self.db.execute_update(query, (asset_id,))
            return rows_affected > 0
            
        except Exception as e:
            print(f"删除资产失败: {e}")
            return False
    
    def _row_to_asset(self, row: sqlite3.Row) -> Asset:
        """将数据库行转换为Asset对象"""
        extended_attrs = None
        if row['extended_attributes']:
            extended_attrs = json.loads(row['extended_attributes'])
        
        # 处理资产子类型
        asset_subtype = None
        try:
            if row['asset_subtype']:
                try:
                    asset_subtype = AssetSubType[row['asset_subtype']]
                except KeyError:
                    logging.warning(f"未知的资产子类型: {row['asset_subtype']}")
        except (KeyError, IndexError):
            # 如果字段不存在（旧数据），设为None
            asset_subtype = None
            
        return Asset(
            asset_id=row['asset_id'],
            asset_name=row['asset_name'],
            asset_type=AssetType[row['asset_type']],  # 使用英文名称查找枚举
            asset_subtype=asset_subtype,
            currency=Currency[row['currency']],      # 使用英文名称查找枚举
            description=row['description'],
            issuer=row['issuer'],
            credit_rating=row['credit_rating'],
            extended_attributes=extended_attrs
        )


class TransactionRepository:
    """交易数据访问对象"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create(self, transaction: BaseTransaction) -> bool:
        """创建交易记录"""
        try:
            with self.db.transaction() as conn:
                # 插入主交易记录
                main_query = """
                    INSERT INTO transactions (
                        transaction_id, asset_id, transaction_date, transaction_type,
                        amount, currency, exchange_rate, amount_base_currency, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                main_params = (
                    transaction.transaction_id,
                    transaction.asset_id,
                    transaction.transaction_date.isoformat(),
                    transaction.transaction_type.name,  # 使用英文名称
                    float(transaction.amount),
                    transaction.currency.name,          # 使用英文名称
                    float(transaction.exchange_rate),
                    float(transaction.amount_base_currency),
                    transaction.notes
                )
                
                conn.execute(main_query, main_params)
                
                # 插入特定类型的详情记录
                self._create_transaction_details(conn, transaction)
                
            return True
            
        except Exception as e:
            print(f"创建交易失败: {e}")
            return False
    
    def get_by_id(self, transaction_id: str) -> Optional[BaseTransaction]:
        """根据ID获取交易"""
        query = "SELECT * FROM transactions WHERE transaction_id = ?"
        results = self.db.execute_query(query, (transaction_id,))
        
        if not results:
            return None
            
        row = results[0]
        return self._row_to_transaction(row)
    
    def get_by_asset(self, asset_id: str) -> List[BaseTransaction]:
        """获取指定资产的所有交易"""
        query = """
            SELECT * FROM transactions 
            WHERE asset_id = ? 
            ORDER BY transaction_date DESC, created_date DESC
        """
        results = self.db.execute_query(query, (asset_id,))
        
        return [self._row_to_transaction(row) for row in results]
    
    def get_by_date_range(self, start_date: date, end_date: date) -> List[BaseTransaction]:
        """获取指定日期范围内的交易"""
        query = """
            SELECT * FROM transactions 
            WHERE transaction_date BETWEEN ? AND ?
            ORDER BY transaction_date DESC, created_date DESC
        """
        results = self.db.execute_query(query, (start_date.isoformat(), end_date.isoformat()))
        
        return [self._row_to_transaction(row) for row in results]
    
    def get_all(self) -> List[BaseTransaction]:
        """获取所有交易"""
        query = "SELECT * FROM transactions ORDER BY transaction_date DESC, created_date DESC"
        results = self.db.execute_query(query)
        
        return [self._row_to_transaction(row) for row in results]
    
    def get_recent(self, limit: int = 50) -> List[BaseTransaction]:
        """获取最近N条交易，按交易日期倒序"""
        query = "SELECT * FROM transactions ORDER BY transaction_date DESC, created_date DESC LIMIT ?"
        results = self.db.execute_query(query, (limit,))
        return [self._row_to_transaction(row) for row in results]
    
    def update(self, transaction: BaseTransaction) -> bool:
        """更新交易记录"""
        try:
            with self.db.transaction() as conn:
                # 更新主交易记录
                main_query = """
                    UPDATE transactions SET 
                        asset_id = ?, transaction_date = ?, transaction_type = ?,
                        amount = ?, currency = ?, exchange_rate = ?, 
                        amount_base_currency = ?, notes = ?
                    WHERE transaction_id = ?
                """
                main_params = (
                    transaction.asset_id,
                    transaction.transaction_date.isoformat(),
                    transaction.transaction_type.name,  # 使用英文名称
                    float(transaction.amount),
                    transaction.currency.name,          # 使用英文名称
                    float(transaction.exchange_rate),
                    float(transaction.amount_base_currency),
                    transaction.notes,
                    transaction.transaction_id
                )
                
                conn.execute(main_query, main_params)
                
                # 更新特定类型的详情记录
                self._update_transaction_details(conn, transaction)
                
            return True
            
        except Exception as e:
            print(f"更新交易失败: {e}")
            return False
    
    def delete(self, transaction_id: str) -> bool:
        """删除交易记录"""
        try:
            with self.db.transaction() as conn:
                # 删除详情记录
                detail_tables = [
                    'cash_transactions',
                    'fixed_income_transactions', 
                    'equity_transactions',
                    'real_estate_transactions'
                ]
                for table in detail_tables:
                    conn.execute(f"DELETE FROM {table} WHERE transaction_id = ?", (transaction_id,))
                # 删除主记录
                cur = conn.execute("DELETE FROM transactions WHERE transaction_id = ?", (transaction_id,))
                if cur.rowcount == 0:
                    return False
            return True
        except Exception as e:
            print(f"删除交易失败: {e}")
            return False
    
    def _create_transaction_details(self, conn: sqlite3.Connection, transaction: BaseTransaction):
        """创建交易详情记录"""
        if isinstance(transaction, CashTransaction):
            query = """
                INSERT INTO cash_transactions (
                    transaction_id, account_type, interest_rate, compound_frequency
                ) VALUES (?, ?, ?, ?)
            """
            params = (
                transaction.transaction_id,
                transaction.account_type,
                float(transaction.interest_rate) if transaction.interest_rate else None,
                transaction.compound_frequency if transaction.compound_frequency else None
            )
            conn.execute(query, params)
            
        elif isinstance(transaction, FixedIncomeTransaction):
            query = """
                INSERT INTO fixed_income_transactions (
                    transaction_id, annual_rate, start_date, maturity_date,
                    interest_type, payment_frequency, face_value, coupon_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                transaction.transaction_id,
                float(transaction.annual_rate) if transaction.annual_rate else None,
                transaction.start_date.isoformat() if transaction.start_date else None,
                transaction.maturity_date.isoformat() if transaction.maturity_date else None,
                transaction.interest_type if transaction.interest_type else None,
                transaction.payment_frequency if transaction.payment_frequency else None,
                float(transaction.face_value) if transaction.face_value else None,
                float(transaction.coupon_rate) if transaction.coupon_rate else None
            )
            conn.execute(query, params)
    
    def _update_transaction_details(self, conn: sqlite3.Connection, transaction: BaseTransaction):
        """更新交易详情记录"""
        # 先删除旧的详情记录，再插入新的
        detail_tables = [
            'cash_transactions',
            'fixed_income_transactions', 
            'equity_transactions',
            'real_estate_transactions'
        ]
        
        for table in detail_tables:
            conn.execute(f"DELETE FROM {table} WHERE transaction_id = ?", (transaction.transaction_id,))
        
        # 重新创建详情记录
        self._create_transaction_details(conn, transaction)
    
    def _row_to_transaction(self, row: sqlite3.Row) -> BaseTransaction:
        """将数据库行转换为Transaction对象"""
        # 根据交易类型确定具体的Transaction子类
        transaction_type = TransactionType[row['transaction_type']]  # 使用英文名称查找枚举
        
        # 基础参数
        base_params = {
            'transaction_id': row['transaction_id'],
            'asset_id': row['asset_id'],
            'transaction_date': datetime.fromisoformat(row['transaction_date']).date(),
            'transaction_type': transaction_type,
            'amount': Decimal(str(row['amount'])),
            'currency': Currency[row['currency']],  # 使用英文名称查找枚举
            'exchange_rate': Decimal(str(row['exchange_rate'])),
            'notes': row['notes']
        }
        
        # 先检查是否有固定收益详情，如果有则创建FixedIncomeTransaction
        fixed_income_details = self._get_fixed_income_details(row['transaction_id'])
        if fixed_income_details:
            return self._create_fixed_income_transaction(base_params, fixed_income_details)
        
        # 检查是否有现金交易详情，如果有则创建CashTransaction
        cash_details = self._get_cash_details(row['transaction_id'])
        if cash_details:
            return self._create_cash_transaction(base_params)
        
        # 如果没有详情表记录，根据交易类型创建默认对象
        if transaction_type in [TransactionType.DEPOSIT, TransactionType.WITHDRAW, TransactionType.INTEREST]:
            return self._create_cash_transaction(base_params)
        
        # 默认返回现金交易对象
        return self._create_cash_transaction(base_params)
    
    def _create_cash_transaction(self, base_params: Dict) -> CashTransaction:
        """创建现金交易对象"""
        details = self._get_cash_details(base_params['transaction_id'])
        
        if details:
            base_params.update({
                'account_type': details.get('account_type'),
                'interest_rate': Decimal(str(details['interest_rate'])) if details.get('interest_rate') else None,
                'compound_frequency': details.get('compound_frequency')
            })
        
        return CashTransaction(**base_params)
    
    def _create_fixed_income_transaction(self, base_params: Dict, details: Dict) -> FixedIncomeTransaction:
        """创建固定收益交易对象"""
        base_params.update({
            'annual_rate': Decimal(str(details['annual_rate'])) if details.get('annual_rate') else None,
            'start_date': datetime.fromisoformat(details['start_date']).date() if details.get('start_date') else None,
            'maturity_date': datetime.fromisoformat(details['maturity_date']).date() if details.get('maturity_date') else None,
            'interest_type': details.get('interest_type'),
            'payment_frequency': details.get('payment_frequency'),
            'face_value': Decimal(str(details['face_value'])) if details.get('face_value') else None,
            'coupon_rate': Decimal(str(details['coupon_rate'])) if details.get('coupon_rate') else None
        })
        
        return FixedIncomeTransaction(**base_params)
    
    def _get_cash_details(self, transaction_id: str) -> Optional[Dict]:
        """获取现金交易详情"""
        query = "SELECT * FROM cash_transactions WHERE transaction_id = ?"
        results = self.db.execute_query(query, (transaction_id,))
        return dict(results[0]) if results else None
    
    def _get_fixed_income_details(self, transaction_id: str) -> Optional[Dict]:
        """获取固定收益交易详情"""
        query = "SELECT * FROM fixed_income_transactions WHERE transaction_id = ?"
        results = self.db.execute_query(query, (transaction_id,))
        return dict(results[0]) if results else None


class PortfolioSnapshotRepository:
    """投资组合快照数据访问对象"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create(self, snapshot: PortfolioSnapshot) -> bool:
        """创建投资组合快照"""
        try:
            query = """
                INSERT INTO portfolio_snapshots (
                    snapshot_id, snapshot_date, base_currency, description,
                    total_value, total_cost, total_return, return_rate,
                    asset_allocation, performance_metrics, position_snapshots
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                snapshot.snapshot_id,
                snapshot.snapshot_date.isoformat(),
                snapshot.base_currency.name,  # 使用英文名称
                snapshot.description,
                float(snapshot.total_value),
                float(snapshot.total_cost),
                float(snapshot.total_return),
                float(snapshot.return_rate),
                json.dumps(snapshot.asset_allocation, default=str),
                json.dumps(snapshot.performance_metrics, default=str),
                json.dumps(snapshot.position_snapshots, default=str)
            )
            
            self.db.execute_insert(query, params)
            return True
            
        except Exception as e:
            print(f"创建投资组合快照失败: {e}")
            return False
    
    def get_by_id(self, snapshot_id: str) -> Optional[PortfolioSnapshot]:
        """根据ID获取快照"""
        query = "SELECT * FROM portfolio_snapshots WHERE snapshot_id = ?"
        results = self.db.execute_query(query, (snapshot_id,))
        
        if not results:
            return None
            
        return self._row_to_snapshot(results[0])
    
    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[PortfolioSnapshot]:
        """获取指定日期范围内的快照"""
        query = """
            SELECT * FROM portfolio_snapshots 
            WHERE snapshot_date BETWEEN ? AND ?
            ORDER BY snapshot_date DESC
        """
        results = self.db.execute_query(query, (start_date.isoformat(), end_date.isoformat()))
        
        return [self._row_to_snapshot(row) for row in results]
    
    def get_latest(self, limit: int = 10) -> List[PortfolioSnapshot]:
        """获取最新的快照列表"""
        query = """
            SELECT * FROM portfolio_snapshots 
            ORDER BY snapshot_date DESC 
            LIMIT ?
        """
        results = self.db.execute_query(query, (limit,))
        
        return [self._row_to_snapshot(row) for row in results]
    
    def delete(self, snapshot_id: str) -> bool:
        """删除快照（检查是否为不可变）"""
        # 检查快照是否为不可变
        check_query = "SELECT is_immutable FROM portfolio_snapshots WHERE snapshot_id = ?"
        result = self.db.execute_query(check_query, (snapshot_id,))
        
        if result and result[0]['is_immutable']:
            print(f"无法删除快照 {snapshot_id}：快照为不可变状态")
            return False
        
        try:
            query = "DELETE FROM portfolio_snapshots WHERE snapshot_id = ?"
            rows_affected = self.db.execute_update(query, (snapshot_id,))
            return rows_affected > 0
            
        except Exception as e:
            print(f"删除快照失败: {e}")
            return False
    
    def _row_to_snapshot(self, row: sqlite3.Row) -> PortfolioSnapshot:
        """将数据库行转换为PortfolioSnapshot对象"""
        position_snapshots = []
        if row['position_snapshots']:
            position_data = json.loads(row['position_snapshots'])
            # 这里需要重新构建Position对象，暂时简化处理
            position_snapshots = position_data
        
        return PortfolioSnapshot(
            snapshot_id=row['snapshot_id'],
            snapshot_date=datetime.fromisoformat(row['snapshot_date']),
            base_currency=Currency[row['base_currency']],  # 使用英文名称查找枚举
            description=row['description'],
            total_value=Decimal(str(row['total_value'])),
            total_cost=Decimal(str(row['total_cost'])),
            total_return=Decimal(str(row['total_return'])),
            return_rate=Decimal(str(row['return_rate'])),
            asset_allocation=json.loads(row['asset_allocation']),
            performance_metrics=json.loads(row['performance_metrics']),
            position_snapshots=position_snapshots
        )


class RepositoryManager:
    """数据访问对象管理器 - 统一管理所有Repository"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
        # 初始化各个Repository
        self.assets = AssetRepository(db_manager)
        self.transactions = TransactionRepository(db_manager)
        self.snapshots = PortfolioSnapshotRepository(db_manager)
    
    def close(self):
        """关闭数据库连接"""
        self.db_manager.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 