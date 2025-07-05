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
        
        positionsTableBody.innerHTML = positions.map(position => `
            <tr data-position-id="${position.id}">
                <td>
                    <div class="asset-info">
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
                <td>${position.currency}</td>
                <td>${this.calculateHoldingDays(position.firstTransactionDate)} 天</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-action withdraw" data-action="withdraw" data-asset-id="${position.id}">
                            <i data-lucide="minus-circle"></i>
                            提取
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
        
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
                this.handlePositionWithdraw(assetId);
            });
        });
    }
    
    handlePositionWithdraw(assetId) {
        // 切换到交易记录页面
        this.navigateToPage('transactions');
        
        // 等待页面加载完成后打开提取交易模态窗口
        setTimeout(() => {
            if (this.transactionManager) {
                this.transactionManager.openWithdrawTransactionModal(assetId);
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
}

// 当DOM加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.wealthLiteApp = new WealthLiteApp();
});

// 导出类以供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WealthLiteApp;
} 