"""
财富管理服务 - 核心业务逻辑服务

该服务整合了资产管理、交易处理、持仓计算和投资组合分析的完整业务流程，
为上层应用提供统一的业务接口。
"""

import uuid
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal
import logging

from ..models.asset import Asset
from ..models.transaction import BaseTransaction, CashTransaction, FixedIncomeTransaction
from ..models.position import Position
from ..models.portfolio import Portfolio, PortfolioSnapshot
from ..models.enums import AssetType, TransactionType, Currency
from ..data.database import DatabaseManager
from ..data.repositories import RepositoryManager


class WealthService:
    """财富管理核心服务"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化财富管理服务
        
        Args:
            db_path: 数据库文件路径，如果不指定则根据环境变量自动选择
                    - 测试环境：使用内存数据库
                    - 开发环境：使用开发数据库
                    - 生产环境：使用生产数据库
        """
        self.db_manager = DatabaseManager(db_path)
        self.repositories = RepositoryManager(self.db_manager)
    
    # ==================== 资产管理 ====================
    
    def create_asset(
        self,
        asset_name: str,
        asset_type: AssetType,
        primary_category: str,
        secondary_category: str,
        currency: Currency = Currency.CNY,
        description: Optional[str] = None,
        issuer: Optional[str] = None,
        credit_rating: Optional[str] = None,
        **extended_attributes
    ) -> Asset:
        """
        创建新资产
        
        Args:
            asset_name: 资产名称
            asset_type: 资产类型
            primary_category: 一级分类
            secondary_category: 二级分类
            currency: 计价货币
            description: 描述
            issuer: 发行方
            credit_rating: 信用评级
            **extended_attributes: 扩展属性
            
        Returns:
            创建的资产对象
            
        Raises:
            ValueError: 参数验证失败
            RuntimeError: 数据库操作失败
        """
        logging.debug(f"[create_asset] 参数: name={asset_name}, type={asset_type}, primary={primary_category}, secondary={secondary_category}, currency={currency}, desc={description}, issuer={issuer}, credit={credit_rating}, ext={extended_attributes}")
        
        # 验证资产名称不能为空
        if not asset_name or not asset_name.strip():
            raise ValueError("资产名称不能为空")
        
        # 验证资产名称是否已存在
        if self.repositories.assets.exists_by_name(asset_name.strip()):
            raise ValueError(f"资产名称已存在: {asset_name}")
        
        # 创建资产对象
        asset = Asset(
            asset_name=asset_name.strip(),
            asset_type=asset_type,
            primary_category=primary_category,
            secondary_category=secondary_category,
            currency=currency,
            description=description,
            issuer=issuer,
            credit_rating=credit_rating,
            extended_attributes=extended_attributes if extended_attributes else None
        )
        logging.info(f"[create_asset] 创建资产对象: {asset}")
        
        # 保存到数据库
        try:
            result = self.repositories.assets.create(asset)
            if not result:
                logging.error(f"[create_asset] 保存资产到数据库失败: {asset_name}")
                raise RuntimeError(f"创建资产失败: {asset_name}")
            logging.info(f"[create_asset] 资产已保存到数据库: {asset.asset_id}")
        except Exception as e:
            logging.error(f"[create_asset] 资产保存异常: {e}", exc_info=True)
            raise
        
        return asset
    
    def get_asset(self, asset_id: str) -> Optional[Asset]:
        """根据ID获取资产"""
        return self.repositories.assets.get_by_id(asset_id)
    
    def get_assets_by_type(self, asset_type: AssetType) -> List[Asset]:
        """根据类型获取资产列表"""
        return self.repositories.assets.get_by_type(asset_type)
    
    def get_all_assets(self) -> List[Asset]:
        """获取所有资产"""
        return self.repositories.assets.get_all()
    
    def update_asset(self, asset: Asset) -> bool:
        """更新资产信息"""
        return self.repositories.assets.update(asset)
    
    def delete_asset(self, asset_id: str) -> bool:
        """删除资产"""
        return self.repositories.assets.delete(asset_id)
    
    # ==================== 交易管理 ====================
    
    def create_cash_transaction(
        self,
        asset_id: str,
        transaction_type: TransactionType,
        amount: Decimal,
        transaction_date: date,
        currency: Currency = Currency.CNY,
        exchange_rate: Decimal = Decimal('1.0'),
        account_type: Optional[str] = None,
        interest_rate: Optional[Decimal] = None,
        compound_frequency: Optional[str] = None,
        notes: Optional[str] = None
    ) -> CashTransaction:
        """
        创建现金类交易
        
        Args:
            asset_id: 资产ID
            transaction_type: 交易类型
            amount: 交易金额
            transaction_date: 交易日期
            currency: 交易货币
            exchange_rate: 汇率
            account_type: 账户类型
            interest_rate: 利率
            compound_frequency: 复利频率
            notes: 备注
            
        Returns:
            创建的交易对象
        """
        # 验证资产是否存在
        asset = self.get_asset(asset_id)
        if not asset:
            raise ValueError(f"资产不存在: {asset_id}")
        
        if asset.asset_type != AssetType.CASH:
            raise ValueError(f"资产类型不匹配，期望: {AssetType.CASH}, 实际: {asset.asset_type}")
        
        # 创建交易对象
        transaction = CashTransaction(
            asset_id=asset_id,
            transaction_type=transaction_type,
            amount=amount,
            transaction_date=transaction_date,
            currency=currency,
            exchange_rate=exchange_rate,
            account_type=account_type,
            interest_rate=interest_rate,
            compound_frequency=compound_frequency,
            notes=notes
        )
        
        # 保存到数据库
        if not self.repositories.transactions.create(transaction):
            raise RuntimeError(f"创建交易失败: {transaction.transaction_id}")
        
        return transaction
    
    def create_fixed_income_transaction(
        self,
        asset_id: str,
        transaction_type: TransactionType,
        amount: Decimal,
        transaction_date: date,
        currency: Currency = Currency.CNY,
        exchange_rate: Decimal = Decimal('1.0'),
        annual_rate: Optional[Decimal] = None,
        start_date: Optional[date] = None,
        maturity_date: Optional[date] = None,
        interest_type: Optional[str] = None,
        payment_frequency: Optional[str] = None,
        face_value: Optional[Decimal] = None,
        coupon_rate: Optional[Decimal] = None,
        notes: Optional[str] = None
    ) -> FixedIncomeTransaction:
        """
        创建固定收益类交易
        
        Args:
            asset_id: 资产ID
            transaction_type: 交易类型
            amount: 交易金额
            transaction_date: 交易日期
            currency: 交易货币
            exchange_rate: 汇率
            annual_rate: 年化收益率
            start_date: 起息日期
            maturity_date: 到期日期
            interest_type: 利息类型
            payment_frequency: 付息频率
            face_value: 面值
            coupon_rate: 票面利率
            notes: 备注
            
        Returns:
            创建的交易对象
        """
        # 验证资产是否存在
        asset = self.get_asset(asset_id)
        if not asset:
            raise ValueError(f"资产不存在: {asset_id}")
        
        if asset.asset_type != AssetType.FIXED_INCOME:
            raise ValueError(f"资产类型不匹配，期望: {AssetType.FIXED_INCOME}, 实际: {asset.asset_type}")
        
        # 创建交易对象
        transaction = FixedIncomeTransaction(
            asset_id=asset_id,
            transaction_type=transaction_type,
            amount=amount,
            transaction_date=transaction_date,
            currency=currency,
            exchange_rate=exchange_rate,
            annual_rate=annual_rate,
            start_date=start_date,
            maturity_date=maturity_date,
            interest_type=interest_type,
            payment_frequency=payment_frequency,
            face_value=face_value,
            coupon_rate=coupon_rate,
            notes=notes
        )
        
        # 保存到数据库
        if not self.repositories.transactions.create(transaction):
            raise RuntimeError(f"创建交易失败: {transaction.transaction_id}")
        
        return transaction
    
    def get_transaction(self, transaction_id: str) -> Optional[BaseTransaction]:
        """根据ID获取交易"""
        return self.repositories.transactions.get_by_id(transaction_id)
    
    def get_transactions_by_asset(self, asset_id: str) -> List[BaseTransaction]:
        """获取指定资产的所有交易"""
        return self.repositories.transactions.get_by_asset(asset_id)
    
    def get_transactions_by_date_range(self, start_date: date, end_date: date) -> List[BaseTransaction]:
        """获取指定日期范围内的交易"""
        return self.repositories.transactions.get_by_date_range(start_date, end_date)
    
    def get_all_transactions(self) -> List[BaseTransaction]:
        """获取所有交易"""
        return self.repositories.transactions.get_all()
    
    def update_transaction(self, transaction: BaseTransaction) -> bool:
        """更新交易"""
        return self.repositories.transactions.update(transaction)
    
    def delete_transaction(self, transaction_id: str) -> bool:
        """删除交易"""
        return self.repositories.transactions.delete(transaction_id)
    
    # ==================== 持仓管理 ====================
    
    def get_position(self, asset_id: str) -> Optional[Position]:
        """
        获取指定资产的持仓信息
        
        Args:
            asset_id: 资产ID
            
        Returns:
            持仓对象，如果没有交易记录则返回None
        """
        # 获取资产信息
        asset = self.get_asset(asset_id)
        if not asset:
            return None
        
        # 获取所有交易记录
        transactions = self.get_transactions_by_asset(asset_id)
        if not transactions:
            return None
        
        # 创建持仓对象
        return Position(asset=asset, transactions=transactions)
    
    def get_all_positions(self) -> List[Position]:
        """
        获取所有持仓信息
        
        Returns:
            持仓列表
        """
        positions = []
        assets = self.get_all_assets()
        
        for asset in assets:
            position = self.get_position(asset.asset_id)
            if position and position.net_invested > 0:  # 只返回有持仓的资产
                positions.append(position)
        
        return positions
    
    # ==================== 投资组合管理 ====================
    
    def get_portfolio(self, base_currency: Currency = Currency.CNY) -> Portfolio:
        """
        获取当前投资组合
        
        Args:
            base_currency: 基础货币
            
        Returns:
            投资组合对象
        """
        positions = self.get_all_positions()
        return Portfolio(positions=positions, base_currency=base_currency)
    
    def create_portfolio_snapshot(
        self,
        description: Optional[str] = None,
        base_currency: Currency = Currency.CNY
    ) -> PortfolioSnapshot:
        """
        创建投资组合快照
        
        Args:
            description: 快照描述
            base_currency: 基础货币
            
        Returns:
            创建的快照对象
        """
        # 获取当前投资组合
        portfolio = self.get_portfolio(base_currency)
        
        # 创建快照
        snapshot = PortfolioSnapshot.from_portfolio(
            portfolio=portfolio,
            description=description or f"投资组合快照 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # 保存到数据库
        if not self.repositories.snapshots.create(snapshot):
            raise RuntimeError(f"创建投资组合快照失败: {snapshot.snapshot_id}")
        
        return snapshot
    
    def get_portfolio_snapshot(self, snapshot_id: str) -> Optional[PortfolioSnapshot]:
        """根据ID获取投资组合快照"""
        return self.repositories.snapshots.get_by_id(snapshot_id)
    
    def get_portfolio_snapshots_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[PortfolioSnapshot]:
        """获取指定日期范围内的投资组合快照"""
        return self.repositories.snapshots.get_by_date_range(start_date, end_date)
    
    def get_latest_portfolio_snapshots(self, limit: int = 10) -> List[PortfolioSnapshot]:
        """获取最新的投资组合快照列表"""
        return self.repositories.snapshots.get_latest(limit)
    
    def delete_portfolio_snapshot(self, snapshot_id: str) -> bool:
        """删除投资组合快照"""
        return self.repositories.snapshots.delete(snapshot_id)
    
    # ==================== 分析功能 ====================
    
    def get_asset_allocation(self, base_currency: Currency = Currency.CNY) -> Dict[str, Decimal]:
        """
        获取资产配置比例
        
        Args:
            base_currency: 基础货币
            
        Returns:
            资产配置字典 {资产类型: 比例}
        """
        portfolio = self.get_portfolio(base_currency)
        return portfolio.get_asset_allocation()
    
    def get_performance_summary(self, base_currency: Currency = Currency.CNY) -> Dict[str, Any]:
        """
        获取业绩摘要
        
        Args:
            base_currency: 基础货币
            
        Returns:
            业绩摘要字典
        """
        portfolio = self.get_portfolio(base_currency)
        
        return {
            'total_value': portfolio.total_value,
            'total_cost': portfolio.total_cost,
            'total_return': portfolio.total_return,
            'total_return_rate': portfolio.total_return_rate,
            'asset_count': len(portfolio.positions),
            'base_currency': base_currency.value,
            'last_updated': datetime.now().isoformat()
        }
    
    # ==================== 资源管理 ====================
    
    def close(self):
        """关闭服务，释放资源"""
        self.repositories.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_recent_transactions(self, limit: int = 50):
        """获取最近的交易记录"""
        return self.repositories.transactions.get_recent(limit) 