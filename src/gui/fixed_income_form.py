"""
固定收益类产品表单

提供固定收益类产品的新建和编辑界面。
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from data.asset_manager import AssetManager
from models.category import CategoryManager
from models.asset import Asset
from models.fixed_income import Currency, ExchangeRateManager


class FixedIncomeForm:
    """固定收益类产品表单"""
    
    def __init__(self, parent, asset_manager: AssetManager, category_manager: CategoryManager, asset: Optional[Asset] = None):
        self.parent = parent
        self.asset_manager = asset_manager
        self.category_manager = category_manager
        self.asset = asset
        self.is_edit_mode = asset is not None
        self.exchange_rate_manager = ExchangeRateManager()
        self.manual_input_mode = False
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑固定收益类产品" if self.is_edit_mode else "新建固定收益类产品")
        self.dialog.geometry("650x700")  # 恢复合理的高度
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self._center_dialog()
        
        # 创建界面
        self._create_widgets()
        self._setup_validation()
        self._bind_events()
        
        # 如果是编辑模式，填充数据
        if self.asset:
            self._populate_data()
        else:
            self._set_default_values()
        
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
        # 按钮框架 - 固定在窗口底部
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
        
        # 保存按钮
        ttk.Button(button_frame, text="保存", command=self._save).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 取消按钮
        ttk.Button(button_frame, text="取消", command=self._cancel).pack(side=tk.RIGHT)
        
        # 创建滚动区域
        canvas_frame = ttk.Frame(self.dialog)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建Canvas和滚动条
        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # 配置滚动
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # 布局Canvas和滚动条
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 绑定鼠标滚轮事件
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        
        # 绑定Canvas大小调整事件
        self.canvas.bind("<Configure>", self._update_canvas_width)
        
        # 主内容框架
        main_frame = ttk.Frame(self.scrollable_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 基本信息框架
        basic_frame = ttk.LabelFrame(main_frame, text="基本信息", padding="10")
        basic_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 产品名称
        ttk.Label(basic_frame, text="产品名称 *:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(basic_frame, textvariable=self.name_var, width=40)
        self.name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=(10, 0))
        
        # 产品类型
        ttk.Label(basic_frame, text="产品类型 *:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.secondary_category_var = tk.StringVar()
        self.secondary_category_combo = ttk.Combobox(
            basic_frame,
            textvariable=self.secondary_category_var,
            values=["定期存款", "国债", "企业债", "债券基金"],
            state="readonly",
            width=37
        )
        self.secondary_category_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2, padx=(10, 0))
        
        # 描述
        ttk.Label(basic_frame, text="描述:").grid(row=2, column=0, sticky=tk.W+tk.N, pady=2)
        self.description_text = tk.Text(basic_frame, height=2, width=40)
        self.description_text.grid(row=2, column=1, sticky=tk.W+tk.E, pady=2, padx=(10, 0))
        
        # 配置列权重
        basic_frame.columnconfigure(1, weight=1)
        
        # 投资信息框架
        investment_frame = ttk.LabelFrame(main_frame, text="投资信息", padding="10")
        investment_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 投资本金
        ttk.Label(investment_frame, text="投资本金 *:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.initial_amount_var = tk.StringVar()
        self.initial_amount_entry = ttk.Entry(investment_frame, textvariable=self.initial_amount_var, width=20)
        self.initial_amount_entry.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        ttk.Label(investment_frame, text="元").grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        
        # 当前价值
        ttk.Label(investment_frame, text="当前价值:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.current_value_var = tk.StringVar()
        self.current_value_entry = ttk.Entry(investment_frame, textvariable=self.current_value_var, width=20, state="readonly")
        self.current_value_entry.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        self.current_value_label = ttk.Label(investment_frame, text="元 (自动计算)")
        self.current_value_label.grid(row=1, column=2, sticky=tk.W, padx=(5, 0))
        
        # 添加手动输入按钮
        self.manual_value_btn = ttk.Button(investment_frame, text="手动输入", command=self._toggle_manual_value)
        self.manual_value_btn.grid(row=1, column=3, sticky=tk.W, padx=(5, 0))
        
        # 起息日期
        ttk.Label(investment_frame, text="起息日期 *:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.start_date_var = tk.StringVar()
        self.start_date_entry = ttk.Entry(investment_frame, textvariable=self.start_date_var, width=20)
        self.start_date_entry.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        ttk.Label(investment_frame, text="(YYYY-MM-DD)").grid(row=2, column=2, sticky=tk.W, padx=(5, 0))
        
        # 币种和汇率框架
        currency_frame = ttk.LabelFrame(main_frame, text="币种和汇率", padding="10")
        currency_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 投资币种
        ttk.Label(currency_frame, text="投资币种 *:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.currency_var = tk.StringVar(value="人民币")
        self.currency_combo = ttk.Combobox(
            currency_frame,
            textvariable=self.currency_var,
            values=["人民币", "港元", "美元", "澳元"],
            state="readonly",
            width=17
        )
        self.currency_combo.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # 汇率
        ttk.Label(currency_frame, text="汇率 *:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.exchange_rate_var = tk.StringVar(value="1.0000")
        self.exchange_rate_entry = ttk.Entry(currency_frame, textvariable=self.exchange_rate_var, width=20)
        self.exchange_rate_entry.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # 更新汇率按钮
        self.update_rate_btn = ttk.Button(currency_frame, text="更新汇率", command=self._update_exchange_rate)
        self.update_rate_btn.grid(row=1, column=2, sticky=tk.W, padx=(5, 0))
        
        # 汇率说明
        self.rate_hint_label = ttk.Label(currency_frame, text="1 人民币 = 1.0000 人民币", foreground="gray")
        self.rate_hint_label.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=2, padx=(10, 0))
        
        # 人民币参考价
        ttk.Label(currency_frame, text="人民币参考价:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.cny_reference_label = ttk.Label(currency_frame, text="0.00 元", foreground="blue", font=("TkDefaultFont", 9, "bold"))
        self.cny_reference_label.grid(row=3, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # 固定收益类特殊参数框架
        fixed_income_frame = ttk.LabelFrame(main_frame, text="固定收益类参数", padding="10")
        fixed_income_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 年利率
        ttk.Label(fixed_income_frame, text="年利率 *:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.annual_rate_var = tk.StringVar()
        self.annual_rate_entry = ttk.Entry(fixed_income_frame, textvariable=self.annual_rate_var, width=20)
        self.annual_rate_entry.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        ttk.Label(fixed_income_frame, text="%").grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        
        # 到期日期
        ttk.Label(fixed_income_frame, text="到期日期 *:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.maturity_date_var = tk.StringVar()
        self.maturity_date_entry = ttk.Entry(fixed_income_frame, textvariable=self.maturity_date_var, width=20)
        self.maturity_date_entry.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        ttk.Label(fixed_income_frame, text="(YYYY-MM-DD)").grid(row=1, column=2, sticky=tk.W, padx=(5, 0))
        
        # 投资期限（自动计算）
        ttk.Label(fixed_income_frame, text="投资期限:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.term_label = ttk.Label(fixed_income_frame, text="请输入起息日期和到期日期", foreground="gray")
        self.term_label.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=2, padx=(10, 0))
        
        # 利息类型
        ttk.Label(fixed_income_frame, text="利息类型:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.interest_type_var = tk.StringVar(value="复利")
        self.interest_type_combo = ttk.Combobox(
            fixed_income_frame,
            textvariable=self.interest_type_var,
            values=["单利", "复利", "浮动利率"],
            state="readonly",
            width=17
        )
        self.interest_type_combo.grid(row=3, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # 付息频率
        ttk.Label(fixed_income_frame, text="付息频率:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.payment_frequency_var = tk.StringVar(value="到期一次性付息")
        self.payment_frequency_combo = ttk.Combobox(
            fixed_income_frame,
            textvariable=self.payment_frequency_var,
            values=["到期一次性付息", "年付", "半年付", "季付", "月付"],
            state="readonly",
            width=17
        )
        self.payment_frequency_combo.grid(row=4, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # 可选参数框架
        optional_frame = ttk.LabelFrame(main_frame, text="可选参数", padding="10")
        optional_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 发行方
        ttk.Label(optional_frame, text="发行方:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.issuer_var = tk.StringVar()
        self.issuer_entry = ttk.Entry(optional_frame, textvariable=self.issuer_var, width=20)
        self.issuer_entry.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # 信用评级
        ttk.Label(optional_frame, text="信用评级:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.credit_rating_var = tk.StringVar()
        self.credit_rating_combo = ttk.Combobox(
            optional_frame,
            textvariable=self.credit_rating_var,
            values=["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-"],
            width=17
        )
        self.credit_rating_combo.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # 票面利率
        ttk.Label(optional_frame, text="票面利率:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.coupon_rate_var = tk.StringVar()
        self.coupon_rate_entry = ttk.Entry(optional_frame, textvariable=self.coupon_rate_var, width=20)
        self.coupon_rate_entry.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        ttk.Label(optional_frame, text="%").grid(row=2, column=2, sticky=tk.W, padx=(5, 0))
        
        # 面值
        ttk.Label(optional_frame, text="面值:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.face_value_var = tk.StringVar()
        self.face_value_entry = ttk.Entry(optional_frame, textvariable=self.face_value_var, width=20)
        self.face_value_entry.grid(row=3, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        ttk.Label(optional_frame, text="元").grid(row=3, column=2, sticky=tk.W, padx=(5, 0))
    
    def _setup_validation(self):
        """设置输入验证"""
        # 数字验证
        vcmd = (self.dialog.register(self._validate_number), '%P')
        self.initial_amount_entry.config(validate='key', validatecommand=vcmd)
        self.annual_rate_entry.config(validate='key', validatecommand=vcmd)
        self.exchange_rate_entry.config(validate='key', validatecommand=vcmd)
        self.coupon_rate_entry.config(validate='key', validatecommand=vcmd)
        self.face_value_entry.config(validate='key', validatecommand=vcmd)
    
    def _validate_number(self, value):
        """验证数字输入"""
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _bind_events(self):
        """绑定事件"""
        # 日期变化时更新投资期限
        self.start_date_var.trace('w', self._update_term)
        self.maturity_date_var.trace('w', self._update_term)
        
        # 产品类型变化时设置默认值
        self.secondary_category_var.trace('w', self._on_product_type_change)
        
        # 币种变化时更新汇率
        self.currency_var.trace('w', self._on_currency_change)
        
        # 汇率和本金变化时更新人民币参考价
        self.exchange_rate_var.trace('w', self._update_cny_reference)
        self.initial_amount_var.trace('w', self._update_cny_reference)
        
        # 当前价值自动计算相关
        self.initial_amount_var.trace('w', self._auto_calculate_current_value)
        self.annual_rate_var.trace('w', self._auto_calculate_current_value)
        self.start_date_var.trace('w', self._auto_calculate_current_value)
        self.interest_type_var.trace('w', self._auto_calculate_current_value)
    
    def _on_currency_change(self, *args):
        """币种变化时的处理"""
        currency_text = self.currency_var.get()
        
        # 根据币种映射到Currency枚举
        currency_map = {
            "人民币": Currency.CNY,
            "港元": Currency.HKD,
            "美元": Currency.USD,
            "澳元": Currency.AUD
        }
        
        currency = currency_map.get(currency_text, Currency.CNY)
        
        # 更新汇率
        default_rate = self.exchange_rate_manager.get_rate(currency)
        self.exchange_rate_var.set(f"{default_rate:.4f}")
        
        # 更新汇率说明
        self._update_rate_hint()
        
        # 更新人民币参考价
        self._update_cny_reference()
    
    def _update_exchange_rate(self):
        """更新汇率按钮点击处理"""
        currency_text = self.currency_var.get()
        
        # 这里可以集成实时汇率API，目前使用默认汇率
        currency_map = {
            "人民币": Currency.CNY,
            "港元": Currency.HKD,
            "美元": Currency.USD,
            "澳元": Currency.AUD
        }
        
        currency = currency_map.get(currency_text, Currency.CNY)
        default_rate = self.exchange_rate_manager.get_rate(currency)
        self.exchange_rate_var.set(f"{default_rate:.4f}")
        
        messagebox.showinfo("汇率更新", f"已更新{currency_text}汇率为 {default_rate}")
    
    def _update_rate_hint(self):
        """更新汇率说明"""
        currency_text = self.currency_var.get()
        try:
            rate = float(self.exchange_rate_var.get())
            self.rate_hint_label.config(text=f"1 {currency_text} = {rate:.4f} 人民币")
        except ValueError:
            self.rate_hint_label.config(text="汇率格式错误")
    
    def _update_cny_reference(self, *args):
        """更新人民币参考价"""
        try:
            principal = float(self.initial_amount_var.get() or "0")
            rate = float(self.exchange_rate_var.get() or "1")
            cny_value = principal * rate
            self.cny_reference_label.config(text=f"{cny_value:.2f} 元")
        except ValueError:
            self.cny_reference_label.config(text="计算错误")
    
    def _update_term(self, *args):
        """更新投资期限"""
        try:
            start_date_str = self.start_date_var.get()
            maturity_date_str = self.maturity_date_var.get()
            
            if start_date_str and maturity_date_str:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                maturity_date = datetime.strptime(maturity_date_str, "%Y-%m-%d").date()
                
                if maturity_date > start_date:
                    days = (maturity_date - start_date).days
                    years = round(days / 365.25, 1)
                    self.term_label.config(text=f"{days} 天 ({years} 年)")
                else:
                    self.term_label.config(text="无效期限")
            else:
                self.term_label.config(text="请输入起息日期和到期日期")
        except ValueError:
            self.term_label.config(text="日期格式错误")
    
    def _on_product_type_change(self, *args):
        """产品类型变化时的处理"""
        product_type = self.secondary_category_var.get()
        
        # 根据产品类型设置默认值
        if product_type == "定期存款":
            self.annual_rate_var.set("3.50")
            self.interest_type_var.set("复利")
            self.payment_frequency_var.set("到期一次性付息")
            self.credit_rating_var.set("")
            self.issuer_var.set("")
        elif product_type == "国债":
            self.annual_rate_var.set("3.20")
            self.interest_type_var.set("复利")
            self.payment_frequency_var.set("年付")
            self.credit_rating_var.set("AAA")
            self.issuer_var.set("财政部")
        elif product_type == "企业债":
            self.annual_rate_var.set("4.50")
            self.interest_type_var.set("复利")
            self.payment_frequency_var.set("年付")
            self.credit_rating_var.set("AA")
            self.issuer_var.set("")
        elif product_type == "债券基金":
            self.annual_rate_var.set("4.00")
            self.interest_type_var.set("复利")
            self.payment_frequency_var.set("到期一次性付息")
            self.credit_rating_var.set("")
            self.issuer_var.set("")
    
    def _set_default_values(self):
        """设置默认值"""
        # 设置默认日期为今天
        self.start_date_var.set(date.today().strftime("%Y-%m-%d"))
        
        # 设置默认产品类型
        self.secondary_category_var.set("定期存款")
        self._on_product_type_change()
        
        # 设置默认币种
        self.currency_var.set("人民币")
        self._on_currency_change()
    
    def _populate_data(self):
        """填充编辑数据"""
        if not self.asset:
            return
        
        # 基本信息
        self.name_var.set(self.asset.asset_name)
        self.secondary_category_var.set(self.asset.secondary_category)
        self.description_text.insert("1.0", self.asset.description)
        
        # 投资信息
        self.initial_amount_var.set(str(self.asset.initial_amount))
        self.start_date_var.set(self.asset.start_date.strftime("%Y-%m-%d"))
        self.current_value_var.set(str(self.asset.current_value))
        
        # 币种和汇率
        self.currency_var.set(self.asset.currency)
        self.exchange_rate_var.set(str(self.asset.exchange_rate))
        
        # 固定收益类参数
        if self.asset.annual_rate:
            self.annual_rate_var.set(str(self.asset.annual_rate))
        
        if self.asset.maturity_date:
            self.maturity_date_var.set(self.asset.maturity_date.strftime("%Y-%m-%d"))
        
        if self.asset.interest_type:
            self.interest_type_var.set(self.asset.interest_type)
        
        if self.asset.payment_frequency:
            self.payment_frequency_var.set(self.asset.payment_frequency)
        
        # 可选参数
        if self.asset.issuer:
            self.issuer_var.set(self.asset.issuer)
        
        if self.asset.credit_rating:
            self.credit_rating_var.set(self.asset.credit_rating)
        
        if self.asset.coupon_rate:
            self.coupon_rate_var.set(str(self.asset.coupon_rate))
        
        if self.asset.face_value:
            self.face_value_var.set(str(self.asset.face_value))
        
        # 判断是否使用手动输入模式
        auto_calculated = self._calculate_auto_value()
        if abs(float(self.asset.current_value) - auto_calculated) > 0.01:
            # 当前价值与自动计算值差异较大，切换到手动输入模式
            self._toggle_manual_value()
    
    def _save(self):
        """保存资产"""
        print("=== 开始保存固定收益类资产 ===")
        
        if not self._validate_required_fields():
            print("验证失败，取消保存")
            return
        
        try:
            # 创建或更新资产对象
            if self.is_edit_mode:
                asset = self.asset
                print(f"编辑模式：更新资产 {asset.asset_id}")
            else:
                asset = Asset()
                print("新建模式：创建新资产")
            
            # 基本信息
            asset.asset_name = self.name_var.get().strip()
            asset.primary_category = "固定收益类"
            asset.secondary_category = self.secondary_category_var.get()
            asset.description = self.description_text.get("1.0", tk.END).strip()
            
            print(f"资产名称: {asset.asset_name}")
            print(f"主分类: {asset.primary_category}")
            print(f"子分类: {asset.secondary_category}")
            
            # 投资信息
            asset.initial_amount = Decimal(self.initial_amount_var.get())
            asset.start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d").date()
            
            # 当前价值处理
            current_value_str = self.current_value_var.get()
            if current_value_str:
                asset.current_value = Decimal(current_value_str)
            else:
                asset.current_value = asset.initial_amount
            
            print(f"投资本金: {asset.initial_amount}")
            print(f"当前价值: {asset.current_value}")
            print(f"起息日期: {asset.start_date}")
            
            # 币种和汇率
            asset.currency = self.currency_var.get()
            asset.exchange_rate = Decimal(self.exchange_rate_var.get())
            
            print(f"币种: {asset.currency}")
            print(f"汇率: {asset.exchange_rate}")
            
            # 固定收益类参数
            asset.annual_rate = Decimal(self.annual_rate_var.get())
            asset.maturity_date = datetime.strptime(self.maturity_date_var.get(), "%Y-%m-%d").date()
            asset.interest_type = self.interest_type_var.get()
            asset.payment_frequency = self.payment_frequency_var.get()
            
            print(f"年利率: {asset.annual_rate}%")
            print(f"到期日期: {asset.maturity_date}")
            print(f"利息类型: {asset.interest_type}")
            
            # 可选参数
            asset.issuer = self.issuer_var.get().strip() or None
            asset.credit_rating = self.credit_rating_var.get().strip() or None
            
            coupon_rate_str = self.coupon_rate_var.get()
            asset.coupon_rate = Decimal(coupon_rate_str) if coupon_rate_str else None
            
            face_value_str = self.face_value_var.get()
            asset.face_value = Decimal(face_value_str) if face_value_str else None
            
            # 更新时间戳
            if not self.is_edit_mode:
                asset.created_date = datetime.now()
            asset.updated_date = datetime.now()
            asset.last_update_date = date.today()
            
            print(f"资产ID: {asset.asset_id}")
            
            # 保存资产
            if self.is_edit_mode:
                print("调用 update_asset...")
                # 直接更新现有资产对象的属性，不需要调用update_asset方法
                success = True  # 因为我们已经直接修改了asset对象
            else:
                print("调用 add_asset...")
                success = self.asset_manager.add_asset(asset)
            
            print(f"保存结果: {success}")
            
            if success:
                print("保存成功，调用 save_data...")
                save_result = self.asset_manager.save_data()
                print(f"数据持久化结果: {save_result}")
                
                if save_result:
                    self.asset = asset
                    print("关闭对话框")
                    self.dialog.destroy()
                    messagebox.showinfo("成功", "资产保存成功！")
                else:
                    messagebox.showerror("保存错误", "数据保存到文件失败")
            else:
                print("保存失败")
                messagebox.showerror("保存错误", "资产保存失败，可能是名称重复或分类不存在")
            
        except Exception as e:
            print(f"保存过程中发生异常: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("保存错误", f"保存资产时发生错误：{str(e)}")
    
    def _validate_required_fields(self) -> bool:
        """验证必填字段"""
        # 验证资产名称
        if not self.name_var.get().strip():
            messagebox.showerror("验证错误", "请输入资产名称")
            self.name_entry.focus()
            return False
        
        # 验证投资本金
        try:
            initial_amount = float(self.initial_amount_var.get())
            if initial_amount <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            messagebox.showerror("验证错误", "请输入有效的投资本金")
            self.initial_amount_entry.focus()
            return False
        
        # 验证年利率
        try:
            annual_rate = float(self.annual_rate_var.get())
            if annual_rate <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            messagebox.showerror("验证错误", "请输入有效的年利率")
            self.annual_rate_entry.focus()
            return False
        
        # 验证汇率
        try:
            exchange_rate = float(self.exchange_rate_var.get())
            if exchange_rate <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            messagebox.showerror("验证错误", "请输入有效的汇率")
            self.exchange_rate_entry.focus()
            return False
        
        # 验证起息日期
        try:
            start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("验证错误", "请输入有效的起息日期 (YYYY-MM-DD)")
            self.start_date_entry.focus()
            return False
        
        # 验证到期日期
        try:
            maturity_date = datetime.strptime(self.maturity_date_var.get(), "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("验证错误", "请输入有效的到期日期 (YYYY-MM-DD)")
            self.maturity_date_entry.focus()
            return False
        
        # 验证日期逻辑
        if maturity_date <= start_date:
            messagebox.showerror("验证错误", "到期日期必须晚于起息日期")
            self.maturity_date_entry.focus()
            return False
        
        return True
    
    def _cancel(self):
        """取消操作"""
        self.dialog.destroy()
    
    def show(self) -> bool:
        """显示对话框并返回是否保存"""
        self.dialog.wait_window()
        return hasattr(self, 'asset') and self.asset is not None
    
    def _toggle_manual_value(self):
        """切换手动输入模式"""
        if self.manual_input_mode:
            # 切换到自动计算模式
            self.current_value_entry.config(state="readonly")
            self.current_value_label.config(text="元 (自动计算)")
            self.manual_value_btn.config(text="手动输入")
            self.manual_input_mode = False
            # 重新计算当前价值
            self._auto_calculate_current_value()
        else:
            # 切换到手动输入模式
            self.current_value_entry.config(state="normal")
            self.current_value_label.config(text="元 (手动输入)")
            self.manual_value_btn.config(text="自动计算")
            self.manual_input_mode = True
    
    def _auto_calculate_current_value(self, *args):
        """自动计算当前价值"""
        if self.manual_input_mode:
            return  # 手动输入模式下不自动更新
        
        try:
            current_value = self._calculate_auto_value()
            self.current_value_var.set(f"{current_value:.2f}")
        except Exception as e:
            print(f"计算当前价值时出错: {e}")
    
    def _calculate_auto_value(self) -> float:
        """计算自动价值"""
        try:
            principal = float(self.initial_amount_var.get() or "0")
            annual_rate = float(self.annual_rate_var.get() or "0")
            start_date_str = self.start_date_var.get().strip()
            interest_type = self.interest_type_var.get()
            
            if not start_date_str or principal <= 0 or annual_rate <= 0:
                return principal
            
            # 验证日期格式
            if len(start_date_str) != 10 or start_date_str.count('-') != 2:
                return principal
                
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            
            # 计算已持有天数
            today = date.today()
            if today <= start_date:
                return principal  # 还未起息
            
            held_days = (today - start_date).days
            held_years = held_days / 365.25
            
            # 根据利息类型计算当前价值
            rate = annual_rate / 100
            
            if interest_type == "单利":
                current_value = principal * (1 + rate * held_years)
            else:  # 复利或浮动利率按复利计算
                current_value = principal * (1 + rate) ** held_years
            
            return current_value
            
        except Exception as e:
            print(f"自动计算当前价值出错: {e}")
            return float(self.initial_amount_var.get() or "0")
    
    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _update_canvas_width(self, event=None):
        """更新Canvas宽度以适应内容"""
        canvas_width = self.canvas.winfo_width()
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
