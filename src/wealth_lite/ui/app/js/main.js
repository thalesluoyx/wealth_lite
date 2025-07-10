/**
 * WealthLite 主JavaScript文件
 * 处理页面导航、币种切换和基础交互功能
 */

class WealthLiteApp {
    constructor() {
        this.currentCurrency = 'CNY';
        this.currentPage = 'dashboard';
        this.exchangeRates = {
            'CNY': 1,
            'USD': 0.14,
            'HKD': 1.1,
            'EUR': 0.13
        };
        
        this.init();
    }

    init() {
        this.initializeIcons();
        this.bindEvents();
        this.loadDashboardData();
        
        // 初始化所有页面管理器
        this.initializePageManagers();
        
        // 显示初始动画
        setTimeout(() => {
            document.body.classList.add('loaded');
        }, 100);
    }

    initializePageManagers() {
        // 初始化图表管理器（避免重复创建）
        if (typeof ChartManager !== 'undefined' && !this.chartManager) {
            this.chartManager = new ChartManager();
        }
        
        // 初始化交易管理器
        if (typeof TransactionManager !== 'undefined') {
            this.transactionManager = new TransactionManager(this);
            // 设置全局实例供模态窗口调用
            window.transactionManager = this.transactionManager;
        }
        
        // 初始化资产管理器
        if (typeof AssetManager !== 'undefined') {
            this.assetManager = new AssetManager(this);
            // 设置全局实例供模态窗口调用
            window.assetManager = this.assetManager;
        }
    }

    initializeIcons() {
        // 初始化 Lucide 图标
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    bindEvents() {
        // 导航事件
        this.bindNavigationEvents();
        
        // 币种切换事件
        this.bindCurrencyToggleEvents();
        
        // 时间范围切换事件
        this.bindTimeRangeEvents();
        
        // 搜索事件
        this.bindSearchEvents();
        
        // 键盘快捷键
        this.bindKeyboardShortcuts();
    }

    bindNavigationEvents() {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const targetPage = item.getAttribute('href').substring(1);
                this.navigateToPage(targetPage);
            });
        });
    }

    bindCurrencyToggleEvents() {
        const currencyToggle = document.getElementById('currencyToggle');
        if (currencyToggle) {
            currencyToggle.addEventListener('click', () => {
                this.toggleCurrency();
            });
        }
    }

    bindTimeRangeEvents() {
        const timeButtons = document.querySelectorAll('.time-btn');
        timeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                // 移除所有活动状态
                timeButtons.forEach(b => b.classList.remove('active'));
                // 添加当前活动状态
                btn.classList.add('active');
                
                const range = btn.dataset.range;
                this.updateChartTimeRange(range);
            });
        });
    }

    bindSearchEvents() {
        const searchBtn = document.querySelector('.btn-icon[title="搜索"]');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                this.openSearchModal();
            });
        }
    }

    bindKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K 打开搜索
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.openSearchModal();
            }
            
            // 数字键快速导航
            if (e.altKey) {
                switch(e.key) {
                    case '1':
                        this.navigateToPage('dashboard');
                        break;
                    case '2':
                        this.navigateToPage('assets');
                        break;
                    case '3':
                        this.navigateToPage('transactions');
                        break;
                    case '4':
                        this.navigateToPage('portfolio');
                        break;
                }
            }
        });
    }



    navigateToPage(pageId) {
        // 隐藏所有页面
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        
        // 显示目标页面
        const targetPage = document.getElementById(pageId);
        if (targetPage) {
            targetPage.classList.add('active');
            targetPage.classList.add('fade-in');
        }
        
        // 更新导航状态
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeNavItem = document.querySelector(`[href="#${pageId}"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }
        
        this.currentPage = pageId;
        
        // 页面特定的初始化
        this.initializePage(pageId);
    }

    initializePage(pageId) {
        switch(pageId) {
            case 'dashboard':
                this.loadDashboardData();
                break;
            case 'assets':
                this.loadAssetsData();
                break;
            case 'transactions':
                this.loadTransactionsData();
                break;
            case 'portfolio':
                this.loadPortfolioData();
                break;
        }
    }

    toggleCurrency() {
        const currencies = ['CNY', 'USD', 'HKD', 'EUR'];
        const currentIndex = currencies.indexOf(this.currentCurrency);
        const nextIndex = (currentIndex + 1) % currencies.length;
        
        this.currentCurrency = currencies[nextIndex];
        
        // 更新按钮文本
        const currencyToggle = document.getElementById('currencyToggle');
        if (currencyToggle) {
            currencyToggle.textContent = this.currentCurrency;
        }
        
        // 更新所有金额显示
        this.updateAllAmounts();
        
        // 显示切换动画
        this.showCurrencyChangeNotification();
    }

    updateAllAmounts() {
        const amountElements = document.querySelectorAll('[data-amount]');
        amountElements.forEach(element => {
            const originalAmount = parseFloat(element.dataset.amount);
            const convertedAmount = this.convertCurrency(originalAmount);
            element.textContent = this.formatAmount(convertedAmount);
        });
        
        // 更新币种符号
        const currencyElements = document.querySelectorAll('.currency');
        currencyElements.forEach(element => {
            element.textContent = this.getCurrencySymbol(this.currentCurrency);
        });
    }

    convertCurrency(amount, fromCurrency = 'CNY') {
        const fromRate = this.exchangeRates[fromCurrency] || 1;
        const toRate = this.exchangeRates[this.currentCurrency] || 1;
        return (amount / fromRate) * toRate;
    }

    formatAmount(amount) {
        return new Intl.NumberFormat('zh-CN', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        }).format(amount);
    }

    formatPercentage(value) {
        return new Intl.NumberFormat('zh-CN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value * 100) + '%';
    }

    getCurrencySymbol(currency) {
        const symbols = {
            'CNY': '元',
            'USD': '$',
            'HKD': 'HK$',
            'EUR': '€'
        };
        return symbols[currency] || currency;
    }

    showCurrencyChangeNotification() {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = 'currency-notification';
        notification.textContent = `已切换到 ${this.currentCurrency}`;
        
        // 添加样式
        Object.assign(notification.style, {
            position: 'fixed',
            top: '80px',
            right: '20px',
            background: 'rgba(255, 255, 255, 0.95)',
            color: 'var(--text-primary)',
            padding: '12px 20px',
            borderRadius: '8px',
            boxShadow: 'var(--shadow-lg)',
            zIndex: '1000',
            fontSize: '14px',
            fontWeight: '500',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });
        
        document.body.appendChild(notification);
        
        // 显示动画
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // 隐藏动画
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 2000);
    }

    updateChartTimeRange(range) {
        console.log(`更新图表时间范围: ${range}`);
        // 使用本实例的图表管理器，而不是全局实例
        if (this.chartManager) {
            this.chartManager.updateTimeRange(range);
        }
    }

    openSearchModal() {
        console.log('打开搜索模态框');
        // TODO: 实现搜索功能
    }

    async loadDashboardData() {
        try {
            // 直接从前端数据计算仪表板统计信息
            const data = await this.calculateDashboardData();
            console.log('✅ 仪表板数据计算成功:', data);
            this.updateDashboardUI(data);
        } catch (error) {
            console.error('❌ 计算仪表板数据失败:', error);
            this.showErrorMessage('数据加载失败，请稍后重试');
        }
    }

    async fetchDashboardData() {
        try {
            // 直接从前端数据计算仪表板统计信息
            const data = await this.calculateDashboardData();
            console.log('✅ 仪表板数据计算成功:', data);
            return data;
            
        } catch (error) {
            console.error('❌ 计算仪表板数据失败:', error);
            // 如果计算失败，返回默认数据避免页面崩溃
            return {
                totalAssets: 0,
                totalChange: 0,
                totalChangePercent: 0,
                cashAssets: 0,
                fixedIncomeAssets: 0,
                assets: []
            };
        }
    }

    async calculateDashboardData() {
        // 获取资产和交易数据
        const assets = await this.loadAssetsData();
        const transactions = await this.loadTransactionsData();
        
        // 计算持仓数据
        const positions = this.calculatePositions(assets, transactions);
        
        // 按资产类型分组
        const assetTypeGroups = {
            'CASH': { name: '现金及等价物', total: 0, positions: [] },
            'FIXED_INCOME': { name: '固定收益', total: 0, positions: [] },
            'EQUITY': { name: '权益类', total: 0, positions: [] },
            'REAL_ESTATE': { name: '不动产', total: 0, positions: [] },
            'COMMODITY': { name: '大宗商品', total: 0, positions: [] }
        };

        // 计算总资产和分类统计
        let totalAssets = 0;
        let totalReturn = 0;
        
        positions.forEach(position => {
            const amount = Math.round(position.amount || 0);
            const positionReturn = Math.round(position.total_return || 0);
            
            totalAssets += amount;
            totalReturn += positionReturn;
            
            // 按资产类型分组
            const assetType = position.type || 'CASH';
            if (assetTypeGroups[assetType]) {
                assetTypeGroups[assetType].total += amount;
                assetTypeGroups[assetType].positions.push(position);
            }
        });

        // 计算收益率
        const totalReturnRate = totalAssets > 0 ? (totalReturn / (totalAssets - totalReturn)) * 100 : 0;

        // 计算上月数据进行对比
        const lastMonthData = this.calculateLastMonthData(transactions);
        const totalChange = totalReturn - lastMonthData.totalReturn;
        const totalChangePercent = lastMonthData.totalAssets > 0 
            ? ((totalAssets - lastMonthData.totalAssets) / lastMonthData.totalAssets * 100).toFixed(1)
            : 0;

        console.log('📊 资产总览数据计算:', {
            positions: positions.length,
            totalAssets,
            totalReturn,
            assetTypeGroups: {
                CASH: assetTypeGroups['CASH'].total,
                FIXED_INCOME: assetTypeGroups['FIXED_INCOME'].total,
                EQUITY: assetTypeGroups['EQUITY'].total,
                REAL_ESTATE: assetTypeGroups['REAL_ESTATE'].total,
                COMMODITY: assetTypeGroups['COMMODITY'].total
            }
        });

        return {
            totalAssets: Math.round(totalAssets),
            totalChange: Math.round(totalChange),
            totalChangePercent: parseFloat(totalChangePercent),
            totalReturn: Math.round(totalReturn),
            totalReturnRate: parseFloat(totalReturnRate.toFixed(2)),
            cashAssets: Math.round(assetTypeGroups['CASH'].total),
            fixedIncomeAssets: Math.round(assetTypeGroups['FIXED_INCOME'].total),
            equityAssets: Math.round(assetTypeGroups['EQUITY'].total),
            realEstateAssets: Math.round(assetTypeGroups['REAL_ESTATE'].total),
            commodityAssets: Math.round(assetTypeGroups['COMMODITY'].total),
            assetTypeGroups: assetTypeGroups,
            assets: positions
        };
    }

    calculatePositions(assets, transactions) {
        // 按资产分组交易
        const assetTransactions = {};
        
        transactions.forEach(transaction => {
            const assetId = transaction.asset_id;
            if (!assetTransactions[assetId]) {
                assetTransactions[assetId] = [];
            }
            assetTransactions[assetId].push(transaction);
        });

        console.log('📊 资产交易分组:', {
            assetsCount: assets.length,
            transactionsCount: transactions.length,
            assetTransactionGroups: Object.keys(assetTransactions).length,
            assetTransactions: Object.keys(assetTransactions).map(assetId => ({
                assetId,
                transactionCount: assetTransactions[assetId].length
            }))
        });

        // 计算每个资产的持仓
        const positions = [];
        
        Object.keys(assetTransactions).forEach(assetId => {
            const asset = assets.find(a => a.id === assetId);
            if (!asset) {
                console.warn(`⚠️ 未找到资产 ${assetId}`);
                return;
            }

            const assetTxns = assetTransactions[assetId];
            const position = this.calculateAssetPosition(asset, assetTxns);
            
            console.log(`📊 资产 ${asset.name} 持仓计算结果:`, {
                amount: position.amount,
                totalReturn: position.total_return,
                totalInvested: position.total_invested,
                totalWithdrawn: position.total_withdrawn,
                totalIncome: position.total_income
            });
            
            if (position.amount > 0) { // 只显示有持仓的资产
                positions.push(position);
            }
        });

        console.log('📊 最终持仓结果:', {
            positionsCount: positions.length,
            totalValue: positions.reduce((sum, p) => sum + p.amount, 0)
        });

        return positions;
    }

    calculateAssetPosition(asset, transactions) {
        let totalInvested = 0;
        let totalWithdrawn = 0;
        let totalIncome = 0;
        let totalFees = 0;
        let firstTransactionDate = null;
        let lastTransactionDate = null;

        transactions.forEach(transaction => {
            const amount = parseFloat(transaction.amount) || 0;
            const exchangeRate = transaction.exchangeRate || 1;
            const baseAmount = amount * exchangeRate;
            const transactionDate = new Date(transaction.date);

            // 更新日期范围
            if (!firstTransactionDate || transactionDate < firstTransactionDate) {
                firstTransactionDate = transactionDate;
            }
            if (!lastTransactionDate || transactionDate > lastTransactionDate) {
                lastTransactionDate = transactionDate;
            }

            // 按交易类型分类
            switch (transaction.type) {
                case 'DEPOSIT':
                case 'BUY':
                    totalInvested += baseAmount;
                    break;
                case 'WITHDRAW':
                case 'SELL':
                    totalWithdrawn += baseAmount;
                    break;
                case 'INTEREST':
                case 'DIVIDEND':
                    totalIncome += baseAmount;
                    break;
                case 'FEE':
                    totalFees += baseAmount;
                    break;
            }
        });

        // 计算持仓指标
        const netInvested = totalInvested - totalWithdrawn;
        const currentValue = netInvested + totalIncome - totalFees;
        const totalReturn = totalIncome - totalFees;
        const totalReturnRate = netInvested > 0 ? (totalReturn / netInvested) * 100 : 0;

        // 计算持有天数
        const holdingDays = firstTransactionDate 
            ? Math.floor((new Date() - firstTransactionDate) / (1000 * 60 * 60 * 24))
            : 0;

        return {
            id: asset.id,
            name: asset.name,
            type: asset.asset_type || asset.type, // 兼容两种字段名
            asset_subtype: asset.asset_subtype,
            currency: asset.currency,
            amount: currentValue,
            total_return: totalReturn,
            total_return_rate: totalReturnRate / 100, // 转换为小数
            principal_amount: netInvested,
            total_invested: totalInvested,
            total_withdrawn: totalWithdrawn,
            total_income: totalIncome,
            total_fees: totalFees,
            net_invested: netInvested,
            current_value: currentValue,
            current_book_value: currentValue,
            transaction_count: transactions.length,
            first_transaction_date: firstTransactionDate ? firstTransactionDate.toISOString().split('T')[0] : null,
            last_transaction_date: lastTransactionDate ? lastTransactionDate.toISOString().split('T')[0] : null,
            firstTransactionDate: firstTransactionDate ? firstTransactionDate.toISOString().split('T')[0] : null,
            holding_days: holdingDays,
            status: currentValue > 0 ? 'ACTIVE' : 'CLOSED',
            unrealized_pnl: 0, // 暂时设为0，后续可以根据市值计算
            realized_pnl: totalReturn,
            annualized_return: holdingDays > 0 ? (totalReturnRate * 365 / holdingDays) / 100 : 0
        };
    }

    calculateLastMonthData(transactions) {
        const currentDate = new Date();
        const lastMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, currentDate.getDate());
        
        // 筛选上月之前的交易
        const pastTransactions = transactions.filter(t => new Date(t.date) <= lastMonth);
        
        // 简化计算：假设上月的总资产和收益
        let totalAssets = 0;
        let totalReturn = 0;
        
        pastTransactions.forEach(transaction => {
            const amount = parseFloat(transaction.amount) || 0;
            const exchangeRate = transaction.exchangeRate || 1;
            const baseAmount = amount * exchangeRate;
            
            switch (transaction.type) {
                case 'DEPOSIT':
                case 'BUY':
                    totalAssets += baseAmount;
                    break;
                case 'WITHDRAW':
                case 'SELL':
                    totalAssets -= baseAmount;
                    break;
                case 'INTEREST':
                case 'DIVIDEND':
                    totalReturn += baseAmount;
                    totalAssets += baseAmount;
                    break;
                case 'FEE':
                    totalAssets -= baseAmount;
                    break;
            }
        });

        return {
            totalAssets: Math.round(totalAssets),
            totalReturn: Math.round(totalReturn)
        };
    }

    updateDashboardUI(data) {
        this.dashboardData = data; // 存储仪表板数据
        
        // 更新总资产（显示在资产类型分布图表中心）
        const assetTypeAmountElement = document.getElementById('assetTypeAmount');
        if (assetTypeAmountElement) {
            assetTypeAmountElement.textContent = this.formatAmount(data.totalAssets);
            assetTypeAmountElement.dataset.amount = data.totalAssets;
        }
        
        // 更新现金资产
        const cashAmountElement = document.getElementById('cashAmount');
        if (cashAmountElement) {
            cashAmountElement.textContent = this.formatAmount(data.cashAssets);
            cashAmountElement.dataset.amount = data.cashAssets;
        }
        
        // 更新固定收益资产
        const fixedAmountElement = document.getElementById('fixedAmount');
        if (fixedAmountElement) {
            fixedAmountElement.textContent = this.formatAmount(data.fixedIncomeAssets);
            fixedAmountElement.dataset.amount = data.fixedIncomeAssets;
        }
        
        // 更新持仓列表
        this.updatePositionsList(data.assets);
        
        // 更新图表
        this.updateCharts(data.assets);
        
        // 输出调试信息
        console.log('✅ 仪表板UI更新完成:', {
            totalAssets: data.totalAssets,
            cashAssets: data.cashAssets,
            fixedIncomeAssets: data.fixedIncomeAssets,
            positionsCount: data.assets?.length || 0
        });
    }

    updatePositionsList(positions) {
        const positionsTableBody = document.getElementById('positionsTableBody');
        const positionsEmpty = document.getElementById('positionsEmpty');
        const positionCount = document.getElementById('positionCount');
        
        if (!positionsTableBody) return;
        
        if (!positions || positions.length === 0) {
            positionsTableBody.innerHTML = '';
            if (positionsEmpty) positionsEmpty.style.display = 'block';
            if (positionCount) positionCount.textContent = '共 0 笔持仓';
            return;
        }
        
        if (positionsEmpty) positionsEmpty.style.display = 'none';
        if (positionCount) positionCount.textContent = `共 ${positions.length} 笔持仓`;
        
        // 清空表格
        positionsTableBody.innerHTML = '';
        
        positions.forEach(position => {
            // 计算收益相关数据
            const totalReturn = (Math.round(position.total_return)) || 0;
            const totalReturnRate = position.total_return_rate || 0;
            const returnClass = totalReturn >= 0 ? 'positive' : 'negative';
            const status = position.status || 'ACTIVE';
            const statusClass = status.toLowerCase();
            
            // 创建主行
            const mainRow = document.createElement('tr');
            mainRow.className = 'position-row';
            mainRow.dataset.positionId = position.id;
            
            mainRow.innerHTML = `
                <td>
                    <div class="asset-info">
                        <span class="expand-icon">▶</span>
                        <div class="asset-icon ${position.type}">
                            <i data-lucide="${this.getAssetIcon(position.type)}"></i>
                        </div>
                        <span class="asset-name">${position.name}</span>
                    </div>
                </td>
                <td>
                    <span class="asset-type ${position.type}">${this.getAssetTypeText(position.type)}</span>
                </td>
                <td>
                    <span class="amount" data-amount="${Math.round(position.amount)}">${this.formatAmount(Math.round(position.amount))}</span>
                </td>
                <td class="${returnClass}">
                    ${this.formatAmount(totalReturn)}
                </td>
                <td class="${returnClass}">
                    ${this.formatPercentage(totalReturnRate)}
                </td>
                <td>
                    <span class="status ${statusClass}">${this.getStatusText(status)}</span>
                </td>
                <td>${this.calculateHoldingDays(position.firstTransactionDate)} 天</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-action withdraw" data-action="withdraw" data-asset-id="${position.id}">
                            <i data-lucide="minus-circle"></i>
                            提取
                        </button>
                    </div>
                </td>
            `;
            
            // 创建详细信息行
            const detailsRow = document.createElement('tr');
            detailsRow.className = 'details-row';
            detailsRow.innerHTML = `
                <td colspan="8" class="details-container">
                    <div class="details-panel">
                        <div class="details-tabs">
                            <button class="tab-button active" data-tab="overview">概览</button>
                            <button class="tab-button" data-tab="transactions">交易记录</button>
                            <button class="tab-button" data-tab="performance">收益分析</button>
                        </div>
                        
                        <div class="tab-content active" data-tab-content="overview">
                            <div class="details-grid">
                                <div class="detail-item">
                                    <span class="detail-label">资产子类型</span>
                                    <span class="detail-value">${position.asset_subtype || '未知'}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">币种</span>
                                    <span class="detail-value">${position.currency || 'CNY'}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">交易笔数</span>
                                    <span class="detail-value">${position.transaction_count || 0} 笔</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">首次交易日期</span>
                                    <span class="detail-value">${position.first_transaction_date || '未知'}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">最后交易日期</span>
                                    <span class="detail-value">${position.last_transaction_date || '未知'}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">本金金额</span>
                                    <span class="detail-value">${this.formatAmount(position.principal_amount || 0)}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="tab-content" data-tab-content="transactions">
                            <div class="details-grid">
                                <div class="detail-item">
                                    <span class="detail-label">总投入金额</span>
                                    <span class="detail-value">${this.formatAmount(position.total_invested || 0)}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">总取出金额</span>
                                    <span class="detail-value">${this.formatAmount(position.total_withdrawn || 0)}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">总收入金额</span>
                                    <span class="detail-value">${this.formatAmount(position.total_income || 0)}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">总费用</span>
                                    <span class="detail-value">${this.formatAmount(position.total_fees || 0)}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">净投入金额</span>
                                    <span class="detail-value">${this.formatAmount(position.net_invested || 0)}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">账面价值</span>
                                    <span class="detail-value">${this.formatAmount(position.current_book_value || 0)}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="tab-content" data-tab-content="performance">
                            <div class="details-grid">
                                <div class="detail-item">
                                    <span class="detail-label">总收益</span>
                                    <span class="detail-value ${returnClass}">${this.formatAmount(totalReturn)}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">总收益率</span>
                                    <span class="detail-value ${returnClass}">${this.formatPercentage(totalReturnRate)}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">未实现损益</span>
                                    <span class="detail-value ${(position.unrealized_pnl || 0) >= 0 ? 'positive' : 'negative'}">${this.formatAmount(position.unrealized_pnl || 0)}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">已实现损益</span>
                                    <span class="detail-value ${(position.realized_pnl || 0) >= 0 ? 'positive' : 'negative'}">${this.formatAmount(position.realized_pnl || 0)}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">年化收益率</span>
                                    <span class="detail-value ${returnClass}">${this.formatPercentage(position.annualized_return || 0)}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">持有天数</span>
                                    <span class="detail-value">${this.calculateHoldingDays(position.firstTransactionDate)} 天</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">当前市值</span>
                                    <span class="detail-value">${this.formatAmount(position.current_value || position.amount)}</span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">持仓状态</span>
                                    <span class="detail-value">
                                        <span class="status ${statusClass}">${this.getStatusText(status)}</span>
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </td>
            `;
            
            positionsTableBody.appendChild(mainRow);
            positionsTableBody.appendChild(detailsRow);
            
            // 添加主行点击事件
            mainRow.addEventListener('click', (e) => {
                // 阻止按钮点击事件冒泡
                if (e.target.closest('.btn-action')) return;
                
                const isExpanded = mainRow.classList.contains('expanded');
                
                // 收起所有其他行
                document.querySelectorAll('.position-row').forEach(row => {
                    row.classList.remove('expanded');
                });
                document.querySelectorAll('.details-row').forEach(row => {
                    row.classList.remove('show');
                });
                
                // 切换当前行
                if (!isExpanded) {
                    mainRow.classList.add('expanded');
                    detailsRow.classList.add('show');
                }
            });
            
            // 添加标签切换事件
            detailsRow.querySelectorAll('.tab-button').forEach(button => {
                button.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const tabName = button.dataset.tab;
                    
                    // 切换标签按钮状态
                    detailsRow.querySelectorAll('.tab-button').forEach(btn => {
                        btn.classList.remove('active');
                    });
                    button.classList.add('active');
                    
                    // 切换标签内容
                    detailsRow.querySelectorAll('.tab-content').forEach(content => {
                        content.classList.remove('active');
                    });
                    detailsRow.querySelector(`[data-tab-content="${tabName}"]`).classList.add('active');
                });
            });
        });
        
        // 汇总行
        const totalAmount = positions.reduce((sum, p) => sum + (p.amount || 0), 0);
        const totalReturn = positions.reduce((sum, p) => sum + (p.total_return || 0), 0);
        const summaryRow = document.createElement('tr');
        summaryRow.className = 'summary-row';
        summaryRow.innerHTML = `
            <td colspan="2" style="font-weight:bold;">汇总</td>
            <td style="font-weight:bold; text-align:right;">${this.formatAmount(Math.round(totalAmount))}</td>
            <td style="font-weight:bold; text-align:right;">${this.formatAmount(Math.round(totalReturn))}</td>
            <td colspan="4"></td>
        `;
        positionsTableBody.appendChild(summaryRow);
        
        // 绑定提取按钮事件
        this.bindPositionActions();
        
        // 重新初始化图标
        this.initializeIcons();
    }
    
    getAssetTypeText(type) {
        const typeMap = {
            // 小写格式（仪表板API）
            'cash': '现金及等价物',
            'fixed_income': '固定收益',
            'equity': '权益类',
            // 大写格式（资产API）
            'CASH': '现金及等价物',
            'FIXED_INCOME': '固定收益',
            'EQUITY': '权益类'
        };
        return typeMap[type] || type;
    }
    
    getStatusText(status) {
        const statusMap = {
            'ACTIVE': '持有中',
            'INACTIVE': '非活跃',
            'CLOSED': '已平仓',
            'MATURED': '已到期',
            'SUSPENDED': '暂停',
            'PARTIALLY_WITHDRAWN': '部分提取',
            'WITHDRAWN': '已提取'
        };
        return statusMap[status] || status;
    }
    
    calculateHoldingDays(firstTransactionDate) {
        if (!firstTransactionDate) return 0;
        const firstDate = new Date(firstTransactionDate);
        const today = new Date();
        const diffTime = Math.abs(today - firstDate);
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    }
    
    bindPositionActions() {
        // 绑定提取按钮事件
        document.querySelectorAll('[data-action="withdraw"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const assetId = e.target.closest('[data-asset-id]').dataset.assetId;
                
                // 从仪表板数据中查找对应的持仓信息（修复：从assets而不是positions中查找）
                const position = this.dashboardData?.assets?.find(p => p.id === assetId);
                if (position) {
                    console.log('✅ 找到持仓数据:', position);
                    this.handlePositionWithdraw(assetId, position);
                } else {
                    console.warn('⚠️ 未找到持仓信息:', assetId);
                    this.handlePositionWithdraw(assetId);
                }
            });
        });
    }
    
    handlePositionWithdraw(assetId, positionData = null) {
        // 切换到交易记录页面
        this.navigateToPage('transactions');
        
        // 等待页面加载完成后打开提取交易模态窗口
        setTimeout(async () => {
            if (this.transactionManager) {
                await this.transactionManager.openWithdrawTransactionModal(assetId, positionData);
            }
        }, 300);
    }

    getAssetIcon(type) {
        const icons = {
            'cash': 'banknote',
            'deposit': 'piggy-bank',
            'investment': 'trending-up',
            'stock': 'line-chart',
            'bond': 'file-text',
            'fund': 'pie-chart'
        };
        return icons[type] || 'wallet';
    }

    async loadAssetsData() {
        console.log('加载资产数据');
        
        try {
            // 调用后端API获取资产数据
            const response = await fetch('/api/assets');
            if (response.ok) {
                const data = await response.json();
                console.log('✅ 资产数据加载成功:', data);
                // 从API响应中提取资产数组
                const assets = data.assets || data || [];
                console.log('📊 提取的资产数组:', assets);
                return assets;
            } else {
                console.warn('⚠️ 资产API调用失败，使用模拟数据');
                // 返回一些模拟数据用于测试
                return [
                    {
                        id: 'asset1',
                        name: '招商银行活期存款',
                        asset_type: 'CASH',
                        asset_subtype: '活期存款',
                        currency: 'CNY'
                    },
                    {
                        id: 'asset2',
                        name: '中国银行定期存款',
                        asset_type: 'FIXED_INCOME',
                        asset_subtype: '定期存款',
                        currency: 'CNY'
                    }
                ];
            }
        } catch (error) {
            console.error('❌ 获取资产数据失败，使用模拟数据:', error);
            // 返回一些模拟数据用于测试
            return [
                {
                    id: 'asset1',
                    name: '招商银行活期存款',
                    asset_type: 'CASH',
                    asset_subtype: '活期存款',
                    currency: 'CNY'
                },
                {
                    id: 'asset2',
                    name: '中国银行定期存款',
                    asset_type: 'FIXED_INCOME',
                    asset_subtype: '定期存款',
                    currency: 'CNY'
                }
            ];
        }
    }

    async loadTransactionsData() {
        console.log('加载交易数据');
        
        try {
            // 调用后端API获取交易数据
            const response = await fetch('/api/transactions');
            if (response.ok) {
                const data = await response.json();
                console.log('✅ 交易数据加载成功:', data);
                // 从API响应中提取交易数组
                const transactions = data.transactions || data || [];
                console.log('📊 提取的交易数组:', transactions);
                return transactions;
            } else {
                console.warn('⚠️ 交易API调用失败，使用模拟数据');
                // 返回一些模拟数据用于测试
                return [
                    {
                        id: 'tx1',
                        asset_id: 'asset1',
                        type: 'DEPOSIT',
                        amount: 50000,
                        currency: 'CNY',
                        exchangeRate: 1,
                        date: '2024-01-15',
                        notes: '初始存款'
                    },
                    {
                        id: 'tx2',
                        asset_id: 'asset1',
                        type: 'INTEREST',
                        amount: 500,
                        currency: 'CNY',
                        exchangeRate: 1,
                        date: '2024-02-15',
                        notes: '利息收入'
                    },
                    {
                        id: 'tx3',
                        asset_id: 'asset2',
                        type: 'DEPOSIT',
                        amount: 100000,
                        currency: 'CNY',
                        exchangeRate: 1,
                        date: '2024-01-20',
                        notes: '定期存款'
                    },
                    {
                        id: 'tx4',
                        asset_id: 'asset2',
                        type: 'INTEREST',
                        amount: 2000,
                        currency: 'CNY',
                        exchangeRate: 1,
                        date: '2024-03-20',
                        notes: '定期利息'
                    }
                ];
            }
        } catch (error) {
            console.error('❌ 获取交易数据失败，使用模拟数据:', error);
            // 返回一些模拟数据用于测试
            return [
                {
                    id: 'tx1',
                    asset_id: 'asset1',
                    type: 'DEPOSIT',
                    amount: 50000,
                    currency: 'CNY',
                    exchangeRate: 1,
                    date: '2024-01-15',
                    notes: '初始存款'
                },
                {
                    id: 'tx2',
                    asset_id: 'asset1',
                    type: 'INTEREST',
                    amount: 500,
                    currency: 'CNY',
                    exchangeRate: 1,
                    date: '2024-02-15',
                    notes: '利息收入'
                },
                {
                    id: 'tx3',
                    asset_id: 'asset2',
                    type: 'DEPOSIT',
                    amount: 100000,
                    currency: 'CNY',
                    exchangeRate: 1,
                    date: '2024-01-20',
                    notes: '定期存款'
                },
                {
                    id: 'tx4',
                    asset_id: 'asset2',
                    type: 'INTEREST',
                    amount: 2000,
                    currency: 'CNY',
                    exchangeRate: 1,
                    date: '2024-03-20',
                    notes: '定期利息'
                }
            ];
        }
    }

    async loadPortfolioData() {
        console.log('加载投资组合数据');
        // TODO: 实现投资组合页面数据加载
    }

    showErrorMessage(message) {
        // 创建错误提示
        const errorElement = document.createElement('div');
        errorElement.className = 'error-notification';
        errorElement.textContent = message;
        
        Object.assign(errorElement.style, {
            position: 'fixed',
            top: '80px',
            right: '20px',
            background: 'var(--danger)',
            color: 'white',
            padding: '12px 20px',
            borderRadius: '8px',
            boxShadow: 'var(--shadow-lg)',
            zIndex: '1000',
            fontSize: '14px',
            fontWeight: '500',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });
        
        document.body.appendChild(errorElement);
        
        setTimeout(() => {
            errorElement.style.transform = 'translateX(0)';
        }, 100);
        
        setTimeout(() => {
            errorElement.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (document.body.contains(errorElement)) {
                    document.body.removeChild(errorElement);
                }
            }, 300);
        }, 3000);
    }

    // 公共方法：获取当前币种
    getCurrentCurrency() {
        return this.currentCurrency;
    }

    // 公共方法：获取当前页面
    getCurrentPage() {
        return this.currentPage;
    }

    updateCharts(positions) {
        // 确保图表管理器已初始化
        if (!this.chartManager) {
            console.log('⚠️ 图表管理器未初始化，跳过图表更新');
            return;
        }
        
        try {
            // 安全地更新主图表（使用实际持仓数据）
            this.chartManager.updateMainChart(positions);
            
            // 更新资产类型图表
            this.chartManager.updateAssetTypeChart(positions);
            
            // 更新现金及等价物图表
            this.chartManager.updateCashChart(positions);
            
            // 更新固定收益图表
            this.chartManager.updateFixedIncomeChart(positions);
        } catch (error) {
            console.error('❌ 图表更新失败:', error);
        }
    }
}

// 当DOM加载完成后初始化应用（避免重复初始化）
document.addEventListener('DOMContentLoaded', () => {
    if (!window.wealthLiteApp) {
        window.wealthLiteApp = new WealthLiteApp();
    }
});

// 导出类以供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WealthLiteApp;
} 