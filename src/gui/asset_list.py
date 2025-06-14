"""
WealthLite 资产列表组件
使用Treeview显示资产数据
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable
from decimal import Decimal

from models.asset import Asset
from data.asset_manager import AssetManager


class AssetList(ttk.Frame):
    """资产列表组件"""
    
    def __init__(self, parent, asset_manager: AssetManager):
        """
        初始化资产列表
        
        Args:
            parent: 父组件
            asset_manager: 资产管理器
        """
        super().__init__(parent)
        self.asset_manager = asset_manager
        self.selection_callback: Optional[Callable[[Optional[Asset]], None]] = None
        
        self._create_widgets()
        self._setup_columns()
        self._bind_events()
    
    def _create_widgets(self):
        """创建组件"""
        # 标题标签
        title_label = ttk.Label(self, text="资产列表", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 5))
        
        # 创建Treeview和滚动条
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # 垂直滚动条
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 水平滚动条
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            selectmode='extended'
        )
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
    
    def _setup_columns(self):
        """设置列"""
        # 定义列
        columns = (
            'name', 'primary_category', 'secondary_category', 
            'initial_amount', 'current_value', 'return', 'return_rate',
            'annualized_return', 'start_date', 'holding_days'
        )
        
        self.tree['columns'] = columns
        self.tree['show'] = 'headings'
        
        # 设置列标题和宽度
        column_config = {
            'name': ('资产名称', 150),
            'primary_category': ('一级分类', 100),
            'secondary_category': ('二级分类', 120),
            'initial_amount': ('初始投入', 100),
            'current_value': ('当前价值', 100),
            'return': ('总收益', 100),
            'return_rate': ('收益率', 80),
            'annualized_return': ('年化回报率', 100),
            'start_date': ('开始日期', 100),
            'holding_days': ('持有天数', 80)
        }
        
        for col, (heading, width) in column_config.items():
            self.tree.heading(col, text=heading, command=lambda c=col: self._sort_column(c))
            self.tree.column(col, width=width, anchor='center')
        
        # 设置资产名称列左对齐
        self.tree.column('name', anchor='w')
    
    def _bind_events(self):
        """绑定事件"""
        self.tree.bind('<<TreeviewSelect>>', self._on_selection_change)
        self.tree.bind('<Double-1>', self._on_double_click)
    
    def _sort_column(self, col: str):
        """排序列"""
        # 获取当前数据
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        
        # 根据列类型进行排序
        if col in ['initial_amount', 'current_value', 'return', 'return_rate', 'annualized_return', 'holding_days']:
            # 数值排序
            try:
                data.sort(key=lambda x: float(x[0].replace('¥', '').replace(',', '').replace('%', '')))
            except ValueError:
                data.sort(key=lambda x: x[0])
        else:
            # 文本排序
            data.sort(key=lambda x: x[0])
        
        # 重新排列项目
        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)
    
    def _on_selection_change(self, event=None):
        """选择变化事件"""
        selected_items = self.tree.selection()
        if selected_items and self.selection_callback:
            # 获取选中的资产
            item_id = selected_items[0]
            tags = self.tree.item(item_id)['tags']
            asset_id = None
            
            # 从tags中找到asset_id（跳过颜色标签）
            for tag in tags:
                if tag not in ['positive', 'negative', 'neutral']:
                    asset_id = tag
                    break
            
            if asset_id:
                asset = self.asset_manager.get_asset_by_id(asset_id)
                self.selection_callback(asset)
            else:
                self.selection_callback(None)
        elif self.selection_callback:
            self.selection_callback(None)
    
    def _on_double_click(self, event=None):
        """双击事件"""
        # 可以在这里添加双击编辑功能
        pass
    
    def refresh(self):
        """刷新列表"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 获取所有资产
        assets = self.asset_manager.get_all_assets()
        self.show_assets(assets)
    
    def show_assets(self, assets: List[Asset]):
        """显示资产列表"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加资产数据
        for asset in assets:
            self._add_asset_to_tree(asset)
    
    def _add_asset_to_tree(self, asset: Asset):
        """添加资产到树形视图"""
        # 计算收益相关数据
        total_return = asset.calculate_total_return()
        return_rate = asset.calculate_total_return_rate()
        annualized_return = asset.calculate_annualized_return()
        holding_days = asset.calculate_holding_days()
        
        # 格式化数据
        values = (
            asset.asset_name,
            asset.primary_category,
            asset.secondary_category,
            f"¥{float(asset.initial_amount):,.2f}",
            f"¥{float(asset.current_value):,.2f}",
            f"¥{float(total_return):,.2f}",
            f"{return_rate:.2%}",
            f"{annualized_return:.2%}",
            asset.start_date.strftime("%Y-%m-%d"),
            str(holding_days)
        )
        
        # 根据收益率设置颜色标签
        if return_rate > 0:
            tags = ('positive', asset.asset_id)
        elif return_rate < 0:
            tags = ('negative', asset.asset_id)
        else:
            tags = ('neutral', asset.asset_id)
        
        # 插入数据
        self.tree.insert('', 'end', values=values, tags=tags)
        
        # 配置颜色标签
        self.tree.tag_configure('positive', foreground='green')
        self.tree.tag_configure('negative', foreground='red')
        self.tree.tag_configure('neutral', foreground='black')
    
    def get_selected_asset(self) -> Optional[Asset]:
        """获取选中的资产"""
        selected_items = self.tree.selection()
        if selected_items:
            item_id = selected_items[0]
            asset_id = self.tree.item(item_id)['tags'][0] if self.tree.item(item_id)['tags'] else None
            
            if asset_id and asset_id in ['positive', 'negative', 'neutral']:
                # 如果第一个tag是颜色标签，取第二个
                tags = self.tree.item(item_id)['tags']
                asset_id = tags[1] if len(tags) > 1 else None
            
            if asset_id:
                return self.asset_manager.get_asset_by_id(asset_id)
        
        return None
    
    def bind_selection_change(self, callback: Callable[[Optional[Asset]], None]):
        """绑定选择变化回调"""
        self.selection_callback = callback
    
    def select_asset(self, asset_id: str):
        """选择指定资产"""
        for item in self.tree.get_children():
            tags = self.tree.item(item)['tags']
            if asset_id in tags:
                self.tree.selection_set(item)
                self.tree.focus(item)
                self.tree.see(item)
                break 