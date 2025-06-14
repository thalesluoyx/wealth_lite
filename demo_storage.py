#!/usr/bin/env python3
"""
WealthLite 数据存储功能演示脚本
展示CSV存储、JSON配置和资产管理器的使用
"""

import sys
import os
from pathlib import Path
from decimal import Decimal
from datetime import date, datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.asset_manager import AssetManager
from src.models.asset import Asset, AssetTransaction


def create_sample_assets():
    """创建示例资产数据"""
    assets = []
    
    # 1. 股票投资
    stock_asset = Asset(
        asset_name="招商银行股票",
        primary_category="权益类",
        secondary_category="股票",
        initial_amount=Decimal("50000"),
        current_value=Decimal("58000"),
        start_date=date(2024, 1, 15),
        description="银行股投资，稳健型"
    )
    stock_asset.add_tag("蓝筹股")
    stock_asset.add_tag("银行")
    
    # 添加交易记录
    stock_asset.add_transaction(AssetTransaction(
        transaction_type="买入",
        amount=Decimal("50000"),
        description="初始买入"
    ))
    stock_asset.add_transaction(AssetTransaction(
        transaction_type="分红",
        amount=Decimal("1200"),
        description="年度分红"
    ))
    
    assets.append(stock_asset)
    
    # 2. 基金投资
    fund_asset = Asset(
        asset_name="易方达蓝筹精选",
        primary_category="权益类",
        secondary_category="股票型基金",
        initial_amount=Decimal("30000"),
        current_value=Decimal("32500"),
        start_date=date(2024, 2, 1),
        description="主动管理型股票基金"
    )
    fund_asset.add_tag("主动基金")
    fund_asset.add_tag("大盘股")
    
    fund_asset.add_transaction(AssetTransaction(
        transaction_type="买入",
        amount=Decimal("30000"),
        description="定投开始"
    ))
    
    assets.append(fund_asset)
    
    # 3. 定期存款
    deposit_asset = Asset(
        asset_name="工商银行定期存款",
        primary_category="固定收益类",
        secondary_category="定期存款",
        initial_amount=Decimal("100000"),
        current_value=Decimal("103000"),
        start_date=date(2024, 1, 1),
        description="一年期定期存款，年利率3%"
    )
    deposit_asset.add_tag("保本")
    deposit_asset.add_tag("低风险")
    
    deposit_asset.add_transaction(AssetTransaction(
        transaction_type="存入",
        amount=Decimal("100000"),
        description="定期存款"
    ))
    
    assets.append(deposit_asset)
    
    # 4. 货币基金
    money_fund = Asset(
        asset_name="余额宝",
        primary_category="现金及等价物",
        secondary_category="货币基金",
        initial_amount=Decimal("20000"),
        current_value=Decimal("20400"),
        start_date=date(2024, 1, 1),
        description="日常流动资金管理"
    )
    money_fund.add_tag("流动性高")
    money_fund.add_tag("低风险")
    
    money_fund.add_transaction(AssetTransaction(
        transaction_type="转入",
        amount=Decimal("20000"),
        description="初始转入"
    ))
    
    assets.append(money_fund)
    
    return assets


def main():
    """主演示函数"""
    print("=" * 60)
    print("WealthLite 数据存储功能演示")
    print("=" * 60)
    
    # 创建资产管理器
    print("\n1. 初始化资产管理器...")
    manager = AssetManager("demo_data")
    
    # 创建示例资产
    print("\n2. 创建示例资产...")
    sample_assets = create_sample_assets()
    
    for asset in sample_assets:
        success = manager.add_asset(asset)
        if success:
            print(f"   ✓ 添加资产: {asset.asset_name}")
        else:
            print(f"   ✗ 添加失败: {asset.asset_name}")
    
    # 保存数据
    print("\n3. 保存数据到文件...")
    save_success = manager.save_data()
    if save_success:
        print("   ✓ 数据保存成功")
    else:
        print("   ✗ 数据保存失败")
    
    # 获取投资组合摘要
    print("\n4. 投资组合摘要:")
    summary = manager.get_portfolio_summary()
    print(f"   总资产数量: {summary['total_assets']}")
    print(f"   初始投资金额: ¥{summary['total_initial_amount']:,.2f}")
    print(f"   当前总价值: ¥{summary['total_current_value']:,.2f}")
    print(f"   总收益: ¥{summary['total_return']:,.2f}")
    print(f"   总收益率: {summary['total_return_rate']:.2%}")
    
    # 分类统计
    print("\n5. 资产分类统计:")
    for category, stats in summary['category_breakdown'].items():
        percentage = stats['current_value'] / summary['total_current_value'] if summary['total_current_value'] > 0 else 0
        print(f"   {category}:")
        print(f"     数量: {stats['count']}")
        print(f"     价值: ¥{stats['current_value']:,.2f}")
        print(f"     占比: {percentage:.1%}")
        print(f"     收益率: {stats['return_rate']:.2%}")
    
    # 搜索功能演示
    print("\n6. 搜索功能演示:")
    search_results = manager.search_assets("银行")
    print(f"   搜索'银行'找到 {len(search_results)} 个资产:")
    for asset in search_results:
        print(f"     - {asset.asset_name}")
    
    # 按分类获取资产
    print("\n7. 按分类获取资产:")
    equity_assets = manager.get_assets_by_category("权益类")
    print(f"   权益类资产 ({len(equity_assets)} 个):")
    for asset in equity_assets:
        return_rate = asset.calculate_annualized_return()
        print(f"     - {asset.asset_name}: 年化收益率 {return_rate:.2%}")
    
    # 数据统计
    print("\n8. 数据统计信息:")
    stats = manager.get_data_statistics()
    print(f"   资产总数: {stats['assets_count']}")
    print(f"   交易记录数: {stats['transactions_count']}")
    print(f"   分类数量: {stats['categories_count']}")
    print(f"   数据已加载: {stats['data_loaded']}")
    
    # 导出Excel报告
    print("\n9. 导出Excel报告...")
    excel_file = "demo_data/portfolio_report.xlsx"
    export_success = manager.export_to_excel(excel_file)
    if export_success:
        print(f"   ✓ Excel报告已导出: {excel_file}")
    else:
        print("   ✗ Excel导出失败")
    
    # 配置管理演示
    print("\n10. 配置管理演示:")
    config = manager.json_storage.load_config()
    print(f"    应用版本: {config['version']}")
    print(f"    货币符号: {config['display_settings']['currency_symbol']}")
    print(f"    小数位数: {config['display_settings']['decimal_places']}")
    
    # 用户设置演示
    print("\n11. 用户设置演示:")
    settings = manager.json_storage.load_settings()
    print(f"    自动保存: {settings['user_preferences']['auto_save']}")
    print(f"    窗口大小: {settings['window_settings']['width']}x{settings['window_settings']['height']}")
    print(f"    主题: {settings['user_preferences']['theme']}")
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("生成的文件:")
    print("  - demo_data/assets.csv (资产数据)")
    print("  - demo_data/transactions.csv (交易记录)")
    print("  - demo_data/config.json (应用配置)")
    print("  - demo_data/settings.json (用户设置)")
    print("  - demo_data/portfolio_report.xlsx (Excel报告)")
    print("=" * 60)


if __name__ == "__main__":
    main() 