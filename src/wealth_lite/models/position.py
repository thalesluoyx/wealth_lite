"""
WealthLite 持仓模型

Position类负责基于交易记录计算持仓状态，所有数值都从交易记录实时计算得出。
遵循"只有交易能产生持仓"的核心原则。
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .asset import Asset
from .transaction import BaseTransaction
from .enums import PositionStatus, Currency


@dataclass
class Position:
    """
    持仓状态类
    
    职责：
    - 基于交易记录计算持仓状态
    - 提供持仓的各种计算指标
    - 所有数值都从交易记录实时计算，不存储中间结果
    """
    
    asset: Asset
    transactions: List[BaseTransaction] = field(default_factory=list)
    base_currency: Currency = Currency.CNY

    def __post_init__(self):
        """初始化后处理"""
        if not self.asset:
            raise ValueError("资产信息不能为空")
        
        # 按交易日期排序
        self.transactions.sort(key=lambda t: t.transaction_date)

    @property
    def position_id(self) -> str:
        """持仓唯一标识（使用资产ID）"""
        return self.asset.asset_id

    @property
    def asset_name(self) -> str:
        """资产名称"""
        return self.asset.display_name

    @property
    def asset_type(self) -> str:
        """资产类型"""
        return self.asset.asset_type.name

    @property
    def transaction_count(self) -> int:
        """交易笔数"""
        return len(self.transactions)

    @property
    def first_transaction_date(self) -> Optional[date]:
        """首次交易日期"""
        if self.transactions:
            return self.transactions[0].transaction_date
        return None

    @property
    def last_transaction_date(self) -> Optional[date]:
        """最后交易日期"""
        if self.transactions:
            return self.transactions[-1].transaction_date
        return None

    @property
    def holding_days(self) -> int:
        """持有天数"""
        if self.first_transaction_date:
            return (date.today() - self.first_transaction_date).days
        return 0

    @property
    def total_invested(self) -> Decimal:
        """总投入金额（基础货币）"""
        from .enums import TransactionType
        investment_types = [TransactionType.BUY, TransactionType.DEPOSIT, TransactionType.TRANSFER_IN]
        
        return sum(
            t.amount_base_currency for t in self.transactions
            if t.transaction_type in investment_types
        )

    @property
    def total_withdrawn(self) -> Decimal:
        """总取出金额（基础货币）"""
        from .enums import TransactionType
        withdrawal_types = [TransactionType.SELL, TransactionType.WITHDRAW, TransactionType.TRANSFER_OUT]
        
        return sum(
            t.amount_base_currency for t in self.transactions
            if t.transaction_type in withdrawal_types
        )

    @property
    def total_income(self) -> Decimal:
        """总收入金额（基础货币）"""
        from .enums import TransactionType
        income_types = [TransactionType.INTEREST, TransactionType.DIVIDEND]
        
        return sum(
            t.amount_base_currency for t in self.transactions
            if t.transaction_type in income_types
        )

    @property
    def total_fees(self) -> Decimal:
        """总费用（基础货币）"""
        from .enums import TransactionType
        
        return sum(
            t.amount_base_currency for t in self.transactions
            if t.transaction_type == TransactionType.FEE
        )

    @property
    def net_invested(self) -> Decimal:
        """净投入金额（投入 - 取出）"""
        return self.total_invested - self.total_withdrawn

    @property
    def principal_amount(self) -> Decimal:
        """本金金额（净投入 - 费用）"""
        return self.net_invested - self.total_fees

    @property
    def current_book_value(self) -> Decimal:
        """当前账面价值（本金 + 收入）- 基础货币"""
        return self.principal_amount + self.total_income
    
    @property
    def current_book_value_original_currency(self) -> Decimal:
        """当前账面价值（原币种）"""
        return self.principal_amount_original_currency + self.total_income_original_currency
    
    @property
    def total_invested_original_currency(self) -> Decimal:
        """总投入金额（原币种）"""
        from .enums import TransactionType
        investment_types = [TransactionType.BUY, TransactionType.DEPOSIT, TransactionType.TRANSFER_IN]
        
        return sum(
            t.amount for t in self.transactions
            if t.transaction_type in investment_types
        )
    
    @property
    def total_withdrawn_original_currency(self) -> Decimal:
        """总取出金额（原币种）"""
        from .enums import TransactionType
        withdrawal_types = [TransactionType.SELL, TransactionType.WITHDRAW, TransactionType.TRANSFER_OUT]
        
        return sum(
            t.amount for t in self.transactions
            if t.transaction_type in withdrawal_types
        )
    
    @property
    def total_income_original_currency(self) -> Decimal:
        """总收入金额（原币种）"""
        from .enums import TransactionType
        income_types = [TransactionType.INTEREST, TransactionType.DIVIDEND]
        
        return sum(
            t.amount for t in self.transactions
            if t.transaction_type in income_types
        )
    
    @property
    def total_fees_original_currency(self) -> Decimal:
        """总费用（原币种）"""
        from .enums import TransactionType
        
        return sum(
            t.amount for t in self.transactions
            if t.transaction_type == TransactionType.FEE
        )
    
    @property
    def net_invested_original_currency(self) -> Decimal:
        """净投入金额（原币种）"""
        return self.total_invested_original_currency - self.total_withdrawn_original_currency
    
    @property
    def principal_amount_original_currency(self) -> Decimal:
        """本金金额（原币种）"""
        return self.net_invested_original_currency - self.total_fees_original_currency

    @property
    def status(self) -> PositionStatus:
        """持仓状态"""
        if self.net_invested <= 0:
            return PositionStatus.CLOSED
        
        # 检查是否有到期的固定收益产品
        from .transaction import FixedIncomeTransaction
        for transaction in self.transactions:
            if isinstance(transaction, FixedIncomeTransaction):
                if transaction.is_matured:
                    return PositionStatus.MATURED
        
        return PositionStatus.ACTIVE

    def calculate_current_value(self, market_price: Optional[Decimal] = None) -> Decimal:
        """
        计算当前市值
        
        Args:
            market_price: 当前市场价格（可选）
        
        Returns:
            当前市值（基础货币）
        """
        if market_price is not None:
            # 使用提供的市场价格
            return self._calculate_market_value(market_price)
        
        # 根据资产类型使用不同的估值方法
        if self.asset.asset_type.name == 'CASH':
            # 现金类资产：账面价值即为市值
            return self.current_book_value
        elif self.asset.asset_type.name == 'FIXED_INCOME':
            # 固定收益：使用专门的计算方法
            return self._calculate_fixed_income_value()
        else:
            # 其他类型：默认使用账面价值
            return self.current_book_value

    def _calculate_market_value(self, market_price: Decimal) -> Decimal:
        """使用市场价格计算市值"""
        # 这里需要根据具体的资产类型和持有数量来计算
        # 简化实现：假设市场价格是每单位价格
        return market_price * self.net_invested

    def _calculate_fixed_income_value(self) -> Decimal:
        """计算固定收益产品的当前价值"""
        # 简化实现：使用账面价值
        # 实际实现中可以考虑利息计算、折现等
        return self.current_book_value

    def calculate_total_return(self, current_value: Optional[Decimal] = None) -> Decimal:
        """
        计算总收益
        
        Args:
            current_value: 当前市值（可选）
        
        Returns:
            总收益（基础货币）
        """
        if current_value is None:
            current_value = self.calculate_current_value()
        
        return current_value - self.principal_amount

    def calculate_total_return_rate(self, current_value: Optional[Decimal] = None) -> float:
        """
        计算总收益率
        
        Args:
            current_value: 当前市值（可选）
        
        Returns:
            总收益率（百分比）
        """
        if self.principal_amount <= 0:
            return 0.0
        
        total_return = self.calculate_total_return(current_value)
        return float(total_return / self.principal_amount * 100)

    def calculate_annualized_return(self, current_value: Optional[Decimal] = None) -> float:
        """
        计算年化收益率
        
        Args:
            current_value: 当前市值（可选）
        
        Returns:
            年化收益率（百分比）
        """
        if self.holding_days <= 0 or self.principal_amount <= 0:
            return 0.0
        
        total_return_rate = self.calculate_total_return_rate(current_value) / 100
        years = self.holding_days / 365.25
        
        if years <= 0:
            return 0.0
        
        # 使用复合年增长率公式：(终值/初值)^(1/年数) - 1
        try:
            current_val = current_value or self.calculate_current_value()
            if current_val > 0:
                annualized_rate = (float(current_val / self.principal_amount) ** (1 / years)) - 1
                return annualized_rate * 100
        except (ZeroDivisionError, ValueError):
            pass
        
        return 0.0

    def get_transactions_by_type(self, transaction_type) -> List[BaseTransaction]:
        """获取指定类型的交易记录"""
        return [t for t in self.transactions if t.transaction_type == transaction_type]

    def get_transactions_by_date_range(self, start_date: date, end_date: date) -> List[BaseTransaction]:
        """获取指定日期范围内的交易记录"""
        return [
            t for t in self.transactions
            if start_date <= t.transaction_date <= end_date
        ]

    def add_transaction(self, transaction: BaseTransaction) -> None:
        """添加交易记录"""
        if transaction.asset_id != self.asset.asset_id:
            raise ValueError("交易记录的资产ID与持仓资产ID不匹配")
        
        self.transactions.append(transaction)
        # 重新排序
        self.transactions.sort(key=lambda t: t.transaction_date)

    def remove_transaction(self, transaction_id: str) -> bool:
        """删除交易记录"""
        for i, transaction in enumerate(self.transactions):
            if transaction.transaction_id == transaction_id:
                del self.transactions[i]
                return True
        return False

    def to_dict(self, include_transactions: bool = True) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            'position_id': self.position_id,
            'asset': self.asset.to_dict(),
            'base_currency': self.base_currency.name,
            'status': self.status.name,
            'transaction_count': self.transaction_count,
            'first_transaction_date': self.first_transaction_date.isoformat() if self.first_transaction_date else None,
            'last_transaction_date': self.last_transaction_date.isoformat() if self.last_transaction_date else None,
            'holding_days': self.holding_days,
            'total_invested': str(self.total_invested),
            'total_withdrawn': str(self.total_withdrawn),
            'total_income': str(self.total_income),
            'total_fees': str(self.total_fees),
            'net_invested': str(self.net_invested),
            'principal_amount': str(self.principal_amount),
            'current_book_value': str(self.current_book_value),
            'current_value': str(self.calculate_current_value()),
            'total_return': str(self.calculate_total_return()),
            'total_return_rate': self.calculate_total_return_rate(),
            'annualized_return': self.calculate_annualized_return()
        }
        
        if include_transactions:
            result['transactions'] = [t.to_dict() for t in self.transactions]
        
        return result

    def __str__(self) -> str:
        """字符串表示"""
        return f"Position({self.asset_name}, {self.status.display_name})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"Position(asset={self.asset_name}, status={self.status.name}, "
                f"net_invested={self.net_invested}, transactions={len(self.transactions)})")

    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, Position):
            return False
        return self.position_id == other.position_id

    def __hash__(self) -> int:
        """哈希值"""
        return hash(self.position_id) 