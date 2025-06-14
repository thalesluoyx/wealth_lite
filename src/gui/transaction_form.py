"""
WealthLite 交易记录表单组件
用于新建和编辑交易记录的对话框
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from models.asset import Asset, AssetTransaction
from data.asset_manager import AssetManager


class TransactionForm:
    """交易记录表单对话框"""
    
    def __init__(self, parent, asset_manager: AssetManager, asset: Asset, transaction: Optional[AssetTransaction] = None):
        """
        初始化交易记录表单
        
        Args:
            parent: 父窗口
            asset_manager: 资产管理器
            asset: 所属资产
            transaction: 要编辑的交易记录（None表示新建）
        """
        self.parent = parent
        self.asset_manager = asset_manager
        self.asset = asset
        self.transaction = transaction
        self.result = False
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑交易记录" if transaction else "新建交易记录")
        self.dialog.geometry("450x450")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self._center_dialog()
        
        # 创建界面
        self._create_widgets()
        self._setup_validation()
        
        # 如果是编辑模式，填充数据
        if self.transaction:
            self._populate_data()
        
        # 设置焦点
        self.transaction_type_combo.focus()
    
    def _center_dialog(self):
        """对话框居中显示"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (width // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 资产信息显示
        info_frame = ttk.LabelFrame(main_frame, text="资产信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"资产名称: {self.asset.asset_name}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"分类: {self.asset.primary_category} - {self.asset.secondary_category}").pack(anchor=tk.W)
        
        # 交易信息框架
        transaction_frame = ttk.LabelFrame(main_frame, text="交易信息", padding="10")
        transaction_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 交易类型
        ttk.Label(transaction_frame, text="交易类型 *:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.transaction_type_var = tk.StringVar()
        self.transaction_type_combo = ttk.Combobox(
            transaction_frame,
            textvariable=self.transaction_type_var,
            values=["买入", "卖出", "分红", "利息", "追加投资", "转入", "转出", "其他"],
            state="readonly",
            width=35
        )
        self.transaction_type_combo.grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=(10, 0))
        
        # 交易日期
        ttk.Label(transaction_frame, text="交易日期 *:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.transaction_date_var = tk.StringVar()
        self.transaction_date_entry = ttk.Entry(transaction_frame, textvariable=self.transaction_date_var, width=38)
        self.transaction_date_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2, padx=(10, 0))
        ttk.Label(transaction_frame, text="(YYYY-MM-DD)").grid(row=1, column=2, sticky=tk.W, padx=(5, 0))
        
        # 设置默认日期为今天
        if not self.transaction:
            self.transaction_date_var.set(date.today().strftime("%Y-%m-%d"))
        
        # 交易金额
        ttk.Label(transaction_frame, text="交易金额 *:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(transaction_frame, textvariable=self.amount_var, width=25)
        self.amount_entry.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        ttk.Label(transaction_frame, text="元").grid(row=2, column=2, sticky=tk.W, padx=(5, 0))
        
        # 交易数量（可选）
        ttk.Label(transaction_frame, text="交易数量:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.quantity_var = tk.StringVar()
        self.quantity_entry = ttk.Entry(transaction_frame, textvariable=self.quantity_var, width=25)
        self.quantity_entry.grid(row=3, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        ttk.Label(transaction_frame, text="股/份").grid(row=3, column=2, sticky=tk.W, padx=(5, 0))
        
        # 单价（可选）
        ttk.Label(transaction_frame, text="单价:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.price_var = tk.StringVar()
        self.price_entry = ttk.Entry(transaction_frame, textvariable=self.price_var, width=25)
        self.price_entry.grid(row=4, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        ttk.Label(transaction_frame, text="元").grid(row=4, column=2, sticky=tk.W, padx=(5, 0))
        
        # 描述
        ttk.Label(transaction_frame, text="描述:").grid(row=5, column=0, sticky=tk.W+tk.N, pady=2)
        self.description_text = tk.Text(transaction_frame, height=2, width=40)
        self.description_text.grid(row=5, column=1, columnspan=2, sticky=tk.W+tk.E, pady=2, padx=(10, 0))
        
        # 配置列权重
        transaction_frame.columnconfigure(1, weight=1)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 保存按钮
        ttk.Button(button_frame, text="保存", command=self._save).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 取消按钮
        ttk.Button(button_frame, text="取消", command=self._cancel).pack(side=tk.RIGHT)
    
    def _setup_validation(self):
        """设置输入验证"""
        # 数字验证
        vcmd = (self.dialog.register(self._validate_number), '%P')
        self.amount_entry.config(validate='key', validatecommand=vcmd)
        self.quantity_entry.config(validate='key', validatecommand=vcmd)
        self.price_entry.config(validate='key', validatecommand=vcmd)
    
    def _validate_number(self, value: str) -> bool:
        """验证数字输入"""
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _populate_data(self):
        """填充编辑数据"""
        if not self.transaction:
            return
        
        # 填充交易信息
        self.transaction_type_var.set(self.transaction.transaction_type)
        self.transaction_date_var.set(self.transaction.transaction_date.strftime("%Y-%m-%d"))
        self.amount_var.set(str(self.transaction.amount))
        
        if self.transaction.quantity:
            self.quantity_var.set(str(self.transaction.quantity))
        
        if self.transaction.price:
            self.price_var.set(str(self.transaction.price))
        
        self.description_text.insert(1.0, self.transaction.description)
    
    def _save(self):
        """保存交易记录"""
        # 验证必填字段
        if not self._validate_required_fields():
            return
        
        try:
            # 获取表单数据
            transaction_type = self.transaction_type_var.get()
            transaction_date = datetime.strptime(self.transaction_date_var.get(), "%Y-%m-%d").date()
            amount = Decimal(self.amount_var.get())
            
            quantity = None
            if self.quantity_var.get().strip():
                quantity = Decimal(self.quantity_var.get())
            
            price = None
            if self.price_var.get().strip():
                price = Decimal(self.price_var.get())
            
            description = self.description_text.get(1.0, tk.END).strip()
            
            if self.transaction:
                # 编辑模式
                self.transaction.transaction_type = transaction_type
                self.transaction.transaction_date = transaction_date
                self.transaction.amount = amount
                self.transaction.quantity = quantity
                self.transaction.price = price
                self.transaction.description = description
            else:
                # 新建模式
                new_transaction = AssetTransaction(
                    transaction_type=transaction_type,
                    transaction_date=transaction_date,
                    amount=amount,
                    quantity=quantity,
                    price=price,
                    description=description
                )
                
                # 添加到资产
                self.asset.add_transaction(new_transaction)
            
            # 保存数据
            success = self.asset_manager.save_data()
            
            if success:
                self.result = True
                self.dialog.destroy()
            else:
                messagebox.showerror("错误", "保存交易记录失败")
                
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def _validate_required_fields(self) -> bool:
        """验证必填字段"""
        if not self.transaction_type_var.get():
            messagebox.showwarning("警告", "请选择交易类型")
            self.transaction_type_combo.focus()
            return False
        
        if not self.transaction_date_var.get().strip():
            messagebox.showwarning("警告", "请输入交易日期")
            self.transaction_date_entry.focus()
            return False
        
        if not self.amount_var.get().strip():
            messagebox.showwarning("警告", "请输入交易金额")
            self.amount_entry.focus()
            return False
        
        try:
            datetime.strptime(self.transaction_date_var.get(), "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("错误", "日期格式不正确，请使用YYYY-MM-DD格式")
            self.transaction_date_entry.focus()
            return False
        
        try:
            Decimal(self.amount_var.get())
        except InvalidOperation:
            messagebox.showerror("错误", "交易金额格式不正确")
            self.amount_entry.focus()
            return False
        
        if self.quantity_var.get().strip():
            try:
                Decimal(self.quantity_var.get())
            except InvalidOperation:
                messagebox.showerror("错误", "交易数量格式不正确")
                self.quantity_entry.focus()
                return False
        
        if self.price_var.get().strip():
            try:
                Decimal(self.price_var.get())
            except InvalidOperation:
                messagebox.showerror("错误", "单价格式不正确")
                self.price_entry.focus()
                return False
        
        return True
    
    def _cancel(self):
        """取消操作"""
        self.result = False
        self.dialog.destroy()
    
    def show(self) -> bool:
        """显示对话框并返回结果"""
        self.dialog.wait_window()
        return self.result 