"""
资产管理器

整合数据存储和配置管理，提供统一的资产数据管理接口。
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional, Any, Tuple
import uuid

from models.asset import Asset, AssetTransaction
from models.category import CategoryManager
from data.csv_storage import CSVStorage
from data.json_storage import JSONStorage
from utils.calculator import Calculator


class AssetManager:
    """资产管理器"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化资产管理器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.csv_storage = CSVStorage(data_dir)
        self.json_storage = JSONStorage(data_dir)
        self.category_manager = CategoryManager()
        
        # 内存中的资产列表
        self._assets: List[Asset] = []
        self._loaded = False
        
        # 加载数据
        self.load_data()
    
    def load_data(self) -> bool:
        """
        从存储加载所有数据
        
        Returns:
            是否加载成功
        """
        try:
            self._assets = self.csv_storage.load_assets()
            self._loaded = True
            return True
        except Exception as e:
            print(f"加载数据失败: {e}")
            self._assets = []
            self._loaded = False
            return False
    
    def save_data(self) -> bool:
        """
        保存所有数据到存储
        
        Returns:
            是否保存成功
        """
        try:
            print(f"=== AssetManager.save_data ===")
            print(f"准备保存 {len(self._assets)} 个资产")
            result = self.csv_storage.save_assets(self._assets)
            print(f"CSV存储保存结果: {result}")
            return result
        except Exception as e:
            print(f"保存数据失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def add_asset(self, asset: Asset) -> bool:
        """
        添加新资产
        
        Args:
            asset: 资产对象
            
        Returns:
            是否添加成功
        """
        print(f"=== AssetManager.add_asset ===")
        print(f"资产名称: {asset.asset_name}")
        print(f"资产ID: {asset.asset_id}")
        
        # 检查资产名称是否重复
        existing_asset = self.get_asset_by_name(asset.asset_name)
        if existing_asset:
            print(f"资产名称重复: {asset.asset_name}")
            return False
        
        # 自动创建分类（如果不存在）
        try:
            category = self.category_manager.get_category(
                asset.primary_category, asset.secondary_category
            )
            if not category:
                print(f"分类不存在，自动创建: {asset.primary_category} - {asset.secondary_category}")
                # 这里可以添加自动创建分类的逻辑，暂时跳过验证
        except Exception as e:
            print(f"分类验证出错: {e}")
        
        print(f"添加资产到列表，当前资产数量: {len(self._assets)}")
        self._assets.append(asset)
        print(f"添加后资产数量: {len(self._assets)}")
        
        return True
    
    def update_asset(self, asset_id: str, **kwargs) -> bool:
        """
        更新资产信息
        
        Args:
            asset_id: 资产ID
            **kwargs: 要更新的字段
            
        Returns:
            是否更新成功
        """
        asset = self.get_asset_by_id(asset_id)
        if not asset:
            return False
        
        # 更新允许的字段
        updatable_fields = [
            'asset_name', 'primary_category', 'secondary_category',
            'current_value', 'description', 'tags'
        ]
        
        for field, value in kwargs.items():
            if field in updatable_fields:
                setattr(asset, field, value)
        
        # 更新修改时间
        asset.updated_date = datetime.now()
        asset.last_update_date = date.today()
        
        return True
    
    def delete_asset(self, asset_id: str) -> bool:
        """
        删除资产
        
        Args:
            asset_id: 资产ID
            
        Returns:
            是否删除成功
        """
        asset = self.get_asset_by_id(asset_id)
        if asset:
            self._assets.remove(asset)
            return True
        return False
    
    def get_asset_by_id(self, asset_id: str) -> Optional[Asset]:
        """
        根据ID获取资产
        
        Args:
            asset_id: 资产ID
            
        Returns:
            资产对象或None
        """
        for asset in self._assets:
            if asset.asset_id == asset_id:
                return asset
        return None
    
    def get_asset_by_name(self, asset_name: str) -> Optional[Asset]:
        """
        根据名称获取资产
        
        Args:
            asset_name: 资产名称
            
        Returns:
            资产对象或None
        """
        for asset in self._assets:
            if asset.asset_name == asset_name:
                return asset
        return None
    
    def get_all_assets(self) -> List[Asset]:
        """
        获取所有资产
        
        Returns:
            资产列表
        """
        return self._assets.copy()
    
    def get_assets_by_category(self, primary_category: str, secondary_category: Optional[str] = None) -> List[Asset]:
        """
        根据分类获取资产
        
        Args:
            primary_category: 一级分类
            secondary_category: 二级分类（可选）
            
        Returns:
            资产列表
        """
        assets = []
        for asset in self._assets:
            if asset.primary_category == primary_category:
                if secondary_category is None or asset.secondary_category == secondary_category:
                    assets.append(asset)
        return assets
    
    def add_transaction(self, asset_id: str, transaction: AssetTransaction) -> bool:
        """
        为资产添加交易记录
        
        Args:
            asset_id: 资产ID
            transaction: 交易记录
            
        Returns:
            是否添加成功
        """
        asset = self.get_asset_by_id(asset_id)
        if asset:
            asset.add_transaction(transaction)
            return True
        return False
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        获取投资组合摘要
        
        Returns:
            组合摘要信息
        """
        if not self._assets:
            return {
                "total_assets": 0,
                "total_initial_amount": 0.0,
                "total_current_value": 0.0,
                "total_return": 0.0,
                "total_return_rate": 0.0,
                "category_breakdown": {}
            }
        
        total_initial = sum(float(asset.initial_amount) for asset in self._assets)
        total_current = sum(float(asset.current_value) for asset in self._assets)
        total_return = total_current - total_initial
        total_return_rate = total_return / total_initial if total_initial > 0 else 0.0
        
        # 按分类统计
        category_breakdown = {}
        for asset in self._assets:
            category_key = f"{asset.primary_category} - {asset.secondary_category}"
            if category_key not in category_breakdown:
                category_breakdown[category_key] = {
                    "count": 0,
                    "initial_amount": 0.0,
                    "current_value": 0.0,
                    "return": 0.0,
                    "return_rate": 0.0
                }
            
            cat_data = category_breakdown[category_key]
            cat_data["count"] += 1
            cat_data["initial_amount"] += float(asset.initial_amount)
            cat_data["current_value"] += float(asset.current_value)
            cat_data["return"] = cat_data["current_value"] - cat_data["initial_amount"]
            cat_data["return_rate"] = (
                cat_data["return"] / cat_data["initial_amount"] 
                if cat_data["initial_amount"] > 0 else 0.0
            )
        
        return {
            "total_assets": len(self._assets),
            "total_initial_amount": total_initial,
            "total_current_value": total_current,
            "total_return": total_return,
            "total_return_rate": total_return_rate,
            "category_breakdown": category_breakdown
        }
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """
        获取投资表现分析
        
        Returns:
            表现分析数据
        """
        if not self._assets:
            return {}
        
        # 计算各项指标
        returns = []
        annualized_returns = []
        holding_periods = []
        
        for asset in self._assets:
            returns.append(asset.calculate_total_return_rate())
            annualized_returns.append(asset.calculate_annualized_return())
            holding_periods.append(asset.calculate_holding_days())
        
        # 统计分析
        avg_return = sum(returns) / len(returns)
        avg_annualized_return = sum(annualized_returns) / len(annualized_returns)
        avg_holding_period = sum(holding_periods) / len(holding_periods)
        
        # 最佳和最差表现
        best_asset = max(self._assets, key=lambda x: x.calculate_total_return_rate())
        worst_asset = min(self._assets, key=lambda x: x.calculate_total_return_rate())
        
        return {
            "average_return_rate": avg_return,
            "average_annualized_return": avg_annualized_return,
            "average_holding_period_days": avg_holding_period,
            "best_performer": {
                "name": best_asset.asset_name,
                "return_rate": best_asset.calculate_total_return_rate(),
                "annualized_return": best_asset.calculate_annualized_return()
            },
            "worst_performer": {
                "name": worst_asset.asset_name,
                "return_rate": worst_asset.calculate_total_return_rate(),
                "annualized_return": worst_asset.calculate_annualized_return()
            }
        }
    
    def search_assets(self, keyword: str) -> List[Asset]:
        """
        搜索资产
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的资产列表
        """
        keyword = keyword.lower()
        results = []
        
        for asset in self._assets:
            # 搜索资产名称、描述、标签
            if (keyword in asset.asset_name.lower() or
                keyword in asset.description.lower() or
                any(keyword in tag.lower() for tag in asset.tags)):
                results.append(asset)
        
        return results
    
    def backup_data(self) -> bool:
        """
        备份数据
        
        Returns:
            是否备份成功
        """
        return self.csv_storage.backup_data()
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """
        获取数据统计信息
        
        Returns:
            统计信息
        """
        csv_info = self.csv_storage.get_file_info()
        json_info = self.json_storage.get_file_info()
        
        # 计算交易记录总数
        total_transactions = sum(len(asset.transactions) for asset in self._assets)
        
        return {
            "assets_count": len(self._assets),
            "transactions_count": total_transactions,
            "categories_count": len(self.category_manager.get_all_categories()),
            "data_loaded": self._loaded,
            "file_info": {
                "csv": csv_info,
                "json": json_info
            }
        }
    
    def export_to_excel(self, file_path: str) -> bool:
        """
        导出数据到Excel文件
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            是否导出成功
        """
        try:
            import xlsxwriter
            
            workbook = xlsxwriter.Workbook(file_path)
            
            # 创建资产汇总工作表
            self._create_assets_sheet(workbook)
            
            # 创建交易记录工作表
            self._create_transactions_sheet(workbook)
            
            # 创建分类统计工作表
            self._create_category_summary_sheet(workbook)
            
            workbook.close()
            return True
            
        except Exception as e:
            print(f"导出Excel失败: {e}")
            return False
    
    def _create_assets_sheet(self, workbook):
        """创建资产汇总工作表"""
        worksheet = workbook.add_worksheet("资产汇总")
        
        # 设置表头
        headers = [
            "资产名称", "一级分类", "二级分类", "初始投入", "当前价值",
            "总收益", "总收益率", "年化回报率", "持有天数", "开始日期", "描述"
        ]
        
        # 写入表头
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # 写入数据
        for row, asset in enumerate(self._assets, 1):
            worksheet.write(row, 0, asset.asset_name)
            worksheet.write(row, 1, asset.primary_category)
            worksheet.write(row, 2, asset.secondary_category)
            worksheet.write(row, 3, float(asset.initial_amount))
            worksheet.write(row, 4, float(asset.current_value))
            worksheet.write(row, 5, float(asset.calculate_total_return()))
            worksheet.write(row, 6, asset.calculate_total_return_rate())
            worksheet.write(row, 7, asset.calculate_annualized_return())
            worksheet.write(row, 8, asset.calculate_holding_days())
            worksheet.write(row, 9, asset.start_date.isoformat())
            worksheet.write(row, 10, asset.description)
    
    def _create_transactions_sheet(self, workbook):
        """创建交易记录工作表"""
        worksheet = workbook.add_worksheet("交易记录")
        
        # 设置表头
        headers = [
            "资产名称", "交易日期", "交易类型", "金额", "数量", "单价", "描述"
        ]
        
        # 写入表头
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # 写入数据
        row = 1
        for asset in self._assets:
            for transaction in asset.transactions:
                worksheet.write(row, 0, asset.asset_name)
                worksheet.write(row, 1, transaction.transaction_date.isoformat())
                worksheet.write(row, 2, transaction.transaction_type)
                worksheet.write(row, 3, float(transaction.amount))
                worksheet.write(row, 4, float(transaction.quantity) if transaction.quantity else "")
                worksheet.write(row, 5, float(transaction.price) if transaction.price else "")
                worksheet.write(row, 6, transaction.description)
                row += 1
    
    def _create_category_summary_sheet(self, workbook):
        """创建分类统计工作表"""
        worksheet = workbook.add_worksheet("分类统计")
        
        # 获取组合摘要
        summary = self.get_portfolio_summary()
        
        # 设置表头
        headers = ["分类", "资产数量", "初始投入", "当前价值", "总收益", "收益率"]
        
        # 写入表头
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # 写入数据
        row = 1
        for category, data in summary["category_breakdown"].items():
            worksheet.write(row, 0, category)
            worksheet.write(row, 1, data["count"])
            worksheet.write(row, 2, data["initial_amount"])
            worksheet.write(row, 3, data["current_value"])
            worksheet.write(row, 4, data["return"])
            worksheet.write(row, 5, data["return_rate"])
            row += 1