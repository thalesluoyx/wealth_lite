"""
CSV文件存储管理器

提供资产数据的CSV文件存储和读取功能。
"""

import csv
import os
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional, Any
from pathlib import Path

from models.asset import Asset, AssetTransaction
from utils.validator import Validator


class CSVStorage:
    """CSV文件存储管理器"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化CSV存储管理器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.assets_file = self.data_dir / "assets.csv"
        self.transactions_file = self.data_dir / "transactions.csv"
        
        # 确保数据目录存在
        self.data_dir.mkdir(exist_ok=True)
        
        # CSV文件头定义
        self.assets_headers = [
            "asset_id", "asset_name", "primary_category", "secondary_category",
            "initial_amount", "current_value", "start_date", "last_update_date",
            "description", "tags", "created_date", "updated_date"
        ]
        
        self.transactions_headers = [
            "transaction_id", "asset_id", "transaction_date", "transaction_type",
            "amount", "quantity", "price", "description"
        ]
    
    def save_assets(self, assets: List[Asset]) -> bool:
        """
        保存资产列表到CSV文件
        
        Args:
            assets: 资产列表
            
        Returns:
            是否保存成功
        """
        try:
            with open(self.assets_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.assets_headers)
                writer.writeheader()
                
                for asset in assets:
                    # 转换资产数据为CSV行
                    row = {
                        "asset_id": asset.asset_id,
                        "asset_name": asset.asset_name,
                        "primary_category": asset.primary_category,
                        "secondary_category": asset.secondary_category,
                        "initial_amount": str(asset.initial_amount),
                        "current_value": str(asset.current_value),
                        "start_date": asset.start_date.isoformat(),
                        "last_update_date": asset.last_update_date.isoformat(),
                        "description": asset.description,
                        "tags": ",".join(asset.tags),  # 标签用逗号分隔
                        "created_date": asset.created_date.isoformat(),
                        "updated_date": asset.updated_date.isoformat()
                    }
                    writer.writerow(row)
            
            # 保存交易记录
            self._save_transactions(assets)
            return True
            
        except Exception as e:
            print(f"保存资产数据失败: {e}")
            return False
    
    def _save_transactions(self, assets: List[Asset]) -> None:
        """
        保存所有资产的交易记录
        
        Args:
            assets: 资产列表
        """
        with open(self.transactions_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.transactions_headers)
            writer.writeheader()
            
            for asset in assets:
                for transaction in asset.transactions:
                    row = {
                        "transaction_id": transaction.transaction_id,
                        "asset_id": asset.asset_id,
                        "transaction_date": transaction.transaction_date.isoformat(),
                        "transaction_type": transaction.transaction_type,
                        "amount": str(transaction.amount),
                        "quantity": str(transaction.quantity) if transaction.quantity else "",
                        "price": str(transaction.price) if transaction.price else "",
                        "description": transaction.description
                    }
                    writer.writerow(row)
    
    def load_assets(self) -> List[Asset]:
        """
        从CSV文件加载资产列表
        
        Returns:
            资产列表
        """
        assets = []
        
        if not self.assets_file.exists():
            return assets
        
        try:
            # 加载资产基本信息
            with open(self.assets_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    # 验证必需字段
                    if not self._validate_asset_row(row):
                        continue
                    
                    # 创建资产对象
                    asset = Asset(
                        asset_id=row["asset_id"],
                        asset_name=row["asset_name"],
                        primary_category=row["primary_category"],
                        secondary_category=row["secondary_category"],
                        initial_amount=Decimal(row["initial_amount"]),
                        current_value=Decimal(row["current_value"]),
                        start_date=date.fromisoformat(row["start_date"]),
                        last_update_date=date.fromisoformat(row["last_update_date"]),
                        description=row.get("description", ""),
                        tags=row.get("tags", "").split(",") if row.get("tags") else [],
                        created_date=datetime.fromisoformat(row["created_date"]),
                        updated_date=datetime.fromisoformat(row["updated_date"])
                    )
                    
                    assets.append(asset)
            
            # 加载交易记录
            self._load_transactions(assets)
            
        except Exception as e:
            print(f"加载资产数据失败: {e}")
        
        return assets
    
    def _load_transactions(self, assets: List[Asset]) -> None:
        """
        加载交易记录并关联到对应资产
        
        Args:
            assets: 资产列表
        """
        if not self.transactions_file.exists():
            return
        
        # 创建资产ID到资产对象的映射
        asset_map = {asset.asset_id: asset for asset in assets}
        
        try:
            with open(self.transactions_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    asset_id = row.get("asset_id")
                    if asset_id not in asset_map:
                        continue
                    
                    # 创建交易记录
                    transaction = AssetTransaction(
                        transaction_id=row["transaction_id"],
                        transaction_date=date.fromisoformat(row["transaction_date"]),
                        transaction_type=row["transaction_type"],
                        amount=Decimal(row["amount"]),
                        quantity=Decimal(row["quantity"]) if row.get("quantity") else None,
                        price=Decimal(row["price"]) if row.get("price") else None,
                        description=row.get("description", "")
                    )
                    
                    # 添加到对应资产
                    asset_map[asset_id].transactions.append(transaction)
                    
        except Exception as e:
            print(f"加载交易记录失败: {e}")
    
    def _validate_asset_row(self, row: Dict[str, str]) -> bool:
        """
        验证资产CSV行数据
        
        Args:
            row: CSV行数据
            
        Returns:
            是否有效
        """
        required_fields = [
            "asset_id", "asset_name", "primary_category", "secondary_category",
            "initial_amount", "current_value", "start_date", "last_update_date"
        ]
        
        # 检查必需字段
        for field in required_fields:
            if not row.get(field):
                return False
        
        # 验证金额
        if not Validator.validate_amount(row["initial_amount"]):
            return False
        if not Validator.validate_amount(row["current_value"]):
            return False
        
        # 验证日期
        if not Validator.validate_date(row["start_date"]):
            return False
        if not Validator.validate_date(row["last_update_date"]):
            return False
        
        # 验证资产名称
        if not Validator.validate_asset_name(row["asset_name"]):
            return False
        
        return True
    
    def backup_data(self, backup_dir: Optional[str] = None) -> bool:
        """
        备份数据文件
        
        Args:
            backup_dir: 备份目录，默认为data/backups
            
        Returns:
            是否备份成功
        """
        if backup_dir is None:
            backup_dir = self.data_dir / "backups"
        else:
            backup_dir = Path(backup_dir)
        
        backup_dir.mkdir(exist_ok=True)
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 备份资产文件
            if self.assets_file.exists():
                backup_assets_file = backup_dir / f"assets_{timestamp}.csv"
                import shutil
                shutil.copy2(self.assets_file, backup_assets_file)
            
            # 备份交易记录文件
            if self.transactions_file.exists():
                backup_transactions_file = backup_dir / f"transactions_{timestamp}.csv"
                shutil.copy2(self.transactions_file, backup_transactions_file)
            
            return True
            
        except Exception as e:
            print(f"备份数据失败: {e}")
            return False
    
    def get_file_info(self) -> Dict[str, Any]:
        """
        获取数据文件信息
        
        Returns:
            文件信息字典
        """
        info = {
            "assets_file": {
                "path": str(self.assets_file),
                "exists": self.assets_file.exists(),
                "size": self.assets_file.stat().st_size if self.assets_file.exists() else 0,
                "modified": datetime.fromtimestamp(
                    self.assets_file.stat().st_mtime
                ).isoformat() if self.assets_file.exists() else None
            },
            "transactions_file": {
                "path": str(self.transactions_file),
                "exists": self.transactions_file.exists(),
                "size": self.transactions_file.stat().st_size if self.transactions_file.exists() else 0,
                "modified": datetime.fromtimestamp(
                    self.transactions_file.stat().st_mtime
                ).isoformat() if self.transactions_file.exists() else None
            }
        }
        
        return info 