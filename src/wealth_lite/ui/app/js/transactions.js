/**
 * 交易管理器
 * 处理交易记录的增删改查和相关UI交互
 */

class TransactionManager {
    constructor(app) {
        this.app = app;
        this.transactions = [];
        this.assets = [];
        this.currentFilters = {
            search: '',
            type: '',
            asset: '',
            startDate: '',
            endDate: ''
        };
        this.currentSort = {
            field: 'date',
            direction: 'desc'
        };
        this.currentPage = 1;
        this.pageSize = 10;
        this.initialized = false;
        this.editingTransactionId = null; // 编辑状态标识
        this.isWithdrawMode = false; // 提取模式标识
        this.lockedAssetId = null; // 锁定的资产ID
        
        // 固定收益产品管理器
        this.fixedIncomeManager = null;
        
        // 延迟初始化，确保DOM元素存在
        setTimeout(() => {
            this.init();
        }, 100);
    }

    init() {
        if (this.initialized) return;
        
        this.initializeFixedIncomeManagers();
        this.bindEvents();
        this.loadInitialData();
        this.initialized = true;
    }

    /**
     * 初始化固定收益产品管理器
     */
    initializeFixedIncomeManagers() {
        console.log('🔧 开始初始化固定收益管理器...');
        
        // 检查FixedIncomeManager是否存在
        if (typeof FixedIncomeManager === 'undefined') {
            console.error('❌ FixedIncomeManager类未找到，请检查fixed-income-manager.js是否正确加载');
            return;
        }
        
        try {
            // 初始化统一的固定收益管理器
            this.fixedIncomeManager = new FixedIncomeManager(this);
            console.log('✅ 固定收益产品管理器初始化完成');
            console.log('🏦 FixedIncomeManager实例:', this.fixedIncomeManager);
        } catch (error) {
            console.error('❌ 固定收益管理器初始化失败:', error);
        }
    }

    bindEvents() {
        console.log('🔧 绑定交易管理器事件...');
        
        // 新增交易按钮
        const addTransactionBtn = document.getElementById('addTransactionBtn');
        if (addTransactionBtn) {
            addTransactionBtn.addEventListener('click', () => {
                console.log('📝 打开新增交易模态窗口');
                this.openAddTransactionModal();
            });
        } else {
            console.warn('⚠️ 未找到addTransactionBtn元素');
        }

        // 表单提交事件
        const addTransactionForm = document.getElementById('addTransactionForm');
        if (addTransactionForm) {
            addTransactionForm.addEventListener('submit', (e) => {
                console.log('💾 提交交易表单');
                e.preventDefault();
                this.handleTransactionSubmit();
            });
        } else {
            console.warn('⚠️ 未找到addTransactionForm元素');
        }

        // 模态窗口关闭事件
        document.getElementById('closeTransactionModal')?.addEventListener('click', () => {
            this.closeAddTransactionModal();
        });

        document.getElementById('cancelTransactionBtn')?.addEventListener('click', () => {
            this.closeAddTransactionModal();
        });

        // 创建新资产按钮事件
        const createAssetBtn = document.getElementById('createAssetBtn');
        if (createAssetBtn) {
            createAssetBtn.addEventListener('click', () => {
                console.log('🏢 打开新增资产模态窗口');
                this.openCreateAssetModal();
            });
        } else {
            console.warn('⚠️ 未找到createAssetBtn元素');
        }

        // 筛选和搜索事件
        document.getElementById('transactionSearch')?.addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });

        document.getElementById('transactionTypeFilter')?.addEventListener('change', (e) => {
            this.handleTypeFilter(e.target.value);
        });

        document.getElementById('assetFilter')?.addEventListener('change', (e) => {
            this.handleAssetFilter(e.target.value);
        });

        document.getElementById('startDate')?.addEventListener('change', (e) => {
            this.handleDateFilter();
        });

        document.getElementById('endDate')?.addEventListener('change', (e) => {
            this.handleDateFilter();
        });

        // 汇率字段显示/隐藏
        document.getElementById('transactionCurrency')?.addEventListener('change', (e) => {
            this.handleCurrencyChange(e.target.value);
            // 通知固定收益管理器处理币种变化
            if (this.fixedIncomeManager) {
                this.fixedIncomeManager.handleCurrencyChangeForFixedIncome();
            }
        });

        // 资产选择变化时显示资产类型
        document.getElementById('assetSelect')?.addEventListener('change', (e) => {
            this.handleAssetSelectionChange(e.target.value);
        });

        // 交易类型变化时通知固定收益管理器
        document.getElementById('transactionType')?.addEventListener('change', (e) => {
            if (this.fixedIncomeManager) {
                this.fixedIncomeManager.handleTransactionTypeChange(e.target.value);
            }
        });

        // 交易日期变化时通知固定收益管理器
        document.getElementById('transactionDate')?.addEventListener('change', () => {
            console.log('🎯 TransactionManager: transactionDate change 事件触发');
            if (this.fixedIncomeManager) {
                this.fixedIncomeManager.handleTransactionDateChange();
            }
        });

        document.getElementById('transactionDate')?.addEventListener('input', () => {
            console.log('🎯 TransactionManager: transactionDate input 事件触发');
            if (this.fixedIncomeManager) {
                this.fixedIncomeManager.handleTransactionDateChange();
            }
        });

        // 表格排序
        document.querySelectorAll('[data-sort]').forEach(th => {
            th.addEventListener('click', () => {
                this.handleSort(th.dataset.sort);
            });
        });

        // 分页
        document.getElementById('prevPage')?.addEventListener('click', () => {
            this.handlePagination(this.currentPage - 1);
        });

        document.getElementById('nextPage')?.addEventListener('click', () => {
            this.handlePagination(this.currentPage + 1);
        });

        // 导出按钮
        document.getElementById('exportBtn')?.addEventListener('click', () => {
            this.handleExport();
        });

        // 模态窗口背景点击关闭功能已移除，避免误操作
    }

    async loadInitialData() {
        try {
            // 并行加载交易和资产数据
            const [transactionsData, assetsData] = await Promise.all([
                this.fetchTransactions(),
                this.fetchAssets()
            ]);
            
            this.transactions = transactionsData;
            this.assets = assetsData;
            
            this.updateUI();
            this.populateAssetFilters();
        } catch (error) {
            console.error('加载交易数据失败:', error);
            this.app.showErrorMessage('数据加载失败，请稍后重试');
        }
    }

    async fetchTransactions() {
        try {
            const response = await fetch('/api/transactions');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('❌ 获取交易数据失败:', error);
            return [];
        }
    }

    async fetchAssets() {
        try {
            const response = await fetch('/api/assets');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('❌ 获取资产数据失败:', error);
            return [];
        }
    }

    updateUI() {
        this.updateStats();
        this.updateTransactionTable();
        this.updatePagination();
    }

    updateStats() {
        const currentMonth = new Date().getMonth();
        const currentYear = new Date().getFullYear();
        const lastMonth = currentMonth === 0 ? 11 : currentMonth - 1;
        const lastMonthYear = currentMonth === 0 ? currentYear - 1 : currentYear;
        
        // 本月交易
        const monthlyTransactions = this.transactions.filter(t => {
            const transactionDate = new Date(t.date);
            return transactionDate.getMonth() === currentMonth && 
                   transactionDate.getFullYear() === currentYear;
        });

        // 上月交易（用于计算变化）
        const lastMonthTransactions = this.transactions.filter(t => {
            const transactionDate = new Date(t.date);
            return transactionDate.getMonth() === lastMonth && 
                   transactionDate.getFullYear() === lastMonthYear;
        });

        // 本月统计
        const monthlyCount = monthlyTransactions.length;
        const monthlyAmount = monthlyTransactions.reduce((sum, t) => {
            const exchangeRate = t.exchangeRate || 1; // 如果没有汇率，默认为1
            return sum + (parseFloat(t.amount) * exchangeRate);
        }, 0);
        
        const monthlyReturn = monthlyTransactions
            .filter(t => t.type === 'INTEREST' || t.type === 'DIVIDEND')
            .reduce((sum, t) => {
                const exchangeRate = t.exchangeRate || 1;
                return sum + (parseFloat(t.amount) * exchangeRate);
            }, 0);

        // 上月统计（用于计算变化）
        const lastMonthCount = lastMonthTransactions.length;
        const lastMonthAmount = lastMonthTransactions.reduce((sum, t) => {
            const exchangeRate = t.exchangeRate || 1;
            return sum + (parseFloat(t.amount) * exchangeRate);
        }, 0);
        
        const lastMonthReturn = lastMonthTransactions
            .filter(t => t.type === 'INTEREST' || t.type === 'DIVIDEND')
            .reduce((sum, t) => {
                const exchangeRate = t.exchangeRate || 1;
                return sum + (parseFloat(t.amount) * exchangeRate);
            }, 0);

        // 计算变化
        const countChange = monthlyCount - lastMonthCount;
        const amountChangePercent = lastMonthAmount > 0 
            ? ((monthlyAmount - lastMonthAmount) / lastMonthAmount * 100).toFixed(1)
            : 0;
        const returnChangePercent = lastMonthReturn > 0 
            ? ((monthlyReturn - lastMonthReturn) / lastMonthReturn * 100).toFixed(1)
            : 0;

        // 更新UI
        document.getElementById('monthlyTransactionCount').textContent = monthlyCount;
        document.getElementById('monthlyTransactionAmount').textContent = 
            this.app.formatAmount(Math.round(monthlyAmount));
        document.getElementById('monthlyReturn').textContent = 
            this.app.formatAmount(Math.round(monthlyReturn));

        // 更新变化显示
        const countChangeElement = document.querySelector('#monthlyTransactionCount').parentElement.querySelector('.stat-change');
        const amountChangeElement = document.querySelector('#monthlyTransactionAmount').parentElement.querySelector('.stat-change');
        const returnChangeElement = document.querySelector('#monthlyReturn').parentElement.querySelector('.stat-change');

        if (countChangeElement) {
            countChangeElement.textContent = countChange >= 0 ? `+${countChange}` : `${countChange}`;
            countChangeElement.className = `stat-change ${countChange >= 0 ? 'positive' : 'negative'}`;
        }

        if (amountChangeElement) {
            amountChangeElement.textContent = `${amountChangePercent >= 0 ? '+' : ''}${amountChangePercent}%`;
            amountChangeElement.className = `stat-change ${amountChangePercent >= 0 ? 'positive' : 'negative'}`;
        }

        if (returnChangeElement) {
            returnChangeElement.textContent = `${returnChangePercent >= 0 ? '+' : ''}${returnChangePercent}%`;
            returnChangeElement.className = `stat-change ${returnChangePercent >= 0 ? 'positive' : 'negative'}`;
        }
    }

    updateTransactionTable() {
        const filteredTransactions = this.getFilteredTransactions();
        const sortedTransactions = this.getSortedTransactions(filteredTransactions);
        const paginatedTransactions = this.getPaginatedTransactions(sortedTransactions);

        const tbody = document.getElementById('transactionsTableBody');
        const emptyState = document.getElementById('transactionsEmpty');
        
        if (paginatedTransactions.length === 0) {
            tbody.innerHTML = '';
            emptyState.style.display = 'block';
        } else {
            emptyState.style.display = 'none';
            tbody.innerHTML = paginatedTransactions.map(transaction => 
                this.renderTransactionRow(transaction)
            ).join('');
        }

        // 更新交易计数
        document.getElementById('transactionCount').textContent = 
            `共 ${filteredTransactions.length} 笔交易`;

        // 重新绑定操作按钮事件
        this.bindTableActions();
    }

    renderTransactionRow(transaction) {
        // 根据asset_id查找资产名
        const asset = this.assets.find(a => a.id === transaction.asset_id);
        const assetName = asset ? asset.name : '-';
        const typeClass = transaction.type.toLowerCase();
        const typeText = this.getTransactionTypeText(transaction.type);
        
        return `
            <tr data-transaction-id="${transaction.id}">
                <td>${this.formatDate(transaction.date)}</td>
                <td>${assetName}</td>
                <td>
                    <span class="transaction-type ${typeClass}">
                        ${typeText}
                    </span>
                </td>
                <td>${this.app.formatAmount(transaction.amount)}</td>
                <td>${transaction.currency}</td>
                <td>${transaction.notes || '-'}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-action edit" data-action="edit" data-id="${transaction.id}">
                            <i data-lucide="edit-2"></i>
                            编辑
                        </button>

                        <button class="btn-action delete" data-action="delete" data-id="${transaction.id}">
                            <i data-lucide="trash-2"></i>
                            删除
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    bindTableActions() {
        // 重新初始化图标
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        // 绑定编辑和删除按钮
        document.querySelectorAll('[data-action="edit"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.target.closest('[data-id]').dataset.id; // 保持原始类型，不转换为数字
                console.log('编辑交易ID:', id, '类型:', typeof id);
                this.handleEditTransaction(id);
            });
        });

        document.querySelectorAll('[data-action="delete"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.target.closest('[data-id]').dataset.id; // 保持原始类型，不转换为数字
                console.log('删除交易ID:', id, '类型:', typeof id);
                this.handleDeleteTransaction(id);
            });
        });
    }

    getFilteredTransactions() {
        return this.transactions.filter(transaction => {
            // 搜索过滤
            if (this.currentFilters.search) {
                const searchTerm = this.currentFilters.search.toLowerCase();
                if (!transaction.assetName.toLowerCase().includes(searchTerm) &&
                    !transaction.notes?.toLowerCase().includes(searchTerm)) {
                    return false;
                }
            }

            // 类型过滤
            if (this.currentFilters.type && transaction.type !== this.currentFilters.type) {
                return false;
            }

            // 资产过滤
            if (this.currentFilters.asset && String(transaction.asset_id || transaction.assetId) !== String(this.currentFilters.asset)) {
                return false;
            }

            // 日期过滤
            if (this.currentFilters.startDate && transaction.date < this.currentFilters.startDate) {
                return false;
            }

            if (this.currentFilters.endDate && transaction.date > this.currentFilters.endDate) {
                return false;
            }

            return true;
        });
    }

    getSortedTransactions(transactions) {
        return [...transactions].sort((a, b) => {
            let aValue, bValue;

            // 特殊处理不同类型的排序
            if (this.currentSort.field === 'asset') {
                // 资产列需要通过asset_id查找资产名称
                const assetA = this.assets.find(asset => asset.id === a.asset_id);
                const assetB = this.assets.find(asset => asset.id === b.asset_id);
                aValue = assetA ? assetA.name.toLowerCase() : '';
                bValue = assetB ? assetB.name.toLowerCase() : '';
            } else if (this.currentSort.field === 'date') {
                aValue = new Date(a[this.currentSort.field]);
                bValue = new Date(b[this.currentSort.field]);
            } else if (this.currentSort.field === 'amount') {
                aValue = parseFloat(a[this.currentSort.field]);
                bValue = parseFloat(b[this.currentSort.field]);
            } else {
                aValue = a[this.currentSort.field];
                bValue = b[this.currentSort.field];
                
                if (typeof aValue === 'string') {
                    aValue = aValue.toLowerCase();
                }
                if (typeof bValue === 'string') {
                    bValue = bValue.toLowerCase();
                }
            }

            if (aValue < bValue) {
                return this.currentSort.direction === 'asc' ? -1 : 1;
            }
            if (aValue > bValue) {
                return this.currentSort.direction === 'asc' ? 1 : -1;
            }
            return 0;
        });
    }

    getPaginatedTransactions(transactions) {
        const startIndex = (this.currentPage - 1) * this.pageSize;
        return transactions.slice(startIndex, startIndex + this.pageSize);
    }

    updatePagination() {
        const filteredTransactions = this.getFilteredTransactions();
        const totalPages = Math.ceil(filteredTransactions.length / this.pageSize);
        const startIndex = (this.currentPage - 1) * this.pageSize + 1;
        const endIndex = Math.min(this.currentPage * this.pageSize, filteredTransactions.length);

        document.getElementById('paginationStart').textContent = startIndex;
        document.getElementById('paginationEnd').textContent = endIndex;
        document.getElementById('paginationTotal').textContent = filteredTransactions.length;

        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');

        prevBtn.disabled = this.currentPage <= 1;
        nextBtn.disabled = this.currentPage >= totalPages;
    }

    // 事件处理方法
    openAddTransactionModal() {
        // 重置编辑状态
        this.editingTransactionId = null;
        this.isWithdrawMode = false;
        this.lockedAssetId = null;
        
        // 重置模态窗口标题和按钮文本 - 添加安全检查
        const modalTitle = document.querySelector('#addTransactionModal .modal-header h3');
        if (modalTitle) {
            modalTitle.textContent = '新增交易';
        }
        
        const submitBtn = document.querySelector('#addTransactionModal .modal-footer .btn-primary');
        if (submitBtn) {
            submitBtn.textContent = '保存交易';
        }
        
        this.populateAssetSelect();
        this.populateTransactionTypes();
        this.setDefaultTransactionDate();
        document.getElementById('addTransactionModal').classList.add('show');
    }

    // 新增方法：从持仓明细触发的提取操作
    async openWithdrawTransactionModal(assetId, positionData = null) {
        // 设置提取模式
        this.editingTransactionId = null;
        this.isWithdrawMode = true;
        this.lockedAssetId = assetId;
        
        // 设置模态窗口标题
        const modalTitle = document.querySelector('#addTransactionModal .modal-header h3');
        if (modalTitle) {
            modalTitle.textContent = '提取资产';
        }
        
        const submitBtn = document.querySelector('#addTransactionModal .modal-footer .btn-primary');
        if (submitBtn) {
            submitBtn.textContent = '确认提取';
        }
        
        this.populateAssetSelect();
        this.populateTransactionTypes();
        this.setDefaultTransactionDate();
        
        // 设置并锁定资产选择
        const assetSelect = document.getElementById('assetSelect');
        if (assetSelect) {
            assetSelect.value = assetId;
            assetSelect.disabled = true;
            assetSelect.classList.add('field-locked');
            
            // 触发资产选择变化事件
            this.handleAssetSelectionChange(assetId);
        }
        
        // 设置并锁定交易类型为提取
        const transactionTypeSelect = document.getElementById('transactionType');
        if (transactionTypeSelect) {
            transactionTypeSelect.value = 'WITHDRAW';
            transactionTypeSelect.disabled = true;
            transactionTypeSelect.classList.add('field-locked');
            
            // 手动触发交易类型变化事件，确保固定收益字段正确隐藏
            if (this.fixedIncomeManager) {
                this.fixedIncomeManager.handleTransactionTypeChange('WITHDRAW');
            }
        }
        
        // 自动填写提取金额和币种
        if (positionData) {
            // 使用传入的持仓数据
            console.log('📊 使用传入的持仓数据:', positionData);
            
            // 自动填写提取金额：优先使用原币种金额，如果没有则使用人民币等值
            const amountField = document.getElementById('transactionAmount');
            let withdrawAmount = positionData.amount; // 默认使用人民币等值
            
            // 如果是外币且有原币种金额，使用原币种金额
            if (positionData.currency !== 'CNY' && positionData.amount_original_currency) {
                withdrawAmount = positionData.amount_original_currency;
                console.log('🌍 外币资产，使用原币种金额:', withdrawAmount, positionData.currency);
            } else if (positionData.currency === 'CNY') {
                withdrawAmount = positionData.amount;
                console.log('🇨🇳 人民币资产，使用人民币金额:', withdrawAmount);
            }
            
            if (amountField && withdrawAmount) {
                amountField.value = withdrawAmount;
                console.log('💰 自动填写提取金额:', withdrawAmount, '币种:', positionData.currency);
            }
            
            // 自动设置币种为持仓币种
            const currencyField = document.getElementById('transactionCurrency');
            if (currencyField && positionData.currency) {
                const currencyDisplay = this.getCurrencyDisplayName(positionData.currency);
                currencyField.value = currencyDisplay;
                currencyField.setAttribute('data-currency-code', positionData.currency);
                console.log('💱 自动设置币种:', positionData.currency, '显示:', currencyDisplay);
                
                // 触发币种变化事件以处理汇率字段
                this.handleCurrencyChange(positionData.currency);
                
                // 通知固定收益管理器处理币种变化
                if (this.fixedIncomeManager) {
                    this.fixedIncomeManager.handleCurrencyChangeForFixedIncome();
                }
            }
        } else {
            // 获取持仓信息并自动填写提取金额（备用方案）
            try {
                console.log('🔍 获取持仓信息以自动填写提取金额...');
                const response = await fetch(`/api/positions/${assetId}`);
                if (response.ok) {
                    const position = await response.json();
                    console.log('📊 获取到持仓信息:', position);
                    
                    // 自动填写提取金额：优先使用原币种金额
                    const amountField = document.getElementById('transactionAmount');
                    let withdrawAmount = position.current_value; // 默认使用人民币等值
                    
                    // 如果是外币且有原币种金额，使用原币种金额
                    if (position.currency !== 'CNY' && position.current_value_original_currency) {
                        withdrawAmount = position.current_value_original_currency;
                        console.log('🌍 外币资产（API），使用原币种金额:', withdrawAmount, position.currency);
                    } else if (position.currency === 'CNY') {
                        withdrawAmount = position.current_value;
                        console.log('🇨🇳 人民币资产（API），使用人民币金额:', withdrawAmount);
                    }
                    
                    if (amountField && withdrawAmount) {
                        amountField.value = withdrawAmount;
                        console.log('💰 自动填写提取金额（API）:', withdrawAmount, '币种:', position.currency);
                    }
                    
                    // 自动设置币种为持仓币种
                    const currencyField = document.getElementById('transactionCurrency');
                    if (currencyField && position.currency) {
                        const currencyDisplay = this.getCurrencyDisplayName(position.currency);
                        currencyField.value = currencyDisplay;
                        currencyField.setAttribute('data-currency-code', position.currency);
                        console.log('💱 自动设置币种（API）:', position.currency, '显示:', currencyDisplay);
                        
                        // 触发币种变化事件以处理汇率字段
                        this.handleCurrencyChange(position.currency);
                        
                        // 通知固定收益管理器处理币种变化
                        if (this.fixedIncomeManager) {
                            this.fixedIncomeManager.handleCurrencyChangeForFixedIncome();
                        }
                    }
                } else {
                    console.warn('⚠️ 获取持仓信息失败:', response.status);
                }
            } catch (error) {
                console.error('❌ 获取持仓信息时发生错误:', error);
            }
        }
        
        document.getElementById('addTransactionModal').classList.add('show');
    }

    closeAddTransactionModal() {
        document.getElementById('addTransactionModal').classList.remove('show');
        this.resetTransactionForm();
        
        // 重置编辑状态和提取模式
        this.editingTransactionId = null;
        this.isWithdrawMode = false;
        this.lockedAssetId = null;
        
        // 重置字段锁定状态
        this.resetFieldLocks();
        
        // 重置模态窗口标题和按钮文本 - 添加安全检查
        const modalTitle = document.querySelector('#addTransactionModal .modal-header h3');
        if (modalTitle) {
            modalTitle.textContent = '新增交易';
        }
        
        const submitBtn = document.querySelector('#addTransactionModal .modal-footer .btn-primary');
        if (submitBtn) {
            submitBtn.textContent = '保存交易';
        }
    }

    openCreateAssetModal() {
        // 调用 assetManager 的方法打开资产创建模态框
        if (window.assetManager) {
            // 保存当前的 TransactionManager 实例引用
            const transactionManager = this;
            
            // 临时覆盖 assetManager 的 saveAsset 方法，添加成功回调
            const originalSaveAsset = window.assetManager.saveAsset.bind(window.assetManager);
            window.assetManager.saveAsset = async function() {
                try {
                    await originalSaveAsset();
                    
                    // 资产创建成功后，刷新交易页面的资产列表
                    console.log('🔄 资产创建成功，刷新交易页面资产列表');
                    const assets = await transactionManager.fetchAssets();
                    transactionManager.assets = assets;
                    transactionManager.populateAssetSelect();
                    transactionManager.populateAssetFilters();
                    
                    // 恢复原始方法
                    window.assetManager.saveAsset = originalSaveAsset;
                } catch (error) {
                    // 恢复原始方法
                    window.assetManager.saveAsset = originalSaveAsset;
                    throw error;
                }
            };
            
            window.assetManager.openAssetModal();
        } else {
            console.error('❌ AssetManager 未初始化');
            this.showValidationError('资产管理器未初始化，请刷新页面重试');
        }
    }

    populateAssetSelect() {
        const select = document.getElementById('assetSelect');
        select.innerHTML = '<option value="">请选择资产...</option>';
        
        this.assets.forEach(asset => {
            const option = document.createElement('option');
            option.value = asset.id;
            option.textContent = asset.name;
            option.dataset.assetType = asset.asset_type; // 添加资产类型数据属性
            select.appendChild(option);
        });
    }

    populateTransactionTypes() {
        const select = document.getElementById('transactionType');
        
        if (this.isWithdrawMode) {
            // 提取模式：只显示提取选项
            select.innerHTML = `
                <option value="">请选择交易类型...</option>
                <option value="WITHDRAW">提取</option>
            `;
        } else {
            // 普通模式：显示存入和利息选项
            select.innerHTML = `
                <option value="">请选择交易类型...</option>
                <option value="DEPOSIT">存入</option>
                <option value="INTEREST">利息</option>
            `;
        }
    }

    populateAssetFilters() {
        const select = document.getElementById('assetFilter');
        select.innerHTML = '<option value="">所有资产</option>';
        
        this.assets.forEach(asset => {
            const option = document.createElement('option');
            option.value = asset.id;
            option.textContent = asset.name;
            select.appendChild(option);
        });
    }

    setDefaultTransactionDate() {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('transactionDate').value = today;
        
        // 通知固定收益管理器交易日期变化
        if (this.fixedIncomeManager) {
            this.fixedIncomeManager.handleTransactionDateChange();
        }
    }

    handleCurrencyChange(currency) {
        const exchangeRateGroup = document.getElementById('exchangeRateGroup');
        const exchangeRateField = document.getElementById('exchangeRate');
        
        if (currency === 'CNY') {
            exchangeRateGroup.style.display = 'none';
        } else {
            exchangeRateGroup.style.display = 'block';
            
            // 只在非编辑模式下设置默认汇率
            if (!this.editingTransactionId) {
                const defaultRates = {
                    'USD': 7.2,
                    'HKD': 0.9,
                    'EUR': 7.8
                };
                exchangeRateField.value = defaultRates[currency] || '';
                console.log('💱 设置默认汇率（新增模式）:', defaultRates[currency]);
            } else {
                console.log('✏️ 编辑模式：保持现有汇率 -', exchangeRateField.value);
            }
        }
    }

    handleAssetSelectionChange(assetId) {
        console.log('🔄 资产选择变化:', assetId);
        
        const assetTypeDisplay = document.getElementById('assetTypeDisplay');
        const assetTypeValue = document.getElementById('assetTypeValue');
        
        if (!assetId) {
            // 没有选择资产时隐藏资产类型显示
            assetTypeDisplay.style.display = 'none';
            
            // 清空币种字段
            const currencyField = document.getElementById('transactionCurrency');
            if (currencyField) {
                currencyField.value = '请先选择资产...';
                currencyField.removeAttribute('data-currency-code');
            }
            
            // 通知固定收益管理器
            if (this.fixedIncomeManager) {
                console.log('📢 通知固定收益管理器: 资产类型变化为 null');
                this.fixedIncomeManager.handleAssetTypeChange(null);
            } else {
                console.warn('⚠️ 固定收益管理器未初始化');
            }
            return;
        }
        
        // 根据资产ID查找资产信息
        const selectedAsset = this.assets.find(asset => asset.id === assetId);
        console.log('🔍 查找到的资产:', selectedAsset);
        
        if (selectedAsset) {
            // 显示资产类型
            const assetTypeDisplayName = this.getAssetTypeDisplayName(selectedAsset.asset_type);
            assetTypeValue.textContent = assetTypeDisplayName;
            assetTypeDisplay.style.display = 'block';
            
            console.log('📊 资产类型:', selectedAsset.asset_type, '显示名称:', assetTypeDisplayName);
            
            // 自动设置交易币种为资产币种
            const currencyField = document.getElementById('transactionCurrency');
            if (currencyField && selectedAsset.currency) {
                const currencyDisplay = this.getCurrencyDisplayName(selectedAsset.currency);
                currencyField.value = currencyDisplay;
                currencyField.setAttribute('data-currency-code', selectedAsset.currency);
                console.log('💱 自动设置币种:', selectedAsset.currency, '显示:', currencyDisplay);
                
                // 触发币种变化处理
                this.handleCurrencyChange(selectedAsset.currency);
                
                // 通知固定收益管理器处理币种变化
                if (this.fixedIncomeManager) {
                    this.fixedIncomeManager.handleCurrencyChangeForFixedIncome();
                }
            }
            
            // 通知固定收益管理器资产类型变化
            if (this.fixedIncomeManager) {
                console.log('📢 通知固定收益管理器: 资产类型变化为', selectedAsset.asset_type);
                this.fixedIncomeManager.handleAssetTypeChange(selectedAsset.asset_type);
            } else {
                console.warn('⚠️ 固定收益管理器未初始化');
            }
        } else {
            console.warn('⚠️ 未找到对应的资产信息');
            assetTypeDisplay.style.display = 'none';
            
            // 通知固定收益管理器
            if (this.fixedIncomeManager) {
                console.log('📢 通知固定收益管理器: 资产类型变化为 null (未找到资产)');
                this.fixedIncomeManager.handleAssetTypeChange(null);
            } else {
                console.warn('⚠️ 固定收益管理器未初始化');
            }
        }
    }

    getAssetTypeDisplayName(assetType) {
        const typeMap = {
            'CASH': '现金及等价物',
            'FIXED_INCOME': '固定收益',
            'EQUITY': '权益类'
        };
        return typeMap[assetType] || assetType;
    }

    getCurrencyDisplayName(currencyCode) {
        const currencyMap = {
            'CNY': 'CNY - 人民币',
            'USD': 'USD - 美元',
            'HKD': 'HKD - 港币',
            'EUR': 'EUR - 欧元',
            'JPY': 'JPY - 日元'
        };
        return currencyMap[currencyCode] || `${currencyCode} - 未知币种`;
    }

    async handleTransactionSubmit() {
        console.log('🚀 开始处理交易提交...');
        
        try {
            const formData = this.getTransactionFormData();
            console.log('📝 表单数据:', formData);
            
            // 检查是否为提取模式
            if (this.isWithdrawMode) {
                console.log('💸 检测到提取模式');
                return await this.handleWithdrawSubmit(formData);
            }
            
            // 检查是否为固定收益产品交易
            if (this.isFixedIncomeTransaction(formData)) {
                console.log('🏦 检测到固定收益产品交易');
                return await this.handleFixedIncomeTransactionSubmit(formData);
            }
            
            console.log('💰 普通交易处理');
            if (!this.validateTransactionForm(formData)) {
                console.log('❌ 表单验证失败');
                return;
            }

            try {
                if (this.editingTransactionId) {
                    console.log('✏️ 编辑模式');
                    // 编辑模式：调用PUT API
                    const response = await fetch(`/api/transactions/${this.editingTransactionId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(formData)
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                    }

                    this.showSuccessMessage('交易记录已更新');
                } else {
                    console.log('➕ 新增模式');
                    // 新增模式：调用POST API
                    await this.saveTransaction(formData);
                    this.showSuccessMessage('交易记录已成功保存');
                }
                
                this.closeAddTransactionModal();
                this.loadInitialData(); // 重新加载数据
            } catch (error) {
                console.error('💥 API调用失败:', error);
                this.showValidationError('保存失败: ' + error.message);
            }
        } catch (error) {
            console.error('💥 交易提交处理失败:', error);
            this.showValidationError('处理失败: ' + error.message);
        }
    }

    /**
     * 处理提取资产提交
     */
    async handleWithdrawSubmit(formData) {
        try {
            console.log('💸 开始处理提取资产...');
            
            // 验证提取表单
            if (!this.validateWithdrawForm(formData)) {
                return;
            }

            // 准备提取数据
            const withdrawData = {
                amount: formData.amount,
                currency: formData.currency,
                exchange_rate: formData.exchange_rate,
                date: formData.transaction_date,
                notes: formData.notes
            };

            console.log('📤 提取数据:', withdrawData);

            // 调用提取资产API
            const response = await fetch(`/api/positions/${this.lockedAssetId}/withdraw`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(withdrawData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('✅ 提取成功:', result);

            // 显示成功消息
            this.showSuccessMessage(`资产提取成功！提取金额: ${result.withdraw_amount}，剩余价值: ${result.remaining_value}`);
            
            // 关闭模态窗口
            this.closeAddTransactionModal();
            
            // 重新加载数据
            await this.loadInitialData();
            
            // 通知主应用刷新仪表板数据
            if (this.app && this.app.loadDashboardData) {
                this.app.loadDashboardData();
            }

        } catch (error) {
            console.error('❌ 提取资产失败:', error);
            this.showValidationError('提取失败: ' + error.message);
        }
    }

    /**
     * 验证提取表单
     */
    validateWithdrawForm(data) {
        if (!data.asset_id) {
            this.showValidationError('请选择资产');
            return false;
        }
        if (!data.amount || data.amount <= 0) {
            this.showValidationError('请输入有效的提取金额');
            return false;
        }
        if (!data.currency) {
            this.showValidationError('请选择币种');
            return false;
        }
        if (!data.transaction_date) {
            this.showValidationError('请选择提取日期');
            return false;
        }
        return true;
    }

    /**
     * 处理固定收益产品交易提交
     */
    async handleFixedIncomeTransactionSubmit(formData) {
        try {
            if (!this.fixedIncomeManager) {
                throw new Error('固定收益管理器未初始化');
            }

            // 合并固定收益特有数据
            const fixedIncomeData = this.fixedIncomeManager.getFixedIncomeFormData();
            const completeFormData = { ...formData, ...fixedIncomeData };

            console.log('🏦 固定收益交易数据:', completeFormData);

            // 使用固定收益管理器处理交易
            const result = await this.fixedIncomeManager.handleFixedIncomeTransaction(completeFormData);

            this.showSuccessMessage(this.editingTransactionId ? '固定收益交易更新成功！' : '固定收益交易添加成功！');
            this.closeAddTransactionModal();
            await this.loadInitialData(); // 重新加载数据

        } catch (error) {
            console.error('❌ 固定收益交易提交失败:', error);
            this.showValidationError('固定收益交易提交失败: ' + error.message);
        }
    }

    /**
     * 检查是否为固定收益产品交易
     */
    isFixedIncomeTransaction(formData) {
        // 检查选中的资产类型
        const selectedAsset = this.assets.find(asset => asset.id === formData.asset_id);
        
        console.log('🔍 检查固定收益交易:', {
            assetId: formData.asset_id,
            assetType: selectedAsset?.asset_type,
            isFixedIncome: selectedAsset?.asset_type === 'FIXED_INCOME'
        });
        
        return selectedAsset?.asset_type === 'FIXED_INCOME';
    }

    getTransactionFormData() {
        try {
            // 获取币种字段
            const currencyField = document.getElementById('transactionCurrency');
            const currencyCode = currencyField?.getAttribute('data-currency-code') || currencyField?.value || '';
            
            // 组装表单数据，字段名与后端保持一致
            // 交易类型直接取下拉框的value（如DEPOSIT、PURCHASE等枚举名）
            const data = {
                asset_id: document.getElementById('assetSelect')?.value || '',
                transaction_type: document.getElementById('transactionType')?.value || '',
                amount: parseFloat(document.getElementById('transactionAmount')?.value || '0'),
                currency: currencyCode,
                transaction_date: document.getElementById('transactionDate')?.value || '',
                exchange_rate: parseFloat(document.getElementById('exchangeRate')?.value || '1.0'),
                notes: document.getElementById('transactionNotes')?.value?.trim() || ''
            };
            
            console.log('📊 获取的表单数据:', data);
            console.log('💱 币种处理:', {
                fieldValue: currencyField?.value,
                currencyCode: currencyCode,
                dataAttribute: currencyField?.getAttribute('data-currency-code')
            });
            return data;
        } catch (error) {
            console.error('❌ 获取表单数据失败:', error);
            throw new Error('获取表单数据失败: ' + error.message);
        }
    }

    validateTransactionForm(data) {
        if (!data.asset_id) {
            this.showValidationError('请选择资产');
            return false;
        }
        if (!data.transaction_type) {
            this.showValidationError('请选择交易类型');
            return false;
        }
        if (!data.amount || data.amount <= 0) {
            this.showValidationError('请输入有效的交易金额');
            return false;
        }
        if (!data.currency) {
            this.showValidationError('请选择币种');
            return false;
        }
        if (!data.transaction_date) {
            this.showValidationError('请选择交易日期');
            return false;
        }
        return true;
    }

    async saveTransaction(data) {
        try {
            // 调用后端API创建交易
            const response = await fetch('/api/transactions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                // 处理后端返回的错误信息
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const newTransaction = await response.json();
            console.log('✅ 交易创建成功:', newTransaction);
            return newTransaction;
        } catch (error) {
            console.error('❌ 保存交易失败:', error);
            throw error;
        }
    }

    resetTransactionForm() {
        document.getElementById('addTransactionForm').reset();
        document.getElementById('exchangeRateGroup').style.display = 'none';
        // 隐藏资产类型显示
        document.getElementById('assetTypeDisplay').style.display = 'none';
        
        // 重置币种字段
        const currencyField = document.getElementById('transactionCurrency');
        if (currencyField) {
            currencyField.value = '请先选择资产...';
            currencyField.removeAttribute('data-currency-code');
        }
        
        // 重置固定收益字段
        if (this.fixedIncomeManager) {
            this.fixedIncomeManager.resetFixedIncomeFields();
        }
    }

    resetFieldLocks() {
        // 解除字段锁定
        const fieldsToUnlock = ['assetSelect', 'transactionType', 'transactionCurrency'];
        fieldsToUnlock.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.disabled = false;
                field.classList.remove('field-locked');
            }
        });
    }

    // 筛选和排序处理
    handleSearch(value) {
        this.currentFilters.search = value;
        this.currentPage = 1;
        this.updateTransactionTable();
        this.updatePagination();
    }

    handleTypeFilter(value) {
        this.currentFilters.type = value;
        this.currentPage = 1;
        this.updateTransactionTable();
        this.updatePagination();
    }

    handleAssetFilter(value) {
        this.currentFilters.asset = value;
        this.currentPage = 1;
        this.updateTransactionTable();
        this.updatePagination();
    }

    handleDateFilter() {
        this.currentFilters.startDate = document.getElementById('startDate').value;
        this.currentFilters.endDate = document.getElementById('endDate').value;
        this.currentPage = 1;
        this.updateTransactionTable();
        this.updatePagination();
    }

    handleSort(field) {
        if (this.currentSort.field === field) {
            this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSort.field = field;
            this.currentSort.direction = 'asc';
        }
        
        this.updateTransactionTable();
    }

    handlePagination(page) {
        const filteredTransactions = this.getFilteredTransactions();
        const totalPages = Math.ceil(filteredTransactions.length / this.pageSize);
        
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.updateTransactionTable();
            this.updatePagination();
        }
    }

    async handleEditTransaction(id) {
        console.log('查找交易ID:', id);
        console.log('所有交易数据:', this.transactions);
        console.log('交易ID列表:', this.transactions.map(t => ({ id: t.id, type: typeof t.id })));
        
        // 查找要编辑的交易
        const transaction = this.transactions.find(t => t.id == id); // 使用==而不是===，允许类型转换
        if (!transaction) {
            console.error('未找到交易记录，ID:', id);
            this.showValidationError('交易记录不存在');
            return;
        }

        console.log('找到交易记录:', transaction);

        // 标记为编辑模式
        this.editingTransactionId = id;
        
        // 填充资产选择器（但不重置）
        this.populateAssetSelect();
        
        // 填充表单数据
        document.getElementById('assetSelect').value = transaction.asset_id;
        document.getElementById('transactionType').value = transaction.type;
        document.getElementById('transactionAmount').value = transaction.amount;
        
        // 设置币种字段（新的方式）
        const currencyField = document.getElementById('transactionCurrency');
        if (currencyField && transaction.currency) {
            const currencyDisplay = this.getCurrencyDisplayName(transaction.currency);
            currencyField.value = currencyDisplay;
            currencyField.setAttribute('data-currency-code', transaction.currency);
        }
        
        document.getElementById('transactionDate').value = transaction.date;
        
        // 通知固定收益管理器交易日期变化（编辑模式）
        if (this.fixedIncomeManager) {
            this.fixedIncomeManager.handleTransactionDateChange();
        }
        document.getElementById('transactionNotes').value = transaction.description || transaction.notes || '';
        
        // 显示资产类型
        this.handleAssetSelectionChange(transaction.asset_id);
        
        // 填充固定收益字段（如果适用）
        if (this.fixedIncomeManager) {
            console.log('🏦 调用固定收益管理器填充字段数据');
            await this.fixedIncomeManager.populateFixedIncomeFields(transaction);
        }
        
        // 锁定不可编辑的字段
        document.getElementById('assetSelect').disabled = true;
        document.getElementById('transactionType').disabled = true;
        document.getElementById('transactionCurrency').disabled = true;
        
        // 添加锁定样式
        document.getElementById('assetSelect').classList.add('field-locked');
        document.getElementById('transactionType').classList.add('field-locked');
        document.getElementById('transactionCurrency').classList.add('field-locked');
        
        // 先设置汇率值，再处理币种变化
        if (transaction.currency !== 'CNY') {
            document.getElementById('exchangeRate').value = transaction.exchange_rate || 1.0;
            console.log('💱 设置编辑交易汇率:', transaction.exchange_rate);
        }
        
        // 处理汇率显示（编辑模式下不会覆盖已设置的汇率）
        this.handleCurrencyChange(transaction.currency);
        
        // 更改模态窗口标题和按钮文本 - 添加安全检查
        const modalTitle = document.querySelector('#addTransactionModal .modal-header h3');
        if (modalTitle) {
            modalTitle.textContent = '编辑交易';
        }
        
        const submitBtn = document.querySelector('#addTransactionModal .modal-footer .btn-primary');
        if (submitBtn) {
            submitBtn.textContent = '更新交易';
        }
        
        // 直接显示模态窗口，不调用openAddTransactionModal()
        document.getElementById('addTransactionModal').classList.add('show');
    }

    async handleDeleteTransaction(id) {
        if (confirm('确定要删除这笔交易吗？')) {
            try {
                const response = await fetch(`/api/transactions/${id}`, {
                    method: 'DELETE'
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                }

                // 重新加载数据
                await this.loadInitialData();
                this.showSuccessMessage('交易记录已删除');
            } catch (error) {
                console.error('❌ 删除交易失败:', error);
                this.showValidationError('删除失败，请稍后重试');
            }
        }
    }

    handleExport() {
        console.log('📤 开始导出交易数据');
        
        try {
            // 获取当前筛选后的交易数据
            const filteredTransactions = this.getFilteredTransactions();
            const sortedTransactions = this.getSortedTransactions(filteredTransactions);
            
            if (sortedTransactions.length === 0) {
                this.showValidationError('没有可导出的交易记录');
                return;
            }
            
            // 准备导出数据
            const exportData = this.prepareExportData(sortedTransactions);
            
            // 创建CSV内容
            const csvContent = this.generateCSVContent(exportData);
            
            // 下载文件
            this.downloadCSV(csvContent, this.generateFileName());
            
            this.showSuccessMessage(`成功导出 ${sortedTransactions.length} 笔交易记录`);
            
        } catch (error) {
            console.error('❌ 导出失败:', error);
            this.showValidationError('导出失败，请稍后重试');
        }
    }

    prepareExportData(transactions) {
        return transactions.map(transaction => {
            // 获取资产信息
            const asset = this.assets.find(a => a.id === transaction.asset_id);
            const assetName = asset ? asset.name : '未知资产';
            const assetType = asset ? this.getAssetTypeDisplayName(asset.asset_type || asset.type) : '未知';
            
            // 基础导出数据
            const exportRow = {
                '交易ID': transaction.id,
                '交易日期': transaction.date,
                '资产名称': assetName,
                '资产类型': assetType,
                '交易类型': this.getTransactionTypeText(transaction.type),
                '交易金额': transaction.amount,
                '币种': this.getCurrencyDisplayName(transaction.currency),
                '汇率': transaction.exchange_rate || 1.0,
                '基础货币金额': transaction.amount_base_currency || (transaction.amount * (transaction.exchange_rate || 1.0)),
                '备注': transaction.description || transaction.notes || '',
                '参考号码': transaction.reference_number || '',
                '创建时间': transaction.created_date ? new Date(transaction.created_date).toLocaleString('zh-CN') : '',
                '交易类别': transaction.transaction_class || 'BaseTransaction'
            };
            
            // 添加特定类型的字段
            if (transaction.quantity !== undefined) {
                exportRow['数量'] = transaction.quantity;
            }
            if (transaction.price_per_share !== undefined) {
                exportRow['每股价格'] = transaction.price_per_share;
            }
            if (transaction.commission !== undefined) {
                exportRow['佣金'] = transaction.commission;
            }
            
            // 固定收益特有字段
            if (transaction.annual_rate !== undefined) {
                exportRow['年利率(%)'] = transaction.annual_rate;
            }
            if (transaction.start_date) {
                exportRow['起息日期'] = transaction.start_date;
            }
            if (transaction.maturity_date) {
                exportRow['到期日期'] = transaction.maturity_date;
            }
            if (transaction.interest_type) {
                exportRow['利息类型'] = transaction.interest_type;
            }
            if (transaction.payment_frequency) {
                exportRow['付息频率'] = transaction.payment_frequency;
            }
            if (transaction.face_value !== undefined) {
                exportRow['面值'] = transaction.face_value;
            }
            if (transaction.coupon_rate !== undefined) {
                exportRow['票面利率(%)'] = transaction.coupon_rate;
            }
            
            // 现金类特有字段
            if (transaction.account_type) {
                exportRow['账户类型'] = transaction.account_type;
            }
            if (transaction.interest_rate !== undefined) {
                exportRow['存款利率(%)'] = transaction.interest_rate;
            }
            if (transaction.compound_frequency) {
                exportRow['复利频率'] = transaction.compound_frequency;
            }
            
            // 房产特有字段
            if (transaction.property_area !== undefined) {
                exportRow['物业面积(㎡)'] = transaction.property_area;
            }
            if (transaction.price_per_unit !== undefined) {
                exportRow['单价(元/㎡)'] = transaction.price_per_unit;
            }
            if (transaction.rental_income !== undefined) {
                exportRow['租金收入'] = transaction.rental_income;
            }
            if (transaction.property_type) {
                exportRow['物业类型'] = transaction.property_type;
            }
            if (transaction.location) {
                exportRow['位置'] = transaction.location;
            }
            if (transaction.tax_amount !== undefined) {
                exportRow['税费'] = transaction.tax_amount;
            }
            
            return exportRow;
        });
    }

    generateCSVContent(data) {
        if (data.length === 0) return '';
        
        // 获取表头
        const headers = Object.keys(data[0]);
        
        // 生成CSV内容
        const csvRows = [];
        
        // 添加表头
        csvRows.push(headers.join(','));
        
        // 添加数据行
        data.forEach(row => {
            const values = headers.map(header => {
                const value = row[header];
                // 处理包含逗号、引号或换行符的值
                if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
                    return `"${value.replace(/"/g, '""')}"`;
                }
                return value;
            });
            csvRows.push(values.join(','));
        });
        
        return csvRows.join('\n');
    }

    downloadCSV(csvContent, filename) {
        // 添加BOM以支持中文
        const BOM = '\uFEFF';
        const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
        
        // 创建下载链接
        const link = document.createElement('a');
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        } else {
            // 如果浏览器不支持download属性，使用window.open
            const url = URL.createObjectURL(blob);
            window.open(url);
            URL.revokeObjectURL(url);
        }
    }

    generateFileName() {
        const now = new Date();
        const dateStr = now.toISOString().split('T')[0]; // YYYY-MM-DD
        const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, ''); // HHMMSS
        
        // 添加筛选条件到文件名
        let filterSuffix = '';
        if (this.currentFilters.type) {
            filterSuffix += `_${this.getTransactionTypeText(this.currentFilters.type)}`;
        }
        if (this.currentFilters.asset) {
            const asset = this.assets.find(a => a.id === this.currentFilters.asset);
            if (asset) {
                filterSuffix += `_${asset.name}`;
            }
        }
        if (this.currentFilters.startDate || this.currentFilters.endDate) {
            filterSuffix += '_日期筛选';
        }
        
        return `交易记录_${dateStr}_${timeStr}${filterSuffix}.csv`;
    }

    // 工具方法
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'numeric',
            day: 'numeric'
        });
    }

    getTransactionTypeText(type) {
        const types = {
            'DEPOSIT': '存入',
            'WITHDRAW': '提取',
            'INTEREST': '利息'
        };
        return types[type] || type;
    }

    showSuccessMessage(message) {
        // 创建成功提示
        const notification = document.createElement('div');
        notification.className = 'success-notification';
        notification.textContent = message;
        
        Object.assign(notification.style, {
            position: 'fixed',
            top: '80px',
            right: '20px',
            background: 'var(--success)',
            color: 'white',
            padding: '12px 20px',
            borderRadius: '8px',
            boxShadow: 'var(--shadow-lg)',
            zIndex: '1001',
            fontSize: '14px',
            fontWeight: '500',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    showValidationError(message) {
        // 创建验证错误提示
        const notification = document.createElement('div');
        notification.className = 'validation-error';
        notification.textContent = message;
        
        Object.assign(notification.style, {
            position: 'fixed',
            top: '80px',
            right: '20px',
            background: 'var(--warning)',
            color: 'white',
            padding: '12px 20px',
            borderRadius: '8px',
            boxShadow: 'var(--shadow-lg)',
            zIndex: '1001',
            fontSize: '14px',
            fontWeight: '500',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 2000);
    }
}

// 导出类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TransactionManager;
}

// 全局暴露实例，供模态窗口按钮调用
window.transactionManager = null; 