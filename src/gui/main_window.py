"""
WealthLite 主窗口
实现应用程序的主界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
from typing import Optional

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data.asset_manager import AssetManager
from models.asset import Asset
from models.category import CategoryManager
from gui.asset_list import AssetList
from gui.transaction_manager import TransactionManager
from gui.fixed_income_form import FixedIncomeForm
from gui.asset_form import AssetForm
from gui.asset_form_factory import AssetFormFactory
from gui.asset_type_selector import AssetTypeSelector
from config.config_manager import config_manager


class MainWindow:
    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        self.root = tk.Tk()
        
        # 使用配置管理器获取数据目录
        data_dir = config_manager.get_data_directory()
        self.asset_manager = AssetManager(data_dir)
        self.category_manager = CategoryManager()
        
        # 窗口配置
        self._setup_window()
        
        # 创建界面组件
        self._create_menu()
        self._create_toolbar()
        self._create_main_content()
        self._create_status_bar()
        
        # 加载数据
        self._load_data()
        
        # 绑定事件
        self._bind_events()
    
    def _setup_window(self):
        """设置窗口属性"""
        self.root.title("WealthLite - 轻量级资产管理工具")
        
        # 从配置获取窗口设置
        window_settings = config_manager.get_window_settings()
        width = window_settings.get('width', 1200)
        height = window_settings.get('height', 800)
        
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(800, 600)
        
        # 设置窗口位置
        if window_settings.get('maximized', False):
            self.root.state('zoomed')  # Windows下最大化
        else:
            pos_x = window_settings.get('position_x', 100)
            pos_y = window_settings.get('position_y', 100)
            self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        
        # 绑定窗口关闭事件以保存设置
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建资产", command=self._new_asset, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="导出Excel", command=self._export_excel)
        file_menu.add_command(label="备份数据", command=self._backup_data)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._quit_app, accelerator="Ctrl+Q")
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="编辑资产", command=self._edit_asset, accelerator="Ctrl+E")
        edit_menu.add_command(label="删除资产", command=self._delete_asset, accelerator="Delete")
        edit_menu.add_separator()
        edit_menu.add_command(label="刷新数据", command=self._refresh_data, accelerator="F5")
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)
    
    def _create_toolbar(self):
        """创建工具栏"""
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        # 新建按钮
        ttk.Button(self.toolbar, text="新建资产", command=self._new_asset).pack(side=tk.LEFT, padx=2)
        
        # 新建固定收益类产品按钮
        ttk.Button(self.toolbar, text="新建固定收益类", command=self._new_fixed_income).pack(side=tk.LEFT, padx=2)
        
        # 编辑按钮
        ttk.Button(self.toolbar, text="编辑", command=self._edit_asset).pack(side=tk.LEFT, padx=2)
        
        # 删除按钮
        ttk.Button(self.toolbar, text="删除", command=self._delete_asset).pack(side=tk.LEFT, padx=2)
        
        # 分隔符
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 刷新按钮
        ttk.Button(self.toolbar, text="刷新", command=self._refresh_data).pack(side=tk.LEFT, padx=2)
        
        # 导出按钮
        ttk.Button(self.toolbar, text="导出Excel", command=self._export_excel).pack(side=tk.LEFT, padx=2)
        
        # 搜索框
        ttk.Label(self.toolbar, text="搜索:").pack(side=tk.RIGHT, padx=2)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.toolbar, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.RIGHT, padx=2)
        self.search_entry.bind('<KeyRelease>', self._on_search)
    
    def _create_main_content(self):
        """创建主要内容区域"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建左右分割的PanedWindow
        self.paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧面板 - 资产列表
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=3)
        
        # 资产列表组件
        self.asset_list = AssetList(left_frame, self.asset_manager)
        self.asset_list.pack(fill=tk.BOTH, expand=True)
        
        # 右侧面板 - 详情和统计
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame, weight=1)
        
        # 创建右侧标签页
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 资产详情标签页
        self.details_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.details_frame, text="资产详情")
        self._create_details_panel()
        
        # 投资组合摘要标签页
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="投资组合")
        self._create_summary_panel()
    
    def _create_details_panel(self):
        """创建资产详情面板"""
        details_frame = ttk.LabelFrame(self.details_frame, text="资产详情", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 创建详情文本框和滚动条
        text_frame = ttk.Frame(details_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 文本框
        self.details_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            state=tk.DISABLED,
            font=('Consolas', 9)
        )
        self.details_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.details_text.yview)
        
        # 添加操作按钮框架
        button_frame = ttk.Frame(details_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 管理交易记录按钮
        self.manage_transactions_btn = ttk.Button(
            button_frame, 
            text="管理交易记录", 
            command=self._manage_transactions,
            state=tk.DISABLED
        )
        self.manage_transactions_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    def _create_summary_panel(self):
        """创建投资组合摘要面板"""
        # 摘要信息显示
        summary_scroll = ttk.Scrollbar(self.summary_frame)
        summary_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.summary_text = tk.Text(
            self.summary_frame,
            wrap=tk.WORD,
            yscrollcommand=summary_scroll.set,
            state=tk.DISABLED
        )
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        summary_scroll.config(command=self.summary_text.yview)
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 状态标签
        self.status_label = ttk.Label(self.status_bar, text="就绪")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 资产数量标签
        self.asset_count_label = ttk.Label(self.status_bar, text="资产: 0")
        self.asset_count_label.pack(side=tk.RIGHT, padx=5)
    
    def _bind_events(self):
        """绑定事件"""
        # 键盘快捷键
        self.root.bind('<Control-n>', lambda e: self._new_asset())
        self.root.bind('<Control-e>', lambda e: self._edit_asset())
        self.root.bind('<Control-q>', lambda e: self._quit_app())
        self.root.bind('<F5>', lambda e: self._refresh_data())
        self.root.bind('<Delete>', lambda e: self._delete_asset())
        
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._quit_app)
        
        # 资产列表选择事件
        self.asset_list.bind_selection_change(self._on_asset_selection_change)
    
    def _load_data(self):
        """加载数据"""
        try:
            self.asset_manager.load_data()
            self.asset_list.refresh()
            self._update_summary()
            self._update_status()
            self.status_label.config(text="数据加载完成")
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {e}")
    
    def _update_summary(self):
        """更新投资组合摘要"""
        try:
            summary = self.asset_manager.get_portfolio_summary()
            
            self.summary_text.config(state=tk.NORMAL)
            self.summary_text.delete(1.0, tk.END)
            
            content = f"""投资组合摘要
{'='*30}

总资产数量: {summary['total_assets']}
初始投资金额: ¥{summary['total_initial_amount']:,.2f}
当前总价值: ¥{summary['total_current_value']:,.2f}
总收益: ¥{summary['total_return']:,.2f}
总收益率: {summary['total_return_rate']:.2%}

分类明细:
{'-'*20}
"""
            
            for category, stats in summary['category_breakdown'].items():
                percentage = stats['current_value'] / summary['total_current_value'] if summary['total_current_value'] > 0 else 0
                content += f"""
{category}:
  数量: {stats['count']}
  价值: ¥{stats['current_value']:,.2f}
  占比: {percentage:.1%}
  收益率: {stats['return_rate']:.2%}
"""
            
            self.summary_text.insert(1.0, content)
            self.summary_text.config(state=tk.DISABLED)
            
        except Exception as e:
            print(f"更新摘要失败: {e}")
    
    def _update_status(self):
        """更新状态栏"""
        asset_count = len(self.asset_manager.get_all_assets())
        self.asset_count_label.config(text=f"资产: {asset_count}")
    
    def _on_asset_selection_change(self, asset: Optional[Asset]):
        """资产选择变化事件"""
        if asset:
            self._show_asset_details(asset)
            # 启用管理交易记录按钮
            self.manage_transactions_btn.config(state=tk.NORMAL)
        else:
            self._clear_asset_details()
            # 禁用管理交易记录按钮
            self.manage_transactions_btn.config(state=tk.DISABLED)
    
    def _show_asset_details(self, asset: Asset):
        """显示资产详情"""
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        
        content = f"""资产详情
{'='*30}

基本信息:
{'-'*20}
资产名称: {asset.asset_name}
一级分类: {asset.primary_category}
二级分类: {asset.secondary_category}
描述: {asset.description}
标签: {', '.join(asset.tags)}

投资信息:
{'-'*20}
初始投入: {asset.initial_amount:,.2f} {asset.currency}
当前价值: {asset.current_value:,.2f} {asset.currency}
汇率: {asset.exchange_rate} (1 {asset.currency} = {asset.exchange_rate} 人民币)
人民币价值: ¥{asset.get_initial_amount_in_cny():,.2f} → ¥{asset.get_current_value_in_cny():,.2f}
总收益: {asset.calculate_total_return():,.2f} {asset.currency} (¥{asset.calculate_total_return_in_cny():,.2f})
总收益率: {asset.calculate_total_return_rate():.2%}
年化回报率: {asset.calculate_annualized_return():.2%}

时间信息:
{'-'*20}
开始日期: {asset.start_date}
持有天数: {asset.calculate_holding_days()}
最后更新: {asset.last_update_date}
"""

        # 为固定收益类产品添加特殊信息
        if asset.is_fixed_income():
            content += f"""
固定收益类信息:
{'-'*20}
年利率: {asset.annual_rate}%
到期日期: {asset.maturity_date}
距离到期: {asset.get_days_to_maturity()}天
利息类型: {asset.interest_type}
付息频率: {asset.payment_frequency}
"""
            if asset.issuer:
                content += f"发行方: {asset.issuer}\n"
            if asset.credit_rating:
                content += f"信用评级: {asset.credit_rating}\n"
            if asset.coupon_rate:
                content += f"票面利率: {asset.coupon_rate}%\n"
            if asset.face_value:
                content += f"面值: ¥{asset.face_value:,.2f}\n"
            
            # 计算到期价值
            maturity_value = asset.calculate_maturity_value()
            maturity_value_cny = asset.calculate_maturity_value_in_cny()
            if maturity_value:
                content += f"预计到期价值: {maturity_value:,.2f} {asset.currency}"
                if maturity_value_cny and asset.currency != "人民币":
                    content += f" (¥{maturity_value_cny:,.2f})"
                content += "\n"
            
            if asset.is_matured():
                content += "状态: 已到期\n"
            else:
                content += "状态: 持有中\n"

        content += f"""
交易记录:
{'-'*20}
"""
        
        if asset.transactions:
            for i, transaction in enumerate(asset.transactions, 1):
                content += f"""
{i}. {transaction.transaction_type} - {transaction.transaction_date}
   金额: ¥{transaction.amount:,.2f}
   描述: {transaction.description}
"""
        else:
            content += "暂无交易记录"
        
        self.details_text.insert(1.0, content)
        self.details_text.config(state=tk.DISABLED)
    
    def _clear_asset_details(self):
        """清空资产详情"""
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        self.details_text.config(state=tk.DISABLED)
    
    def _on_search(self, event=None):
        """搜索事件"""
        keyword = self.search_var.get().strip()
        if keyword:
            results = self.asset_manager.search_assets(keyword)
            self.asset_list.show_assets(results)
            self.status_label.config(text=f"搜索到 {len(results)} 个资产")
        else:
            self.asset_list.refresh()
            self.status_label.config(text="显示所有资产")
    
    # 菜单和工具栏命令方法
    def _new_asset(self):
        """新建资产"""
        try:
            print("开始新建资产流程...")
            
            # 显示资产类型选择对话框
            print("创建资产类型选择器...")
            selector = AssetTypeSelector(self.root)
            
            print("显示选择器对话框...")
            selected_type = selector.show()
            
            print(f"用户选择的资产类型: {selected_type}")
            
            if not selected_type:
                print("用户取消了选择")
                return  # 用户取消了选择
            
            print(f"开始创建{selected_type}表单...")
            
            # 根据选择的类型创建对应的表单
            form = AssetFormFactory.create_form(
                self.root, 
                self.asset_manager, 
                self.category_manager, 
                asset_type=selected_type
            )
            
            print(f"表单创建成功: {type(form).__name__}")
            print("显示表单...")
            
            if form.show():
                print("表单保存成功，刷新界面...")
                self.asset_list.refresh()
                self._update_summary()
                self._update_status()
                self.status_label.config(text="资产添加成功")
            else:
                print("用户取消了表单")
                
        except Exception as e:
            print(f"新建资产时出错: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"新建资产失败: {e}")
    
    def _edit_asset(self):
        """编辑资产"""
        selected_asset = self.asset_list.get_selected_asset()
        if not selected_asset:
            messagebox.showwarning("警告", "请先选择要编辑的资产")
            return
        
        # 根据资产类型选择对应的表单
        form = AssetFormFactory.create_form(
            self.root, 
            self.asset_manager, 
            self.category_manager, 
            selected_asset
        )
        if form.show():
            self.asset_list.refresh()
            self._update_summary()
            self.status_label.config(text="资产更新成功")
    
    def _delete_asset(self):
        """删除资产"""
        selected_asset = self.asset_list.get_selected_asset()
        if not selected_asset:
            messagebox.showwarning("警告", "请先选择要删除的资产")
            return
        
        if messagebox.askyesno("确认删除", f"确定要删除资产 '{selected_asset.asset_name}' 吗？"):
            if self.asset_manager.delete_asset(selected_asset.asset_id):
                self.asset_list.refresh()
                self._update_summary()
                self._update_status()
                self._clear_asset_details()
                self.status_label.config(text="资产删除成功")
            else:
                messagebox.showerror("错误", "删除资产失败")
    
    def _refresh_data(self):
        """刷新数据"""
        self._load_data()
    
    def _export_excel(self):
        """导出Excel"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="导出Excel文件",
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
            )
            
            if file_path:
                if self.asset_manager.export_to_excel(file_path):
                    messagebox.showinfo("成功", f"Excel文件已导出到: {file_path}")
                    self.status_label.config(text="Excel导出成功")
                else:
                    messagebox.showerror("错误", "Excel导出失败")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {e}")
    
    def _backup_data(self):
        """备份数据"""
        try:
            if self.asset_manager.backup_data():
                messagebox.showinfo("成功", "数据备份完成")
                self.status_label.config(text="数据备份成功")
            else:
                messagebox.showerror("错误", "数据备份失败")
        except Exception as e:
            messagebox.showerror("错误", f"备份失败: {e}")
    
    def _show_about(self):
        """显示关于"""
        messagebox.showinfo("关于", "WealthLite v0.1.0\n\n轻量级资产分类与投资回报管理工具\n\n© 2024 WealthLite Team")
    
    def _quit_app(self):
        """退出应用"""
        if messagebox.askyesno("确认退出", "确定要退出WealthLite吗？"):
            # 保存数据
            try:
                self.asset_manager.save_data()
            except Exception as e:
                print(f"保存数据失败: {e}")
            
            self.root.quit()
            self.root.destroy()
    
    def _manage_transactions(self):
        """管理交易记录"""
        selected_asset = self.asset_list.get_selected_asset()
        if not selected_asset:
            messagebox.showwarning("警告", "请先选择要管理交易记录的资产")
            return
        
        # 打开交易记录管理窗口
        transaction_manager = TransactionManager(self.root, self.asset_manager, selected_asset)
        transaction_manager.show()
        
        # 刷新资产详情显示（可能有交易记录变更）
        self._show_asset_details(selected_asset)
        self._update_summary()
    
    def _new_fixed_income(self):
        """新建固定收益类产品"""
        try:
            form = FixedIncomeForm(self.root, self.asset_manager, self.category_manager)
            if form.show():
                self.asset_list.refresh()
                self._update_summary()
                self._update_status()
                self.status_label.config(text="固定收益类产品创建成功")
        except Exception as e:
            messagebox.showerror("错误", f"创建固定收益类产品失败: {e}")
    
    def _on_window_close(self):
        """窗口关闭事件"""
        # 保存窗口设置
        try:
            # 获取当前窗口状态
            is_maximized = self.root.state() == 'zoomed'
            
            if not is_maximized:
                # 获取窗口尺寸和位置
                geometry = self.root.geometry()
                # 解析geometry字符串 "widthxheight+x+y"
                size_pos = geometry.split('+')
                size = size_pos[0].split('x')
                width = int(size[0])
                height = int(size[1])
                pos_x = int(size_pos[1]) if len(size_pos) > 1 else 100
                pos_y = int(size_pos[2]) if len(size_pos) > 2 else 100
                
                # 保存窗口设置
                config_manager.set_user_setting('window_settings.width', width)
                config_manager.set_user_setting('window_settings.height', height)
                config_manager.set_user_setting('window_settings.position_x', pos_x)
                config_manager.set_user_setting('window_settings.position_y', pos_y)
            
            config_manager.set_user_setting('window_settings.maximized', is_maximized)
            print("窗口设置已保存")
            
        except Exception as e:
            print(f"保存窗口设置失败: {e}")
        
        self._quit_app()
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop() 