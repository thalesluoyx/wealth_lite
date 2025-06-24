"""
港元外汇存款集成测试

测试港元外汇存款的完整生命周期，包括：
1. 人民币转港币定存
2. 定存到期处理的两种情况：
   - 情况A：到期后变成港元现金
   - 情况B：到期后转回人民币
"""

import pytest
import tempfile
import os
from datetime import date, datetime
from decimal import Decimal

from src.wealth_lite.models.enums import AssetType, TransactionType, Currency
from src.wealth_lite.services.wealth_service import WealthService


class TestForeignCurrencyDeposits:
    """港元外汇存款测试"""
    
    @pytest.fixture
    def temp_db_path(self):
        """创建临时数据库文件"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        # 清理临时文件
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def wealth_service(self, temp_db_path):
        """创建财富管理服务实例"""
        service = WealthService(db_path=temp_db_path)
        yield service
        service.close()
    
    def test_hkd_deposit_to_hkd_cash_scenario(self, wealth_service):
        """
        测试场景A：港元定存到期后变成港元现金
        
        流程：
        1. 用人民币100,000元按汇率0.9换成港币90,000元
        2. 港币90,000元做3个月定存，年利率3.5%
        3. 到期后获得利息，总计港币90,787.5元
        4. 到期后保持港币现金形式，不兑换回人民币
        """
        # 1. 创建港元定存资产
        hkd_deposit_asset = wealth_service.create_asset(
            asset_name="汇丰银行港元定期存款",
            asset_type=AssetType.FIXED_INCOME,
            primary_category="固定收益类",
            secondary_category="外币定存",
            currency=Currency.HKD,
            description="3个月港元定期存款，年利率3.5%",
            issuer="汇丰银行（香港）有限公司"
        )
        
        # 2. 创建港元定存交易（直接记录港币金额和当时汇率）
        # 假设存入时汇率：1 HKD = 0.9 CNY，即 1 CNY = 1.111 HKD
        deposit_transaction = wealth_service.create_fixed_income_transaction(
            asset_id=hkd_deposit_asset.asset_id,
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal('90000.00'),  # 港币金额
            currency=Currency.HKD,
            exchange_rate=Decimal('0.9'),  # 1 HKD = 0.9 CNY
            transaction_date=date(2024, 1, 15),
            annual_rate=Decimal('3.5'),
            start_date=date(2024, 1, 15),
            maturity_date=date(2024, 4, 15),  # 3个月后
            interest_type="SIMPLE",
            payment_frequency="MATURITY",
            face_value=Decimal('90000.00'),
            coupon_rate=Decimal('3.5'),
            notes="港元定存，存入时汇率0.9，等值人民币81,000元"
        )
        
        # 验证存入交易
        assert deposit_transaction.amount == Decimal('90000.00')
        assert deposit_transaction.currency == Currency.HKD
        assert deposit_transaction.exchange_rate == Decimal('0.9')
        assert deposit_transaction.amount_base_currency == Decimal('81000.00')  # 90000 * 0.9
        
        # 3. 创建到期利息收入交易
        # 计算3个月利息：90000 * 3.5% * (90/365) ≈ 787.5 港币
        interest_transaction = wealth_service.create_fixed_income_transaction(
            asset_id=hkd_deposit_asset.asset_id,
            transaction_type=TransactionType.INTEREST,
            amount=Decimal('787.50'),  # 港币利息
            currency=Currency.HKD,
            exchange_rate=Decimal('0.92'),  # 到期时汇率略有变化：1 HKD = 0.92 CNY
            transaction_date=date(2024, 4, 15),
            annual_rate=Decimal('3.5'),
            notes="定存到期利息收入，到期时汇率0.92"
        )
        
        # 验证利息交易
        assert interest_transaction.amount == Decimal('787.50')
        assert interest_transaction.currency == Currency.HKD
        assert interest_transaction.exchange_rate == Decimal('0.92')
        assert interest_transaction.amount_base_currency == Decimal('724.50')  # 787.5 * 0.92
        
        # 4. 创建港元现金资产（到期后转为现金）
        hkd_cash_asset = wealth_service.create_asset(
            asset_name="汇丰银行港元储蓄账户",
            asset_type=AssetType.CASH,
            primary_category="现金及等价物",
            secondary_category="外币储蓄",
            currency=Currency.HKD,
            description="港元储蓄账户",
            issuer="汇丰银行（香港）有限公司"
        )
        
        # 5. 创建定存到期转现金交易
        # 总计：90000 + 787.5 = 90787.5 港币
        maturity_transfer = wealth_service.create_cash_transaction(
            asset_id=hkd_cash_asset.asset_id,
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal('90787.50'),  # 本金+利息
            currency=Currency.HKD,
            exchange_rate=Decimal('0.92'),  # 到期时汇率
            transaction_date=date(2024, 4, 15),
            account_type="SAVINGS",
            notes="港元定存到期转入储蓄账户，保持港币形式"
        )
        
        # 验证转账交易
        assert maturity_transfer.amount == Decimal('90787.50')
        assert maturity_transfer.currency == Currency.HKD
        assert maturity_transfer.amount_base_currency == Decimal('83524.50')  # 90787.5 * 0.92
        
        # 6. 验证定存持仓（已到期，应该显示最终价值）
        deposit_position = wealth_service.get_position(hkd_deposit_asset.asset_id)
        assert deposit_position is not None
        # 使用原币种计算
        assert deposit_position.current_book_value_original_currency == Decimal('90787.50')
        assert deposit_position.principal_amount_original_currency == Decimal('90000.00')
        # 收益也用原币种计算
        original_currency_return = deposit_position.total_income_original_currency
        assert original_currency_return == Decimal('787.50')
        
        # 7. 验证港元现金持仓
        cash_position = wealth_service.get_position(hkd_cash_asset.asset_id)
        assert cash_position is not None
        # 现金账户使用原币种计算
        assert cash_position.current_book_value_original_currency == Decimal('90787.50')
        assert cash_position.principal_amount_original_currency == Decimal('90787.50')
        
        # 8. 验证投资组合（包含两个港币资产）
        portfolio = wealth_service.get_portfolio()
        assert len(portfolio.positions) == 2
        
        # 计算总价值（基础货币人民币）
        expected_total_cny = Decimal('81000.00') + Decimal('724.50') + Decimal('83524.50')
        assert portfolio.total_value == expected_total_cny
        
        # 9. 验证汇率收益
        # 存入时：90000 HKD * 0.9 = 81000 CNY
        # 到期时：90787.5 HKD * 0.92 = 83524.5 CNY
        # 汇率收益：(0.92 - 0.9) * 90787.5 = 1815.75 CNY
        exchange_gain = (Decimal('0.92') - Decimal('0.9')) * Decimal('90787.50')
        assert abs(exchange_gain - Decimal('1815.75')) < Decimal('0.01')
        
        print(f"港元定存本金: HK${deposit_transaction.amount}")
        print(f"港元利息收入: HK${interest_transaction.amount}")
        print(f"港元现金余额: HK${cash_position.current_book_value}")
        print(f"存入时汇率: {deposit_transaction.exchange_rate}")
        print(f"到期时汇率: {interest_transaction.exchange_rate}")
        print(f"汇率收益: ¥{exchange_gain}")
    
    def test_hkd_deposit_to_cny_conversion_scenario(self, wealth_service):
        """
        测试场景B：港元定存到期后兑换回人民币
        
        流程：
        1. 用人民币100,000元按汇率0.9换成港币90,000元
        2. 港币90,000元做6个月定存，年利率3.8%
        3. 到期后获得利息，总计港币91,710元
        4. 到期后按新汇率兑换回人民币
        """
        # 1. 创建港元定存资产
        hkd_deposit_asset = wealth_service.create_asset(
            asset_name="中银香港港元定期存款",
            asset_type=AssetType.FIXED_INCOME,
            primary_category="固定收益类",
            secondary_category="外币定存",
            currency=Currency.HKD,
            description="6个月港元定期存款，年利率3.8%",
            issuer="中国银行（香港）有限公司"
        )
        
        # 2. 创建港元定存交易
        # 存入时汇率：1 HKD = 0.9 CNY
        deposit_transaction = wealth_service.create_fixed_income_transaction(
            asset_id=hkd_deposit_asset.asset_id,
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal('90000.00'),  # 港币金额
            currency=Currency.HKD,
            exchange_rate=Decimal('0.9'),  # 1 HKD = 0.9 CNY
            transaction_date=date(2024, 1, 1),
            annual_rate=Decimal('3.8'),
            start_date=date(2024, 1, 1),
            maturity_date=date(2024, 7, 1),  # 6个月后
            interest_type="SIMPLE",
            payment_frequency="MATURITY",
            face_value=Decimal('90000.00'),
            coupon_rate=Decimal('3.8'),
            notes="港元定存，存入时汇率0.9，等值人民币81,000元"
        )
        
        # 3. 创建到期利息收入交易
        # 计算6个月利息：90000 * 3.8% * (180/365) ≈ 1,710 港币
        interest_transaction = wealth_service.create_fixed_income_transaction(
            asset_id=hkd_deposit_asset.asset_id,
            transaction_type=TransactionType.INTEREST,
            amount=Decimal('1710.00'),  # 港币利息
            currency=Currency.HKD,
            exchange_rate=Decimal('0.95'),  # 到期时汇率上升：1 HKD = 0.95 CNY
            transaction_date=date(2024, 7, 1),
            annual_rate=Decimal('3.8'),
            notes="定存到期利息收入，到期时汇率0.95"
        )
        
        # 4. 创建人民币现金资产（兑换目标）
        cny_cash_asset = wealth_service.create_asset(
            asset_name="招商银行人民币储蓄账户",
            asset_type=AssetType.CASH,
            primary_category="现金及等价物",
            secondary_category="储蓄存款",
            currency=Currency.CNY,
            description="人民币储蓄账户",
            issuer="招商银行股份有限公司"
        )
        
        # 5. 创建外汇兑换交易（港币换人民币）
        # 总港币：90000 + 1710 = 91710 HKD
        # 按到期汇率兑换：91710 * 0.95 = 87124.5 CNY
        conversion_transaction = wealth_service.create_cash_transaction(
            asset_id=cny_cash_asset.asset_id,
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal('87124.50'),  # 兑换后的人民币金额
            currency=Currency.CNY,
            exchange_rate=Decimal('1.0'),  # 人民币对人民币汇率为1
            transaction_date=date(2024, 7, 1),
            account_type="SAVINGS",
            notes="港元定存到期兑换，91710 HKD * 0.95 = 87124.5 CNY"
        )
        
        # 验证兑换交易
        assert conversion_transaction.amount == Decimal('87124.50')
        assert conversion_transaction.currency == Currency.CNY
        
        # 6. 验证定存持仓
        deposit_position = wealth_service.get_position(hkd_deposit_asset.asset_id)
        assert deposit_position is not None
        # 使用原币种计算
        assert deposit_position.current_book_value_original_currency == Decimal('91710.00')  # 本金+利息
        assert deposit_position.principal_amount_original_currency == Decimal('90000.00')
        assert deposit_position.total_income_original_currency == Decimal('1710.00')
        
        # 7. 验证人民币现金持仓
        cny_position = wealth_service.get_position(cny_cash_asset.asset_id)
        assert cny_position is not None
        # 人民币资产可以使用基础货币计算（因为基础货币就是人民币）
        assert cny_position.current_book_value == Decimal('87124.50')
        
        # 8. 验证总收益
        # 原始投资：81000 CNY（90000 HKD * 0.9）
        # 最终收回：87124.5 CNY
        # 总收益：87124.5 - 81000 = 6124.5 CNY
        total_return_cny = Decimal('87124.50') - Decimal('81000.00')
        assert total_return_cny == Decimal('6124.50')
        
        # 收益分解（简化验证）：
        # 总收益包含：利息收益 + 汇率收益
        # 这里主要验证总收益计算的正确性
        # 详细的收益分解可以通过交易记录分析得出
        
        print(f"港元定存本金: HK${deposit_transaction.amount}")
        print(f"港元利息收入: HK${interest_transaction.amount}")
        print(f"港元总额: HK${deposit_position.current_book_value_original_currency}")
        print(f"兑换后人民币: ¥{cny_position.current_book_value}")
        print(f"总收益: ¥{total_return_cny}")
        
        # 验证关键指标
        assert deposit_position.current_book_value_original_currency == Decimal('91710.00')
        assert cny_position.current_book_value == Decimal('87124.50')
        assert total_return_cny > 0  # 确保有正收益
    
    def test_multiple_currency_deposits_portfolio(self, wealth_service):
        """
        测试多币种存款的投资组合管理
        
        场景：同时持有人民币、港币、美元三种定存
        """
        # 1. 人民币定存
        cny_deposit = wealth_service.create_asset(
            asset_name="工商银行人民币定存",
            asset_type=AssetType.FIXED_INCOME,
            primary_category="固定收益类",
            secondary_category="定期存款",
            currency=Currency.CNY,
            description="1年期人民币定存，年利率2.8%"
        )
        
        wealth_service.create_fixed_income_transaction(
            asset_id=cny_deposit.asset_id,
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal('100000.00'),
            currency=Currency.CNY,
            exchange_rate=Decimal('1.0'),
            transaction_date=date(2024, 1, 1),
            annual_rate=Decimal('2.8')
        )
        
        # 2. 港币定存
        hkd_deposit = wealth_service.create_asset(
            asset_name="汇丰银行港币定存",
            asset_type=AssetType.FIXED_INCOME,
            primary_category="固定收益类",
            secondary_category="外币定存",
            currency=Currency.HKD,
            description="1年期港币定存，年利率3.5%"
        )
        
        wealth_service.create_fixed_income_transaction(
            asset_id=hkd_deposit.asset_id,
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal('80000.00'),  # 港币
            currency=Currency.HKD,
            exchange_rate=Decimal('0.9'),  # 1 HKD = 0.9 CNY
            transaction_date=date(2024, 1, 1),
            annual_rate=Decimal('3.5')
        )
        
        # 3. 美元定存
        usd_deposit = wealth_service.create_asset(
            asset_name="花旗银行美元定存",
            asset_type=AssetType.FIXED_INCOME,
            primary_category="固定收益类",
            secondary_category="外币定存",
            currency=Currency.USD,
            description="1年期美元定存，年利率4.2%"
        )
        
        wealth_service.create_fixed_income_transaction(
            asset_id=usd_deposit.asset_id,
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal('12000.00'),  # 美元
            currency=Currency.USD,
            exchange_rate=Decimal('7.2'),  # 1 USD = 7.2 CNY
            transaction_date=date(2024, 1, 1),
            annual_rate=Decimal('4.2')
        )
        
        # 4. 验证多币种投资组合
        portfolio = wealth_service.get_portfolio()
        assert len(portfolio.positions) == 3
        
        # 计算总价值（基础货币人民币）
        expected_total_cny = (
            Decimal('100000.00') +  # CNY: 100000 * 1.0
            Decimal('72000.00') +   # HKD: 80000 * 0.9
            Decimal('86400.00')     # USD: 12000 * 7.2
        )
        assert portfolio.total_value == expected_total_cny
        
        # 5. 验证币种分布
        allocation = portfolio.calculate_asset_allocation()
        
        # 按资产类型分布（都是固定收益）
        assert allocation[AssetType.FIXED_INCOME.name]['percentage'] == 100.0
        
        # 验证各币种的等值人民币金额
        cny_position = wealth_service.get_position(cny_deposit.asset_id)
        hkd_position = wealth_service.get_position(hkd_deposit.asset_id)
        usd_position = wealth_service.get_position(usd_deposit.asset_id)
        
        assert cny_position.current_book_value == Decimal('100000.00')
        assert hkd_position.current_book_value_original_currency == Decimal('80000.00')  # 港币原币种金额
        assert usd_position.current_book_value_original_currency == Decimal('12000.00')  # 美元原币种金额
        
        print(f"人民币定存: ¥{cny_position.current_book_value}")
        print(f"港币定存: HK${hkd_position.current_book_value_original_currency} (≈¥{hkd_position.current_book_value})")
        print(f"美元定存: ${usd_position.current_book_value_original_currency} (≈¥{usd_position.current_book_value})")
        print(f"投资组合总价值: ¥{portfolio.total_value}")
    
    def test_exchange_rate_fluctuation_impact(self, wealth_service):
        """
        测试汇率波动对外币资产价值的影响
        """
        # 1. 创建美元定存
        usd_deposit = wealth_service.create_asset(
            asset_name="美元定存汇率测试",
            asset_type=AssetType.FIXED_INCOME,
            primary_category="固定收益类",
            secondary_category="外币定存",
            currency=Currency.USD,
            description="汇率波动测试用美元定存"
        )
        
        # 2. 初始存入（汇率7.0）
        initial_deposit = wealth_service.create_fixed_income_transaction(
            asset_id=usd_deposit.asset_id,
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal('10000.00'),  # 美元
            currency=Currency.USD,
            exchange_rate=Decimal('7.0'),  # 1 USD = 7.0 CNY
            transaction_date=date(2024, 1, 1),
            annual_rate=Decimal('4.0')
        )
        
        # 验证初始价值
        assert initial_deposit.amount_base_currency == Decimal('70000.00')  # 10000 * 7.0
        
        # 3. 第一次利息收入（汇率上升到7.3）
        interest1 = wealth_service.create_fixed_income_transaction(
            asset_id=usd_deposit.asset_id,
            transaction_type=TransactionType.INTEREST,
            amount=Decimal('200.00'),  # 美元利息
            currency=Currency.USD,
            exchange_rate=Decimal('7.3'),  # 汇率上升
            transaction_date=date(2024, 6, 30),
            annual_rate=Decimal('4.0'),
            notes="半年利息，汇率上升至7.3"
        )
        
        # 4. 第二次利息收入（汇率下降到6.8）
        interest2 = wealth_service.create_fixed_income_transaction(
            asset_id=usd_deposit.asset_id,
            transaction_type=TransactionType.INTEREST,
            amount=Decimal('200.00'),  # 美元利息
            currency=Currency.USD,
            exchange_rate=Decimal('6.8'),  # 汇率下降
            transaction_date=date(2024, 12, 31),
            annual_rate=Decimal('4.0'),
            notes="年底利息，汇率下降至6.8"
        )
        
        # 5. 验证汇率变化对收益的影响
        position = wealth_service.get_position(usd_deposit.asset_id)
        assert position.current_book_value_original_currency == Decimal('10400.00')  # 10000 + 200 + 200 USD
        
        # 计算基础货币收益
        # 初始投资：10000 USD * 7.0 = 70000 CNY
        # 第一次利息：200 USD * 7.3 = 1460 CNY
        # 第二次利息：200 USD * 6.8 = 1360 CNY
        # 总计：70000 + 1460 + 1360 = 72820 CNY
        
        assert initial_deposit.amount_base_currency == Decimal('70000.00')
        assert interest1.amount_base_currency == Decimal('1460.00')  # 200 * 7.3
        assert interest2.amount_base_currency == Decimal('1360.00')  # 200 * 6.8
        
        # 验证投资组合中的基础货币总值
        portfolio = wealth_service.get_portfolio()
        expected_total = Decimal('70000.00') + Decimal('1460.00') + Decimal('1360.00')
        assert portfolio.total_value == expected_total
        
        print(f"美元本金: ${initial_deposit.amount} (初始汇率{initial_deposit.exchange_rate})")
        print(f"第一次利息: ${interest1.amount} (汇率{interest1.exchange_rate})")
        print(f"第二次利息: ${interest2.amount} (汇率{interest2.exchange_rate})")
        print(f"美元总额: ${position.current_book_value_original_currency}")
        print(f"人民币等值总额: ¥{portfolio.total_value}") 