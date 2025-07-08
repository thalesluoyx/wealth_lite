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
        // 这里会调用图表更新逻辑
        if (window.chartManager) {
            window.chartManager.updateTimeRange(range);
        }
    }

    openSearchModal() {
        console.log('打开搜索模态框');
        // TODO: 实现搜索功能
    }

    async loadDashboardData() {
        try {
            // 调用后端API获取仪表板数据
            const response = await fetch('/api/dashboard/summary');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('✅ 仪表板数据加载成功:', data);
            this.updateDashboardUI(data);
        } catch (error) {
            console.error('❌ 获取仪表板数据失败:', error);
            this.showErrorMessage('数据加载失败，请稍后重试');
        }
    }

    async fetchDashboardData() {
        try {
            // 调用后端API获取仪表板数据
            const response = await fetch('/api/dashboard/summary');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('✅ 仪表板数据加载成功:', data);
            return data;
            
        } catch (error) {
            console.error('❌ 获取仪表板数据失败:', error);
            // 如果API调用失败，返回默认数据避免页面崩溃
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

    updateDashboardUI(data) {
        this.dashboardData = data; // 存储仪表板数据
        // 更新总资产
        const totalAmountElement = document.getElementById('totalAmount');
        if (totalAmountElement) {
            totalAmountElement.innerHTML = `${this.formatAmount(data.totalAssets)}<span class="currency">${this.getCurrencySymbol(this.currentCurrency)}</span>`;
            totalAmountElement.dataset.amount = data.totalAssets;
        }
        
        // 更新变化信息
        const totalChangeElement = document.getElementById('totalChange');
        const totalChangePercentElement = document.getElementById('totalChangePercent');
        
        if (totalChangeElement) {
            totalChangeElement.textContent = `+${this.formatAmount(data.totalChange)}`;
            totalChangeElement.dataset.amount = data.totalChange;
        }
        
        if (totalChangePercentElement) {
            totalChangePercentElement.textContent = `+${data.totalChangePercent}%`;
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
                    <span class="amount" data-amount="${position.amount}">${this.formatAmount(position.amount)}</span>
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
            <td style="font-weight:bold; text-align:right;">${this.formatAmount(totalAmount)}</td>
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
        
        // 资产管理器已在应用启动时初始化
        if (this.assetManager) {
            // 刷新数据
            this.assetManager.loadAssets();
        }
    }

    async loadTransactionsData() {
        console.log('加载交易数据');
        
        // 交易管理器已在应用启动时初始化
        if (this.transactionManager) {
            // 刷新数据
            this.transactionManager.loadInitialData();
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
        if (!this.chartManager) return;
        
        // 更新资产类型图表
        this.chartManager.updateAssetTypeChart(positions);
        
        // 更新现金及等价物图表
        this.chartManager.updateCashChart(positions);
        
        // 更新固定收益图表
        this.chartManager.updateFixedIncomeChart(positions);
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