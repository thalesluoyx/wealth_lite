"""
WealthLite 资产表单组件
用于新建和编辑资产的对话框
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from models.asset import Asset, AssetTransaction
from models.category import CategoryManager
from data.asset_manager import AssetManager


class AssetForm:
    """资产表单对话框"""
    
    def __init__(self, parent, asset_manager: AssetManager, category_manager: CategoryManager, asset: Optional[Asset] = None):
        """
        初始化资产表单
        
        Args:
            parent: 父窗口
            asset_manager: 资产管理器
            category_manager: 分类管理器
            asset: 要编辑的资产（None表示新建）
        """
        self.parent = parent
        self.asset_manager = asset_manager
        self.category_manager = category_manager
        self.asset = asset
        self.result = False
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑资产" if asset else "新建资产")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self._center_dialog()
        
        # 创建界面
        self._create_widgets()
        self._setup_validation()
        
        # 如果是编辑模式，填充数据
        if self.asset:
            self._populate_data()
        
        # 设置焦点
        self.name_entry.focus()
    
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
        
        # 基本信息框架
        basic_frame = ttk.LabelFrame(main_frame, text="基本信息", padding="10")
        basic_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 资产名称
        ttk.Label(basic_frame, text="资产名称 *:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(basic_frame, textvariable=self.name_var, width=40)
        self.name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=(10, 0))
        
        # 一级分类
        ttk.Label(basic_frame, text="一级分类 *:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.primary_category_var = tk.StringVar()
        self.primary_category_combo = ttk.Combobox(
            basic_frame, 
            textvariable=self.primary_category_var,
            values=self.category_manager.get_primary_categories(),
            state="readonly",
            width=37
        )
        self.primary_category_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2, padx=(10, 0))
        self.primary_category_combo.bind('<<ComboboxSelected>>', self._on_primary_category_change)
        
        # 二级分类
        ttk.Label(basic_frame, text="二级分类 *:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.secondary_category_var = tk.StringVar()
        self.secondary_category_combo = ttk.Combobox(
            basic_frame,
            textvariable=self.secondary_category_var,
            state="readonly",
            width=37
        )
        self.secondary_category_combo.grid(row=2, column=1, sticky=tk.W+tk.E, pady=2, padx=(10, 0))
        
        # 描述
        ttk.Label(basic_frame, text="描述:").grid(row=3, column=0, sticky=tk.W+tk.N, pady=2)
        self.description_text = tk.Text(basic_frame, height=3, width=40)
        self.description_text.grid(row=3, column=1, sticky=tk.W+tk.E, pady=2, padx=(10, 0))
        
        # 配置列权重
        basic_frame.columnconfigure(1, weight=1)
        
        # 投资信息框架
        investment_frame = ttk.LabelFrame(main_frame, text="投资信息", padding="10")
        investment_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 初始投入
        ttk.Label(investment_frame, text="初始投入 *:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.initial_amount_var = tk.StringVar()
        self.initial_amount_entry = ttk.Entry(investment_frame, textvariable=self.initial_amount_var, width=20)
        self.initial_amount_entry.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        ttk.Label(investment_frame, text="元").grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        
        # 当前价值
        ttk.Label(investment_frame, text="当前价值 *:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.current_value_var = tk.StringVar()
        self.current_value_entry = ttk.Entry(investment_frame, textvariable=self.current_value_var, width=20)
        self.current_value_entry.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        ttk.Label(investment_frame, text="元").grid(row=1, column=2, sticky=tk.W, padx=(5, 0))
        
        # 开始日期
        ttk.Label(investment_frame, text="开始日期 *:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.start_date_var = tk.StringVar()
        self.start_date_entry = ttk.Entry(investment_frame, textvariable=self.start_date_var, width=20)
        self.start_date_entry.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        ttk.Label(investment_frame, text="(YYYY-MM-DD)").grid(row=2, column=2, sticky=tk.W, padx=(5, 0))
        
        # 设置默认日期为今天
        if not self.asset:
            self.start_date_var.set(date.today().strftime("%Y-%m-%d"))
        
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
        self.initial_amount_entry.config(validate='key', validatecommand=vcmd)
        self.current_value_entry.config(validate='key', validatecommand=vcmd)
    
    def _validate_number(self, value: str) -> bool:
        """验证数字输入"""
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _on_primary_category_change(self, event=None):
        """一级分类变化事件"""
        primary_category = self.primary_category_var.get()
        if primary_category:
            secondary_categories = self.category_manager.get_secondary_categories(primary_category)
            self.secondary_category_combo['values'] = secondary_categories
            self.secondary_category_var.set("")
    
    def _populate_data(self):
        """填充编辑数据"""
        if not self.asset:
            return
        
        # 基本信息
        self.name_var.set(self.asset.asset_name)
        self.primary_category_var.set(self.asset.primary_category)
        
        # 触发二级分类更新
        self._on_primary_category_change()
        self.secondary_category_var.set(self.asset.secondary_category)
        
        self.description_text.insert(1.0, self.asset.description)
        
        # 投资信息
        self.initial_amount_var.set(str(self.asset.initial_amount))
        self.current_value_var.set(str(self.asset.current_value))
        self.start_date_var.set(self.asset.start_date.strftime("%Y-%m-%d"))
    
    def _save(self):
        """保存资产"""
        # 验证必填字段
        if not self._validate_required_fields():
            return
        
        try:
            # 获取表单数据
            asset_name = self.name_var.get().strip()
            primary_category = self.primary_category_var.get()
            secondary_category = self.secondary_category_var.get()
            description = self.description_text.get(1.0, tk.END).strip()
            
            initial_amount = Decimal(self.initial_amount_var.get())
            current_value = Decimal(self.current_value_var.get())
            start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d").date()
            
            if self.asset:
                # 编辑模式
                self.asset.asset_name = asset_name
                self.asset.primary_category = primary_category
                self.asset.secondary_category = secondary_category
                self.asset.description = description
                self.asset.initial_amount = initial_amount
                self.asset.current_value = current_value
                self.asset.start_date = start_date
                self.asset.last_update_date = date.today()
                
                success = self.asset_manager.save_data()
            else:
                # 新建模式
                new_asset = Asset(
                    asset_name=asset_name,
                    primary_category=primary_category,
                    secondary_category=secondary_category,
                    initial_amount=initial_amount,
                    current_value=current_value,
                    start_date=start_date,
                    description=description
                )
                
                success = self.asset_manager.add_asset(new_asset)
            
            if success:
                self.result = True
                self.dialog.destroy()
            else:
                messagebox.showerror("错误", "保存资产失败")
                
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def _validate_required_fields(self) -> bool:
        """验证必填字段"""
        if not self.name_var.get().strip():
            messagebox.showwarning("警告", "请输入资产名称")
            self.name_entry.focus()
            return False
        
        if not self.primary_category_var.get():
            messagebox.showwarning("警告", "请选择一级分类")
            self.primary_category_combo.focus()
            return False
        
        if not self.secondary_category_var.get():
            messagebox.showwarning("警告", "请选择二级分类")
            self.secondary_category_combo.focus()
            return False
        
        if not self.initial_amount_var.get().strip():
            messagebox.showwarning("警告", "请输入初始投入")
            self.initial_amount_entry.focus()
            return False
        
        if not self.current_value_var.get().strip():
            messagebox.showwarning("警告", "请输入当前价值")
            self.current_value_entry.focus()
            return False
        
        if not self.start_date_var.get().strip():
            messagebox.showwarning("警告", "请输入开始日期")
            self.start_date_entry.focus()
            return False
        
        try:
            Decimal(self.initial_amount_var.get())
        except InvalidOperation:
            messagebox.showerror("错误", "初始投入金额格式不正确")
            self.initial_amount_entry.focus()
            return False
        
        try:
            Decimal(self.current_value_var.get())
        except InvalidOperation:
            messagebox.showerror("错误", "当前价值金额格式不正确")
            self.current_value_entry.focus()
            return False
        
        try:
            datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("错误", "开始日期格式不正确")
            self.start_date_entry.focus()
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