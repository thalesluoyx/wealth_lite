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

        const addAssetForm = document.getElementById('addAssetForm');
        if (addAssetForm) {
            addAssetForm.addEventListener('submit', (e) => {
                console.log('💾 提交资产表单');
                e.preventDefault();
                this.handleAssetSubmit();
            });
        } else {
            console.warn('⚠️ 未找到addAssetForm元素');
        }

        // 新增资产相关事件
        const createAssetBtn = document.getElementById('createAssetBtn');
        if (createAssetBtn) {
            createAssetBtn.addEventListener('click', () => {
                console.log('🏢 打开新增资产模态窗口');
                this.openAddAssetModal();
            });
        } else {
            console.warn('⚠️ 未找到createAssetBtn元素');
        }

        // 模态窗口关闭事件
        document.getElementById('closeTransactionModal')?.addEventListener('click', () => {
            this.closeAddTransactionModal();
        });

        document.getElementById('cancelTransactionBtn')?.addEventListener('click', () => {
            this.closeAddTransactionModal();
        });

        document.getElementById('closeAssetModal')?.addEventListener('click', () => {
            this.closeAddAssetModal();
        });

        document.getElementById('cancelAssetBtn')?.addEventListener('click', () => {
            this.closeAddAssetModal();
        });

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
        
        const monthlyTransactions = this.transactions.filter(t => {
            const transactionDate = new Date(t.date);
            return transactionDate.getMonth() === currentMonth && 
                   transactionDate.getFullYear() === currentYear;
        });

        const monthlyCount = monthlyTransactions.length;
        const monthlyAmount = monthlyTransactions.reduce((sum, t) => {
            return sum + (t.amount * t.exchangeRate);
        }, 0);
        
        const monthlyReturn = monthlyTransactions
            .filter(t => t.type === 'INTEREST')
            .reduce((sum, t) => sum + (t.amount * t.exchangeRate), 0);

        // 更新UI
        document.getElementById('monthlyTransactionCount').textContent = monthlyCount;
        document.getElementById('monthlyTransactionAmount').textContent = 
            this.app.formatAmount(monthlyAmount);
        document.getElementById('monthlyReturn').textContent = 
            this.app.formatAmount(monthlyReturn);
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
            if (this.currentFilters.asset && transaction.assetId !== parseInt(this.currentFilters.asset)) {
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
            let aValue = a[this.currentSort.field];
            let bValue = b[this.currentSort.field];

            // 特殊处理不同类型的排序
            if (this.currentSort.field === 'date') {
                aValue = new Date(aValue);
                bValue = new Date(bValue);
            } else if (this.currentSort.field === 'amount') {
                aValue = parseFloat(aValue);
                bValue = parseFloat(bValue);
            } else if (typeof aValue === 'string') {
                aValue = aValue.toLowerCase();
                bValue = bValue.toLowerCase();
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
    openWithdrawTransactionModal(assetId) {
        // 设置提取模式
        this.editingTransactionId = null;
        this.isWithdrawMode = true;
        this.lockedAssetId = assetId;
        
        // 设置模态窗口标题
        const modalTitle = document.querySelector('#addTransactionModal .modal-header h3');
        if (modalTitle) {
            modalTitle.textContent = '提取资金';
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

    openAddAssetModal() {
        document.getElementById('addAssetModal').classList.add('show');
    }

    closeAddAssetModal() {
        document.getElementById('addAssetModal').classList.remove('show');
        this.resetAssetForm();
    }

    populateAssetSelect() {
        const select = document.getElementById('assetSelect');
        select.innerHTML = '<option value="">请选择资产...</option>';
        
        this.assets.forEach(asset => {
            const option = document.createElement('option');
            option.value = asset.id;
            option.textContent = asset.name;
            option.dataset.assetType = asset.type; // 添加资产类型数据属性
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
        if (currency === 'CNY') {
            exchangeRateGroup.style.display = 'none';
        } else {
            exchangeRateGroup.style.display = 'block';
            // 设置默认汇率
            const defaultRates = {
                'USD': 7.2,
                'HKD': 0.9,
                'EUR': 7.8
            };
            document.getElementById('exchangeRate').value = defaultRates[currency] || '';
        }
    }

    handleAssetSelectionChange(assetId) {
        console.log('🔄 资产选择变化:', assetId);
        
        const assetTypeDisplay = document.getElementById('assetTypeDisplay');
        const assetTypeValue = document.getElementById('assetTypeValue');
        
        if (!assetId) {
            // 没有选择资产时隐藏资产类型显示
            assetTypeDisplay.style.display = 'none';
            
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
            const assetTypeDisplayName = this.getAssetTypeDisplayName(selectedAsset.type);
            assetTypeValue.textContent = assetTypeDisplayName;
            assetTypeDisplay.style.display = 'block';
            
            console.log('📊 资产类型:', selectedAsset.type, '显示名称:', assetTypeDisplayName);
            
            // 通知固定收益管理器资产类型变化
            if (this.fixedIncomeManager) {
                console.log('📢 通知固定收益管理器: 资产类型变化为', selectedAsset.type);
                this.fixedIncomeManager.handleAssetTypeChange(selectedAsset.type);
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
            'EQUITY': '权益类',
            'ALTERNATIVE': '另类投资',
            'REAL_ESTATE': '不动产'
        };
        return typeMap[assetType] || assetType;
    }

    async handleTransactionSubmit() {
        console.log('🚀 开始处理交易提交...');
        
        try {
            const formData = this.getTransactionFormData();
            console.log('📝 表单数据:', formData);
            
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
            assetType: selectedAsset?.type,
            isFixedIncome: selectedAsset?.type === 'FIXED_INCOME'
        });
        
        return selectedAsset?.type === 'FIXED_INCOME';
    }

    async handleAssetSubmit() {
        const formData = this.getAssetFormData();
        
        if (!this.validateAssetForm(formData)) {
            return;
        }

        try {
            // 调用后端API保存资产
            const newAsset = await this.saveAsset(formData);

            // 保存成功后，重新拉取资产列表，确保下拉框和数据同步
            this.assets = await this.fetchAssets();
            this.populateAssetSelect();
            this.populateAssetFilters();

            // 关闭资产模态窗口
            this.closeAddAssetModal();

            // 自动选择新创建的资产（如果下拉框有该id）
            const assetSelect = document.getElementById('assetSelect');
            if (assetSelect && newAsset.id) {
                assetSelect.value = newAsset.id;
            }

            this.showSuccessMessage('资产已成功创建');
        } catch (error) {
            console.error('创建资产失败:', error);
            this.app.showErrorMessage('创建失败，请稍后重试');
        }
    }

    getTransactionFormData() {
        try {
            // 组装表单数据，字段名与后端保持一致
            // 交易类型直接取下拉框的value（如DEPOSIT、PURCHASE等枚举名）
            const data = {
                asset_id: document.getElementById('assetSelect')?.value || '',
                transaction_type: document.getElementById('transactionType')?.value || '',
                amount: parseFloat(document.getElementById('transactionAmount')?.value || '0'),
                currency: document.getElementById('transactionCurrency')?.value || '',
                transaction_date: document.getElementById('transactionDate')?.value || '',
                exchange_rate: parseFloat(document.getElementById('exchangeRate')?.value || '1.0'),
                notes: document.getElementById('transactionNotes')?.value?.trim() || ''
            };
            
            console.log('📊 获取的表单数据:', data);
            return data;
        } catch (error) {
            console.error('❌ 获取表单数据失败:', error);
            throw new Error('获取表单数据失败: ' + error.message);
        }
    }

    getAssetFormData() {
        return {
            name: document.getElementById('assetName').value.trim(),
            type: document.getElementById('assetType').value,
            currency: document.getElementById('assetCurrency').value,
            description: document.getElementById('assetDescription').value.trim()
        };
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

    validateAssetForm(data) {
        if (!data.name) {
            this.showValidationError('请输入资产名称');
            return false;
        }
        if (!data.type) {
            this.showValidationError('请选择资产类型');
            return false;
        }
        if (!data.currency) {
            this.showValidationError('请选择币种');
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

    async saveAsset(data) {
        try {
            // 调用后端API创建资产
            const response = await fetch('/api/assets', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: data.name,
                    type: data.type,
                    currency: data.currency,
                    description: data.description || '',
                    primary_category: data.primary_category || '',
                    secondary_category: data.secondary_category || ''
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const newAsset = await response.json();
            console.log('✅ 资产创建成功:', newAsset);
            
            return newAsset;
            
        } catch (error) {
            console.error('❌ 保存资产失败:', error);
            throw error;
        }
    }

    resetTransactionForm() {
        document.getElementById('addTransactionForm').reset();
        document.getElementById('exchangeRateGroup').style.display = 'none';
        // 隐藏资产类型显示
        document.getElementById('assetTypeDisplay').style.display = 'none';
        
        // 重置固定收益字段
        if (this.fixedIncomeManager) {
            this.fixedIncomeManager.resetFixedIncomeFields();
        }
    }

    resetAssetForm() {
        document.getElementById('addAssetForm').reset();
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
        document.getElementById('transactionCurrency').value = transaction.currency;
        document.getElementById('transactionDate').value = transaction.date;
        
        // 通知固定收益管理器交易日期变化（编辑模式）
        if (this.fixedIncomeManager) {
            this.fixedIncomeManager.handleTransactionDateChange();
        }
        document.getElementById('transactionNotes').value = transaction.description || transaction.notes || '';
        
        // 显示资产类型
        this.handleAssetSelectionChange(transaction.asset_id);
        
        // 锁定不可编辑的字段
        document.getElementById('assetSelect').disabled = true;
        document.getElementById('transactionType').disabled = true;
        document.getElementById('transactionCurrency').disabled = true;
        
        // 添加锁定样式
        document.getElementById('assetSelect').classList.add('field-locked');
        document.getElementById('transactionType').classList.add('field-locked');
        document.getElementById('transactionCurrency').classList.add('field-locked');
        
        // 处理汇率显示
        this.handleCurrencyChange(transaction.currency);
        if (transaction.currency !== 'CNY') {
            document.getElementById('exchangeRate').value = transaction.exchange_rate || 1.0;
        }
        
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
        // TODO: 实现导出功能
        console.log('导出交易数据');
    }

    // 工具方法
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-CN', {
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