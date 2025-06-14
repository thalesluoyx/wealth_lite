"""
资产表单工厂

根据资产类型选择对应的表单进行新建或编辑操作。
"""

from typing import Optional
from models.asset import Asset
from data.asset_manager import AssetManager
from models.category import CategoryManager
from gui.asset_form import AssetForm
from gui.fixed_income_form import FixedIncomeForm


class AssetFormFactory:
    """资产表单工厂类"""
    
    @staticmethod
    def create_form(parent, asset_manager: AssetManager, category_manager: CategoryManager, 
                   asset: Optional[Asset] = None, asset_type: str = None):
        """
        根据资产类型创建对应的表单
        
        Args:
            parent: 父窗口
            asset_manager: 资产管理器
            category_manager: 分类管理器
            asset: 要编辑的资产（新建时为None）
            asset_type: 资产类型（仅在新建时使用）
        
        Returns:
            对应的表单实例
        """
        # 如果是编辑模式，从资产对象获取类型
        if asset:
            primary_category = asset.primary_category
        else:
            primary_category = asset_type
        
        # 根据资产类型选择对应的表单
        if primary_category == "固定收益类":
            return FixedIncomeForm(parent, asset_manager, category_manager, asset)
        else:
            # 其他类型使用通用表单
            return AssetForm(parent, asset_manager, category_manager, asset)
    
    @staticmethod
    def get_supported_asset_types():
        """
        获取支持的资产类型列表
        
        Returns:
            支持的资产类型字典，格式为 {类型名: 表单类}
        """
        return {
            "固定收益类": FixedIncomeForm,
            "股票类": AssetForm,  # 暂时使用通用表单
            "基金类": AssetForm,  # 暂时使用通用表单
            "房地产": AssetForm,  # 暂时使用通用表单
            "其他": AssetForm     # 通用表单
        }
    
    @staticmethod
    def has_specialized_form(asset_type: str) -> bool:
        """
        检查指定资产类型是否有专门的表单
        
        Args:
            asset_type: 资产类型
            
        Returns:
            是否有专门的表单
        """
        specialized_forms = {
            "固定收益类": True,
            # 未来可以添加更多专门表单
        }
        return specialized_forms.get(asset_type, False) 