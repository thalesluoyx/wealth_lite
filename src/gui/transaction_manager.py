"""
WealthLite 交易记录管理窗口
显示和管理选中资产的所有交易记录
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
from datetime import date

from models.asset import Asset, AssetTransaction
from data.asset_manager import AssetManager
from gui.transaction_form import TransactionForm


class TransactionManager:
    """交易记录管理窗口"""
    
    def __init__(self, parent, asset_manager: AssetManager, asset: Asset):
        """
        初始化交易记录管理窗口
        
        Args:
            parent: 父窗口
            asset_manager: 资产管理器
            asset: 要管理交易记录的资产
        """
        self.parent = parent
        self.asset_manager = asset_manager
        self.asset = asset
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title(f"交易记录管理 - {asset.asset_name}")
        self.window.geometry("800x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        # 居中显示
        self._center_window()
        
        # 创建界面
        self._create_widgets()
        self._bind_events()
        
        # 加载数据
        self._refresh_transactions()
    
    def _center_window(self):
        """窗口居中显示"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (width // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 资产信息框架
        info_frame = ttk.LabelFrame(main_frame, text="资产信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 资产信息显示
        info_text = f"""资产名称: {self.asset.asset_name}
分类: {self.asset.primary_category} - {self.asset.secondary_category}
初始投入: ¥{self.asset.initial_amount:,.2f}
当前价值: ¥{self.asset.current_value:,.2f}
总收益: ¥{self.asset.calculate_total_return():,.2f}
收益率: {self.asset.calculate_total_return_rate():.2%}"""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)
        
        # 工具栏框架
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 工具栏按钮
        ttk.Button(toolbar_frame, text="新建交易", command=self._new_transaction).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="编辑交易", command=self._edit_transaction).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="删除交易", command=self._delete_transaction).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="刷新", command=self._refresh_transactions).pack(side=tk.LEFT, padx=(0, 5))
        
        # 交易记录列表框架
        list_frame = ttk.LabelFrame(main_frame, text="交易记录", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview和滚动条
        tree_frame = ttk.Frame(list_frame)
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
        
        # 设置列
        self._setup_columns()
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 关闭按钮
        ttk.Button(button_frame, text="关闭", command=self._close).pack(side=tk.RIGHT)
    
    def _setup_columns(self):
        """设置列"""
        # 定义列
        columns = ('date', 'type', 'amount', 'quantity', 'price', 'description')
        
        self.tree['columns'] = columns
        self.tree['show'] = 'headings'
        
        # 设置列标题和宽度
        column_config = {
            'date': ('交易日期', 100),
            'type': ('交易类型', 100),
            'amount': ('金额', 120),
            'quantity': ('数量', 100),
            'price': ('单价', 100),
            'description': ('描述', 200)
        }
        
        for col, (heading, width) in column_config.items():
            self.tree.heading(col, text=heading, command=lambda c=col: self._sort_column(c))
            self.tree.column(col, width=width, anchor='center')
        
        # 设置描述列左对齐
        self.tree.column('description', anchor='w')
    
    def _bind_events(self):
        """绑定事件"""
        self.tree.bind('<Double-1>', self._on_double_click)
        self.window.bind('<Delete>', lambda e: self._delete_transaction())
        self.window.bind('<F5>', lambda e: self._refresh_transactions())
    
    def _sort_column(self, col: str):
        """排序列"""
        # 获取当前数据
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        
        # 根据列类型进行排序
        if col in ['amount', 'quantity', 'price']:
            # 数值排序
            try:
                data.sort(key=lambda x: float(x[0].replace('¥', '').replace(',', '')) if x[0] else 0)
            except ValueError:
                data.sort(key=lambda x: x[0])
        else:
            # 文本排序
            data.sort(key=lambda x: x[0])
        
        # 重新排列项目
        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)
    
    def _refresh_transactions(self):
        """刷新交易记录列表"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加交易记录
        for transaction in self.asset.transactions:
            self._add_transaction_to_tree(transaction)
    
    def _add_transaction_to_tree(self, transaction: AssetTransaction):
        """添加交易记录到树形视图"""
        # 格式化数据
        values = (
            transaction.transaction_date.strftime("%Y-%m-%d"),
            transaction.transaction_type,
            f"¥{float(transaction.amount):,.2f}",
            str(transaction.quantity) if transaction.quantity else "",
            f"¥{float(transaction.price):,.2f}" if transaction.price else "",
            transaction.description
        )
        
        # 插入数据，使用transaction_id作为标签
        self.tree.insert('', 'end', values=values, tags=(transaction.transaction_id,))
    
    def _get_selected_transaction(self) -> Optional[AssetTransaction]:
        """获取选中的交易记录"""
        selected_items = self.tree.selection()
        if not selected_items:
            return None
        
        item_id = selected_items[0]
        transaction_id = self.tree.item(item_id)['tags'][0] if self.tree.item(item_id)['tags'] else None
        
        if transaction_id:
            for transaction in self.asset.transactions:
                if transaction.transaction_id == transaction_id:
                    return transaction
        
        return None
    
    def _new_transaction(self):
        """新建交易记录"""
        form = TransactionForm(self.window, self.asset_manager, self.asset)
        if form.show():
            self._refresh_transactions()
            messagebox.showinfo("成功", "交易记录添加成功")
    
    def _edit_transaction(self):
        """编辑交易记录"""
        selected_transaction = self._get_selected_transaction()
        if not selected_transaction:
            messagebox.showwarning("警告", "请先选择要编辑的交易记录")
            return
        
        form = TransactionForm(self.window, self.asset_manager, self.asset, selected_transaction)
        if form.show():
            self._refresh_transactions()
            messagebox.showinfo("成功", "交易记录修改成功")
    
    def _delete_transaction(self):
        """删除交易记录"""
        selected_transaction = self._get_selected_transaction()
        if not selected_transaction:
            messagebox.showwarning("警告", "请先选择要删除的交易记录")
            return
        
        if messagebox.askyesno("确认删除", f"确定要删除这条交易记录吗？\n\n{selected_transaction.transaction_type} - {selected_transaction.transaction_date}\n金额: ¥{selected_transaction.amount:,.2f}"):
            try:
                # 从资产中移除交易记录
                self.asset.transactions.remove(selected_transaction)
                
                # 保存数据
                if self.asset_manager.save_data():
                    self._refresh_transactions()
                    messagebox.showinfo("成功", "交易记录删除成功")
                else:
                    messagebox.showerror("错误", "删除交易记录失败")
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {e}")
    
    def _on_double_click(self, event=None):
        """双击事件"""
        self._edit_transaction()
    
    def _close(self):
        """关闭窗口"""
        self.window.destroy()
    
    def show(self):
        """显示窗口"""
        self.window.wait_window() 