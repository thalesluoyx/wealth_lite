/**
 * 固定收益产品管理器
 * 
 * 职责：
 * - UI管理：创建固定收益特有表单字段、事件绑定、字段显示控制
 * - 计算逻辑：利息计算、日期计算、预览功能
 * - 交易处理：处理存入、利息、提取交易
 * - 工具方法：验证、数据获取、重置等
 * 
 * 设计原则：
 * - 单一职责：统一管理所有固定收益相关功能
 * - 模块化：功能按区域分组
 * - 集成性：与TransactionManager无缝集成
 */

class FixedIncomeManager {
    constructor(transactionManager) {
        this.transactionManager = transactionManager;
        this.isInitialized = false;
        
        // 利息类型枚举
        this.InterestType = {
            SIMPLE: 'SIMPLE',      // 单利
            COMPOUND: 'COMPOUND'   // 复利
        };
        
        // 付息频率枚举
        this.PaymentFrequency = {
            MATURITY: 'MATURITY',   // 到期一次性付息
            ANNUALLY: 'ANNUALLY',   // 年付
            SEMI_ANNUALLY: 'SEMI_ANNUALLY', // 半年付
            QUARTERLY: 'QUARTERLY', // 季付
            MONTHLY: 'MONTHLY'      // 月付
        };
        
        // 提前支取规则
        this.EarlyWithdrawalRules = {
            DEPOSIT: {
                allowEarlyWithdrawal: true,
                penaltyRate: 0.0035, // 活期利率 0.35%
                penaltyType: 'RATE_REDUCTION'
            },
            TREASURY: {
                allowEarlyWithdrawal: true,
                penaltyRate: 0.001, // 0.1% 手续费
                penaltyType: 'FEE'
            }
        };
        
        // UI状态管理
        this.uiState = {
            isFixedIncomeMode: false,
            currentTransactionType: null
        };
        
        this.init();
    }

    // ==================== 初始化 ====================

    init() {
        if (this.isInitialized) return;
        
        try {
            this.createFixedIncomeFields();
            this.bindEvents();
            this.isInitialized = true;
            
            console.log('🏦 固定收益产品管理器初始化完成');
        } catch (error) {
            console.error('❌ 固定收益产品管理器初始化失败:', error);
        }
    }

    // ==================== UI管理 ====================

    /**
     * 创建固定收益产品特有的表单字段
     */
    createFixedIncomeFields() {
        console.log('🔧 开始创建固定收益字段...');
        
        // 检查是否已经存在固定收益字段容器
        let container = document.getElementById('fixedIncomeFieldsContainer');
        console.log('📦 现有容器:', container);
        
        if (!container) {
            console.log('🆕 创建新的固定收益字段容器');
            container = this.createFieldsContainer();
        }

        // 创建各个字段组（支持外汇定期存款）
        this.createAnnualRateField(container);
        this.createDateFields(container);
        this.createTermField(container);
        this.createInterestTypeField(container);
        this.createPaymentFrequencyField(container);
        this.createInterestCalculator(container);
        this.createExchangeRatePreview();
        
        // 确保初始状态下字段是隐藏的且没有required属性
        this.hideFixedIncomeFields();
        console.log('✅ 固定收益字段创建完成');
    }

    createFieldsContainer() {
        console.log('🔧 开始创建固定收益字段容器...');
        
        const container = document.createElement('div');
        container.id = 'fixedIncomeFieldsContainer';
        container.className = 'fixed-income-fields';
        container.style.display = 'none';

        // 插入到交易表单中的合适位置（备注字段之前）
        const transactionForm = document.getElementById('addTransactionForm');
        
        // 使用更兼容的方法查找备注字段组
        let notesGroup = null;
        if (transactionForm) {
            const formGroups = transactionForm.querySelectorAll('.form-group');
            for (let group of formGroups) {
                if (group.querySelector('#transactionNotes')) {
                    notesGroup = group;
                    break;
                }
            }
        }
        
        console.log('📝 交易表单:', transactionForm);
        console.log('📝 备注字段组:', notesGroup);
        
        if (transactionForm && notesGroup) {
            transactionForm.insertBefore(container, notesGroup);
            console.log('✅ 固定收益字段容器已插入到表单中');
        } else {
            console.warn('⚠️ 无法找到合适的位置插入固定收益字段容器');
            // 作为备用方案，直接添加到表单末尾
            if (transactionForm) {
                transactionForm.appendChild(container);
                console.log('📝 作为备用方案，容器已添加到表单末尾');
            }
        }

        return container;
    }

    createExchangeRatePreviewContainer() {
        console.log('🔧 开始创建汇率预览容器...');
        
        // 创建汇率预览容器
        const exchangeContainer = document.createElement('div');
        exchangeContainer.id = 'exchangeRatePreviewContainer';
        exchangeContainer.style.display = 'none';

        // 插入到汇率字段之后、交易日期之前
        const transactionForm = document.getElementById('addTransactionForm');
        const exchangeRateGroup = document.getElementById('exchangeRateGroup');
        
        // 查找交易日期字段组
        let transactionDateGroup = null;
        if (transactionForm) {
            const formGroups = transactionForm.querySelectorAll('.form-group');
            for (let group of formGroups) {
                if (group.querySelector('#transactionDate')) {
                    transactionDateGroup = group;
                    break;
                }
            }
        }
        
        console.log('📝 汇率字段组:', exchangeRateGroup);
        console.log('📝 交易日期字段组:', transactionDateGroup);
        
        if (transactionForm && transactionDateGroup) {
            transactionForm.insertBefore(exchangeContainer, transactionDateGroup);
            console.log('✅ 汇率预览容器已插入到表单中（交易日期之前）');
        } else {
            console.warn('⚠️ 无法找到合适的位置插入汇率预览容器');
        }

        return exchangeContainer;
    }

    createAnnualRateField(container) {
        const fieldGroup = document.createElement('div');
        fieldGroup.className = 'form-group';
        fieldGroup.id = 'annualRateGroup';
        fieldGroup.innerHTML = `
            <label for="annualRate" class="form-label">年利率<span class="required">*</span></label>
            <div class="input-group">
                <input type="number" 
                       id="annualRate" 
                       name="annual_rate" 
                       step="0.01" 
                       min="0" 
                       max="50" 
                       placeholder="请输入年利率"
                       class="form-input">
                <span class="input-suffix">%</span>
            </div>
            <small class="form-help">请输入年化利率，如3.5表示3.5%</small>
        `;
        container.appendChild(fieldGroup);
    }

    createDateFields(container) {
        // 起息日期
        const startDateGroup = document.createElement('div');
        startDateGroup.className = 'form-group';
        startDateGroup.id = 'startDateGroup';
        startDateGroup.innerHTML = `
            <label for="fiStartDate" class="form-label">起息日期<span class="required">*</span></label>
            <input type="date" 
                   id="fiStartDate" 
                   name="start_date" 
                   class="form-input">
            <small class="form-help">产品开始计息的日期</small>
        `;
        container.appendChild(startDateGroup);

        // 到期日期
        const maturityDateGroup = document.createElement('div');
        maturityDateGroup.className = 'form-group';
        maturityDateGroup.id = 'maturityDateGroup';
        maturityDateGroup.innerHTML = `
            <label for="maturityDate" class="form-label">到期日期<span class="required">*</span></label>
            <input type="date" 
                   id="maturityDate" 
                   name="maturity_date" 
                   class="form-input">
            <small class="form-help">产品到期日期，可根据存款期限自动计算</small>
        `;
        container.appendChild(maturityDateGroup);
    }

    createTermField(container) {
        const termGroup = document.createElement('div');
        termGroup.className = 'form-group';
        termGroup.id = 'depositTermGroup';
        termGroup.innerHTML = `
            <label for="depositTerm" class="form-label">存款期限</label>
            <select id="depositTerm" name="deposit_term" class="form-select">
                <option value="">请选择期限</option>
                <option value="1">1个月</option>
                <option value="3">3个月</option>
                <option value="6">6个月</option>
                <option value="12">1年</option>
                <option value="24">2年</option>
                <option value="36">3年</option>
                <option value="60">5年</option>
            </select>
            <small class="form-help">选择后将自动计算到期日期</small>
        `;
        container.appendChild(termGroup);
    }

    createInterestTypeField(container) {
        const interestTypeGroup = document.createElement('div');
        interestTypeGroup.className = 'form-group';
        interestTypeGroup.id = 'interestTypeGroup';
        interestTypeGroup.innerHTML = `
            <label for="interestType" class="form-label">利息类型</label>
            <select id="interestType" name="interest_type" class="form-select">
                <option value="SIMPLE">单利</option>
                <option value="COMPOUND">复利</option>
            </select>
            <small class="form-help">选择利息计算方式</small>
        `;
        container.appendChild(interestTypeGroup);
    }

    createPaymentFrequencyField(container) {
        const frequencyGroup = document.createElement('div');
        frequencyGroup.className = 'form-group';
        frequencyGroup.id = 'paymentFrequencyGroup';
        frequencyGroup.innerHTML = `
            <label for="paymentFrequency" class="form-label">付息频率</label>
            <select id="paymentFrequency" name="payment_frequency" class="form-select">
                <option value="MATURITY">到期一次性付息</option>
                <option value="ANNUALLY">年付</option>
                <option value="SEMI_ANNUALLY">半年付</option>
                <option value="QUARTERLY">季付</option>
                <option value="MONTHLY">月付</option>
            </select>
            <small class="form-help">选择利息支付频率</small>
        `;
        container.appendChild(frequencyGroup);
    }

    createInterestCalculator(container) {
        const calculatorGroup = document.createElement('div');
        calculatorGroup.className = 'form-group';
        calculatorGroup.id = 'interestCalculatorGroup';
        calculatorGroup.innerHTML = `
            <div id="interestPreview" class="interest-preview" style="display: none;">
                <!-- 利息预览内容将通过JavaScript动态填充 -->
            </div>
        `;
        container.appendChild(calculatorGroup);
    }

    createExchangeRatePreview() {
        // 创建或获取汇率预览容器
        let exchangeContainer = document.getElementById('exchangeRatePreviewContainer');
        if (!exchangeContainer) {
            exchangeContainer = this.createExchangeRatePreviewContainer();
        }

        const exchangeGroup = document.createElement('div');
        exchangeGroup.className = 'form-group';
        exchangeGroup.id = 'exchangeRatePreviewGroup';
        exchangeGroup.style.display = 'none';
        exchangeGroup.innerHTML = `
            <div class="exchange-rate-preview">
                <label class="form-label">汇率信息</label>
                <div class="exchange-info">
                    <div class="exchange-row">
                        <span class="exchange-label">外币金额：</span>
                        <span id="foreignCurrencyAmount" class="exchange-value">-</span>
                    </div>
                    <div class="exchange-row">
                        <span class="exchange-label">当前汇率：</span>
                        <span id="currentExchangeRate" class="exchange-value">-</span>
                    </div>
                    <div class="exchange-row highlight">
                        <span class="exchange-label">人民币等值：</span>
                        <span id="cnyEquivalent" class="exchange-value">¥0.00</span>
                    </div>
                </div>
            </div>
        `;
        exchangeContainer.appendChild(exchangeGroup);
    }

    // ==================== 事件绑定 ====================

    bindEvents() {
        try {
            // 注意：不要直接绑定全局元素（assetSelect, transactionType）的事件
            // 这些事件由TransactionManager处理，然后调用相应的方法
            
            // 注意：交易日期变化事件由TransactionManager统一处理，会调用handleTransactionDateChange方法
            
            // 存款期限变化自动计算到期日
            document.getElementById('depositTerm')?.addEventListener('change', () => {
                this.calculateMaturityDate();
            });

            // 起息日期变化重新计算到期日
            document.getElementById('fiStartDate')?.addEventListener('change', () => {
                // 标记用户已手动设置起息日期
                const startDateField = document.getElementById('fiStartDate');
                if (startDateField && startDateField.value) {
                    startDateField.setAttribute('data-user-set', 'true');
                }
                this.calculateMaturityDate();
            });

            // 字段变化时计算利息预览
            ['annualRate', 'fiStartDate', 'maturityDate', 'interestType'].forEach(fieldId => {
                document.getElementById(fieldId)?.addEventListener('input', () => {
                    this.calculateInterestPreview();
                });
                document.getElementById(fieldId)?.addEventListener('change', () => {
                    this.calculateInterestPreview();
                });
            });

            // 监听金额和汇率变化，实时更新人民币等值
            document.getElementById('transactionAmount')?.addEventListener('input', () => {
                this.updateExchangeRatePreview();
            });
            document.getElementById('exchangeRate')?.addEventListener('input', () => {
                this.updateExchangeRatePreview();
            });
            document.getElementById('transactionCurrency')?.addEventListener('change', () => {
                this.handleCurrencyChangeForFixedIncome();
            });

            // 实时验证
            ['annualRate', 'fiStartDate', 'maturityDate'].forEach(fieldId => {
                const field = document.getElementById(fieldId);
                if (field) {
                    field.addEventListener('blur', () => this.validateFieldRealTime(field));
                    field.addEventListener('input', () => this.clearFieldError(field));
                }
            });

            console.log('🔗 固定收益字段事件绑定完成');
        } catch (error) {
            console.error('❌ 固定收益字段事件绑定失败:', error);
        }
    }

    // ==================== 状态管理 ====================

    /**
     * 处理交易日期变化，自动同步起息日期
     */
    handleTransactionDateChange() {
        console.log('🎯 handleTransactionDateChange 被调用');
        
        // 只在固定收益模式下处理
        if (!this.uiState.isFixedIncomeMode) {
            console.log('⏭️ 跳过：不是固定收益模式, isFixedIncomeMode:', this.uiState.isFixedIncomeMode);
            return;
        }
        
        const transactionDateField = document.getElementById('transactionDate');
        const startDateField = document.getElementById('fiStartDate');
        
        console.log('🔍 元素检查:', {
            transactionDateField: !!transactionDateField,
            startDateField: !!startDateField,
            transactionDate: transactionDateField?.value,
            startDate: startDateField?.value,
            hasUserSetAttr: startDateField?.hasAttribute('data-user-set')
        });
        
        if (!transactionDateField || !startDateField) {
            console.log('⏭️ 跳过：必要元素不存在');
            return;
        }
        
        const transactionDate = transactionDateField.value;
        
        // 如果交易日期有值，且起息日期为空或者用户未手动设置过起息日期
        if (transactionDate && 
            (!startDateField.value || !startDateField.hasAttribute('data-user-set'))) {
            
            console.log('📅 交易日期变化，自动更新起息日期:', transactionDate);
            startDateField.value = transactionDate;
            
            // 重新计算到期日期和利息预览
            this.calculateMaturityDate();
            this.calculateInterestPreview();
        } else {
            console.log('⏭️ 跳过自动设置，原因:', {
                hasTransactionDate: !!transactionDate,
                hasStartDate: !!startDateField.value,
                userHasSet: startDateField.hasAttribute('data-user-set')
            });
        }
    }

    handleAssetTypeChange(assetType) {
        console.log('🏦 FixedIncomeManager: 收到资产类型变化通知:', assetType);
        console.log('🔍 当前起息日期值:', document.getElementById('fiStartDate')?.value);
        
        if (assetType === 'FIXED_INCOME') {
            console.log('✅ 显示固定收益字段');
            this.showFixedIncomeFields();
        } else {
            console.log('❌ 隐藏固定收益字段');
            this.hideFixedIncomeFields();
        }
        
        console.log('🔍 处理后起息日期值:', document.getElementById('fiStartDate')?.value);
    }

    handleTransactionTypeChange(transaction_type) {
        this.uiState.currentTransactionType = transaction_type;
        this.adjustFieldsForTransactionType(transaction_type);
    }

    adjustFieldsForTransactionType(transaction_type) {
        const container = document.getElementById('fixedIncomeFieldsContainer');
        if (!container || !this.uiState.isFixedIncomeMode) return;

        console.log('🔧 根据交易类型调整字段显示:', transaction_type);

        // 根据交易类型调整字段显示
        switch (transaction_type) {
            case 'DEPOSIT':
                // 存入交易显示所有字段
                console.log('📋 显示所有固定收益字段 (存入交易)');
                this.showAllFixedIncomeFields();
                this.showCurrencyAndExchangeRateFields();
                break;
            case 'INTEREST':
                // 利息交易完全隐藏固定收益字段，实现极简化界面
                console.log('📋 隐藏所有固定收益字段 (利息交易 - 极简模式)');
                this.hideAllFixedIncomeFields();
                this.hideCurrencyAndExchangeRateFields();
                break;
            case 'WITHDRAW':
                // 提取交易隐藏所有固定收益字段，只保留基本交易字段
                console.log('📋 隐藏所有固定收益字段 (提取交易 - 极简模式)');
                this.hideAllFixedIncomeFields();
                this.showCurrencyAndExchangeRateFields();
                break;
            default:
                // 默认情况（包括null或空值）显示所有字段
                console.log('📋 显示所有固定收益字段 (默认)');
                this.showAllFixedIncomeFields();
                this.showCurrencyAndExchangeRateFields();
        }
    }

    showFixedIncomeFields() {
        console.log('🏦 开始显示固定收益字段...');
        this.uiState.isFixedIncomeMode = true;
        const container = document.getElementById('fixedIncomeFieldsContainer');
        console.log('📦 固定收益字段容器:', container);
        
        if (container) {
            container.style.display = 'block';
            console.log('✅ 容器显示状态已设置为 block');
            
            // 获取当前交易类型
            const transactionTypeSelect = document.getElementById('transactionType');
            const currentTransactionType = transactionTypeSelect ? transactionTypeSelect.value : null;
            console.log('🔍 当前交易类型:', currentTransactionType);
            
            // 更新状态并调整字段显示
            if (currentTransactionType) {
                this.uiState.currentTransactionType = currentTransactionType;
            }
            this.adjustFieldsForTransactionType(this.uiState.currentTransactionType);
            
            // 设置必填字段的required属性
            this.setFixedIncomeFieldsRequired(true);
            
            // 自动同步交易日期到起息日期
            this.handleTransactionDateChange();
            
            console.log('✅ 固定收益字段显示完成');
        } else {
            console.error('❌ 固定收益字段容器未找到');
        }
    }

    hideFixedIncomeFields() {
        console.log('🏦 开始隐藏固定收益字段...');
        this.uiState.isFixedIncomeMode = false;
        const container = document.getElementById('fixedIncomeFieldsContainer');
        console.log('📦 固定收益字段容器:', container);
        
        if (container) {
            container.style.display = 'none';
            console.log('✅ 容器显示状态已设置为 none');
            
            // 移除必填字段的required属性，避免表单验证冲突
            this.setFixedIncomeFieldsRequired(false);
            console.log('✅ 固定收益字段隐藏完成');
        } else {
            console.error('❌ 固定收益字段容器未找到');
        }
    }

    /**
     * 设置固定收益字段的required属性
     * @param {boolean} isRequired - 是否设置为必填
     */
    setFixedIncomeFieldsRequired(isRequired) {
        // 根据当前交易类型决定哪些字段需要设为必填
        const currentTransactionType = this.uiState.currentTransactionType;
        
        if (currentTransactionType === 'INTEREST') {
            // 利息交易不需要设置固定收益字段为必填
            console.log('✅ 利息交易模式：跳过固定收益字段必填设置');
            return;
        }

        // 非利息交易才设置固定收益字段为必填
        const requiredFields = ['annualRate', 'fiStartDate', 'maturityDate'];
        requiredFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                if (isRequired) {
                    field.setAttribute('required', '');
                } else {
                    field.removeAttribute('required');
                }
            }
        });
        
        console.log(`✅ 固定收益字段必填状态已设置为: ${isRequired}`);
    }

    showAllFixedIncomeFields() {
        const fieldIds = ['annualRateGroup', 'startDateGroup', 'maturityDateGroup', 
                         'depositTermGroup', 'interestTypeGroup', 'paymentFrequencyGroup'];
        fieldIds.forEach(id => {
            const field = document.getElementById(id);
            if (field) field.style.display = 'block';
        });
        
        // 🔧 恢复必填字段的required属性
        const requiredFieldIds = ['annualRate', 'fiStartDate', 'maturityDate'];
        requiredFieldIds.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.setAttribute('required', '');
                //console.log(`✅ 恢复字段 ${fieldId} 的required属性`);
            }
        });
    }

    showBasicFixedIncomeFields() {
        // 首先显示基本字段（年利率、起息日期、到期日期）
        const showFields = ['annualRateGroup', 'startDateGroup', 'maturityDateGroup'];
        showFields.forEach(id => {
            const field = document.getElementById(id);
            if (field) field.style.display = 'block';
        });
        
        // 然后隐藏复杂字段
        const hideFields = ['depositTermGroup', 'interestTypeGroup', 'paymentFrequencyGroup'];
        hideFields.forEach(id => {
            const field = document.getElementById(id);
            if (field) field.style.display = 'none';
        });
        
        // 🔧 恢复基本字段的required属性
        const requiredFieldIds = ['annualRate', 'fiStartDate', 'maturityDate'];
        requiredFieldIds.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.setAttribute('required', '');
                //console.log(`✅ 恢复基本字段 ${fieldId} 的required属性`);
            }
        });
    }

    /**
     * 利息交易专用：隐藏所有固定收益字段，实现极简化界面
     */
    hideAllFixedIncomeFields() {
        const fieldIds = ['annualRateGroup', 'startDateGroup', 'maturityDateGroup', 
                         'depositTermGroup', 'interestTypeGroup', 'paymentFrequencyGroup'];
        fieldIds.forEach(id => {
            const field = document.getElementById(id);
            if (field) field.style.display = 'none';
        });
        
        // 🔧 关键修复：移除隐藏字段的required属性，避免表单验证错误
        const requiredFieldIds = ['annualRate', 'fiStartDate', 'maturityDate'];
        requiredFieldIds.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.removeAttribute('required');
                //console.log(`✅ 移除字段 ${fieldId} 的required属性`);
            }
        });
        
        //console.log('✅ 已隐藏所有固定收益字段 (利息交易极简模式)');
    }

    /**
     * 隐藏币种和汇率字段（利息交易专用）
     */
    hideCurrencyAndExchangeRateFields() {
        // 隐藏币种选择字段 - 使用更准确的选择器
        const currencyField = document.getElementById('transactionCurrency');
        const currencyGroup = currencyField?.closest('.form-group');
        if (currencyGroup) {
            currencyGroup.style.display = 'none';
            console.log('✅ 已隐藏币种字段');
        } else {
            console.warn('⚠️ 未找到币种字段组');
        }

        // 隐藏汇率字段
        const exchangeRateGroup = document.getElementById('exchangeRateGroup');
        if (exchangeRateGroup) {
            exchangeRateGroup.style.display = 'none';
            console.log('✅ 已隐藏汇率字段');
        } else {
            console.warn('⚠️ 未找到汇率字段组');
        }
    }

    /**
     * 显示币种和汇率字段（非利息交易使用）
     */
    showCurrencyAndExchangeRateFields() {
        // 显示币种选择字段
        const currencyField = document.getElementById('transactionCurrency');
        const currencyGroup = currencyField?.closest('.form-group');
        if (currencyGroup) {
            currencyGroup.style.display = 'block';
            console.log('✅ 已显示币种字段');
        } else {
            console.warn('⚠️ 未找到币种字段组');
        }

        // 汇率字段的显示由币种变化事件控制，这里不强制显示
        console.log('✅ 币种字段已恢复显示');
    }

    // ==================== 计算逻辑 ====================

    calculateMaturityDate() {
        try {
            const termSelect = document.getElementById('depositTerm');
            const startDateInput = document.getElementById('fiStartDate');
            const maturityDateInput = document.getElementById('maturityDate');

            if (!termSelect?.value || !startDateInput?.value) return;

            const startDate = new Date(startDateInput.value);
            const termMonths = parseInt(termSelect.value);
            
            // 计算到期日期
            const maturityDate = new Date(startDate);
            maturityDate.setMonth(maturityDate.getMonth() + termMonths);
            
            // 设置到期日期
            maturityDateInput.value = maturityDate.toISOString().split('T')[0];
            
            // 触发利息预览计算
            this.calculateInterestPreview();
            
        } catch (error) {
            console.error('到期日期计算失败:', error);
        }
    }

    /**
     * 计算利息
     * @param {Object} params - 计算参数
     * @param {number} params.principal - 本金
     * @param {number} params.annualRate - 年利率(百分比)
     * @param {Date} params.startDate - 起息日期
     * @param {Date} params.endDate - 到期日期
     * @param {string} params.interestType - 利息类型
     * @returns {Object} 计算结果
     */
    calculateInterest(params) {
        const { principal, annualRate, startDate, endDate, interestType = 'SIMPLE' } = params;
        
        if (!principal || !annualRate || !startDate || !endDate) {
            throw new Error('计算参数不完整');
        }

        const rate = annualRate / 100; // 转换为小数
        const days = this.calculateDaysBetween(startDate, endDate);
        const years = days / 365;

        let totalInterest;
        
        if (interestType === 'COMPOUND') {
            // 复利计算: A = P(1 + r)^t
            const totalAmount = principal * Math.pow(1 + rate, years);
            totalInterest = totalAmount - principal;
        } else {
            // 单利计算: I = P * r * t
            totalInterest = principal * rate * years;
        }

        return {
            principal: principal,
            totalInterest: Math.round(totalInterest * 100) / 100,
            totalAmount: Math.round((principal + totalInterest) * 100) / 100,
            holdingDays: days,
            annualRate: annualRate,
            interestType: interestType
        };
    }

    calculateDaysBetween(startDate, endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        const timeDiff = end.getTime() - start.getTime();
        return Math.ceil(timeDiff / (1000 * 3600 * 24));
    }

    /**
     * 计算两个日期之间的月份差
     * @param {Date} startDate - 开始日期
     * @param {Date} endDate - 结束日期
     * @returns {number} 月份差
     */
    calculateMonthsBetween(startDate, endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        let months = (end.getFullYear() - start.getFullYear()) * 12;
        months += end.getMonth() - start.getMonth();
        
        // 如果结束日期的日数小于开始日期的日数，说明不满一个月
        if (end.getDate() < start.getDate()) {
            months--;
        }
        
        return months;
    }

    calculateInterestPreview() {
        try {
            // 获取当前表单数据
            const amount = parseFloat(document.getElementById('transactionAmount')?.value);
            const annualRate = parseFloat(document.getElementById('annualRate')?.value);
            const startDate = document.getElementById('fiStartDate')?.value;
            const maturityDate = document.getElementById('maturityDate')?.value;
            const interestType = document.getElementById('interestType')?.value || 'SIMPLE';

            if (!amount || !annualRate || !startDate || !maturityDate) {
                // 隐藏预览
                const previewSection = document.getElementById('interestPreview');
                if (previewSection) previewSection.style.display = 'none';
                return;
            }

            const result = this.calculateInterest({
                principal: amount,
                annualRate: annualRate,
                startDate: new Date(startDate),
                endDate: new Date(maturityDate),
                interestType: interestType
            });

            this.displayInterestPreview(result);

        } catch (error) {
            console.error('利息预览计算失败:', error);
            // 不显示错误给用户，只是隐藏预览
            const previewSection = document.getElementById('interestPreview');
            if (previewSection) previewSection.style.display = 'none';
        }
    }

    displayInterestPreview(result) {
        const previewSection = document.getElementById('interestPreview');
        if (!previewSection) return;

        previewSection.innerHTML = `
            <div class="interest-preview-content">
                <h4>利息计算预览</h4>
                <div class="preview-grid">
                    <div class="preview-item">
                        <label>本金:</label>
                        <span>¥${result.principal.toLocaleString()}</span>
                    </div>
                    <div class="preview-item">
                        <label>预期利息:</label>
                        <span>¥${result.totalInterest.toLocaleString()}</span>
                    </div>
                    <div class="preview-item">
                        <label>到期总额:</label>
                        <span>¥${result.totalAmount.toLocaleString()}</span>
                    </div>
                    <div class="preview-item">
                        <label>持有天数:</label>
                        <span>${result.holdingDays}天</span>
                    </div>
                </div>
            </div>
        `;

        previewSection.style.display = 'block';
    }

    // ==================== 交易处理 ====================

    /**
     * 处理固定收益产品交易提交
     */
    async handleFixedIncomeTransaction(formData) {
        try {
            // 验证固定收益产品参数
            const validationResult = this.validateFixedIncomeTransaction(formData);
            if (!validationResult.isValid) {
                throw new Error(validationResult.errors.join(', '));
            }

            // 根据交易类型处理
            switch (formData.transaction_type) {
                case 'DEPOSIT':
                    return await this.handleDepositTransaction(formData);
                case 'INTEREST':
                    return await this.handleInterestTransaction(formData);
                case 'WITHDRAW':
                    return await this.handleWithdrawalTransaction(formData);
                default:
                    throw new Error('不支持的交易类型');
            }
        } catch (error) {
            console.error('固定收益交易处理失败:', error);
            throw error;
        }
    }

    async handleDepositTransaction(formData) {
        // 构建固定收益交易数据
        const transactionData = {
            ...formData,
            transaction_type: 'DEPOSIT',
            annual_rate: parseFloat(formData.annual_rate),
            start_date: formData.start_date,
            maturity_date: formData.maturity_date,
            interest_type: formData.interest_type || 'SIMPLE',
            payment_frequency: formData.payment_frequency || 'MATURITY',
            face_value: parseFloat(formData.amount),
            coupon_rate: parseFloat(formData.annual_rate)
        };

        // 只在新增交易时计算预期收益并添加到备注，编辑时不添加
        if (!this.transactionManager.editingTransactionId && 
            formData.annual_rate && formData.start_date && formData.maturity_date) {
            try {
                const interestInfo = this.calculateInterest({
                    principal: parseFloat(formData.amount),
                    annualRate: parseFloat(formData.annual_rate),
                    startDate: new Date(formData.start_date),
                    endDate: new Date(formData.maturity_date),
                    interestType: formData.interest_type || 'SIMPLE'
                });

                const originalNotes = formData.notes || '';
                const interestNote = `预期收益: ¥${interestInfo.totalInterest.toFixed(2)}, 到期总额: ¥${interestInfo.totalAmount.toFixed(2)}`;
                transactionData.notes = originalNotes ? `${originalNotes}\n${interestNote}` : interestNote;
                console.log('💰 新增交易，自动添加预期收益信息到备注');
            } catch (error) {
                console.warn('预期收益计算失败:', error);
            }
        } else if (this.transactionManager.editingTransactionId) {
            console.log('✏️ 编辑交易，保持原有备注不变');
        }

        // 检查是否为编辑模式
        if (this.transactionManager.editingTransactionId) {
            return await this.updateTransaction(this.transactionManager.editingTransactionId, transactionData);
        } else {
            return await this.transactionManager.saveTransaction(transactionData);
        }
    }

    async handleInterestTransaction(formData) {
        console.log('🏦 处理利息交易，开始自动获取资产信息...');
        
        try {
            // 获取资产信息以自动填充币种和汇率
            const assetInfo = await this.getAssetInfo(formData.asset_id);
            if (!assetInfo) {
                throw new Error('无法获取资产信息，请确认资产是否存在');
            }

            console.log('📊 获取到资产信息:', assetInfo);

            // 构建利息交易数据，自动使用资产的币种和汇率
            const transactionData = {
                asset_id: formData.asset_id,
                transaction_type: 'INTEREST',
                amount: parseFloat(formData.amount),
                transaction_date: formData.transaction_date,
                currency: assetInfo.currency,  // 自动使用资产币种
                exchange_rate: await this.getExchangeRate(assetInfo.currency),  // 自动获取汇率
                notes: formData.notes || ''
            };

            console.log('💰 构建的利息交易数据:', transactionData);

            // 只在新增交易时添加利息交易的备注信息，编辑时不添加
            if (!this.transactionManager.editingTransactionId) {
                const originalNotes = transactionData.notes;
                const interestNote = `利息收入 - 自动使用资产币种: ${assetInfo.currency}`;
                transactionData.notes = originalNotes ? `${originalNotes}\n${interestNote}` : interestNote;
                console.log('💰 新增利息交易，自动添加币种信息到备注');
            } else {
                console.log('✏️ 编辑利息交易，保持原有备注不变');
            }

            // 检查是否为编辑模式
            if (this.transactionManager.editingTransactionId) {
                return await this.updateTransaction(this.transactionManager.editingTransactionId, transactionData);
            } else {
                return await this.transactionManager.saveTransaction(transactionData);
            }

        } catch (error) {
            console.error('❌ 利息交易处理失败:', error);
            throw error;
        }
    }

    /**
     * 获取资产信息
     * @param {string} assetId - 资产ID
     * @returns {Object|null} 资产信息
     */
    async getAssetInfo(assetId) {
        try {
            // 从TransactionManager的资产列表中查找
            const assets = this.transactionManager.assets || [];
            const asset = assets.find(a => a.id === assetId);
            
            if (asset) {
                console.log('✅ 从缓存中找到资产信息:', asset);
                return {
                    id: asset.id,
                    name: asset.asset_name,
                    currency: asset.currency || 'CNY',
                    asset_type: asset.asset_type
                };
            }

            // 如果缓存中没有，尝试从API获取
            console.log('📡 从API获取资产信息...');
            const response = await fetch(`/api/assets/${assetId}`);
            if (response.ok) {
                const assetData = await response.json();
                console.log('✅ 从API获取到资产信息:', assetData);
                return {
                    id: assetData.id,
                    name: assetData.asset_name,
                    currency: assetData.currency || 'CNY',
                    asset_type: assetData.asset_type
                };
            }

            console.warn('⚠️ 无法从API获取资产信息');
            return null;

        } catch (error) {
            console.error('❌ 获取资产信息失败:', error);
            return null;
        }
    }

    /**
     * 获取汇率
     * @param {string} currency - 币种
     * @returns {number} 汇率
     */
    async getExchangeRate(currency) {
        // 如果是基础货币（人民币），汇率为1
        if (currency === 'CNY') {
            return 1.0;
        }

        try {
            // 尝试从系统配置或缓存中获取汇率
            const defaultRates = {
                'USD': 7.2,
                'HKD': 0.9,
                'EUR': 7.8,
                'GBP': 9.1,
                'JPY': 0.05
            };

            const rate = defaultRates[currency] || 1.0;
            console.log(`💱 使用汇率: 1 ${currency} = ${rate} CNY`);
            return rate;

        } catch (error) {
            console.error('❌ 获取汇率失败，使用默认汇率1.0:', error);
            return 1.0;
        }
    }

    async handleWithdrawalTransaction(formData) {
        const transactionData = {
            ...formData,
            transaction_type: 'WITHDRAW'
        };

        // 检查是否为编辑模式
        if (this.transactionManager.editingTransactionId) {
            return await this.updateTransaction(this.transactionManager.editingTransactionId, transactionData);
        } else {
            return await this.transactionManager.saveTransaction(transactionData);
        }
    }

    /**
     * 更新现有交易记录
     * @param {string} transactionId - 交易ID
     * @param {Object} transactionData - 交易数据
     * @returns {Promise} API响应
     */
    async updateTransaction(transactionId, transactionData) {
        try {
            console.log('✏️ 更新固定收益交易, ID:', transactionId, '数据:', transactionData);
            
            const response = await fetch(`/api/transactions/${transactionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(transactionData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('✅ 固定收益交易更新成功:', result);
            return result;

        } catch (error) {
            console.error('❌ 更新固定收益交易失败:', error);
            throw error;
        }
    }

    // ==================== 验证逻辑 ====================

    validateFixedIncomeTransaction(formData) {
        const errors = [];

        // 基础验证（所有交易类型都需要）
        if (!formData.asset_id) {
            errors.push('请选择资产');
        }

        if (!formData.amount || parseFloat(formData.amount) <= 0) {
            errors.push('交易金额必须大于0');
        }

        if (!formData.transaction_date) {
            errors.push('交易日期不能为空');
        }

        // 根据交易类型进行特殊验证
        switch (formData.transaction_type) {
            case 'DEPOSIT':
                // 存入交易的完整验证
                if (!formData.annual_rate || parseFloat(formData.annual_rate) <= 0) {
                    errors.push('年利率必须大于0');
                }

                if (formData.annual_rate && parseFloat(formData.annual_rate) > 50) {
                    errors.push('年利率不能超过50%');
                }

                if (!formData.start_date) {
                    errors.push('起息日期不能为空');
                }

                if (!formData.maturity_date) {
                    errors.push('到期日期不能为空');
                }

                if (formData.start_date && formData.maturity_date && 
                    new Date(formData.maturity_date) <= new Date(formData.start_date)) {
                    errors.push('到期日期必须晚于起息日期');
                }

                // 日期合理性验证
                if (formData.start_date && new Date(formData.start_date) > new Date()) {
                    const today = new Date().toISOString().split('T')[0];
                    if (formData.start_date > today) {
                        errors.push('起息日期不能晚于今天');
                    }
                }
                break;

            case 'INTEREST':
                // 利息交易的简化验证 - 只验证基本字段
                console.log('✅ 利息交易使用简化验证逻辑');
                // 已经在上面进行了基础验证，利息交易不需要额外验证
                break;

            case 'WITHDRAW':
                // 提取交易的验证
                // 目前只需要基础验证
                break;

            default:
                errors.push('不支持的交易类型');
        }

        console.log('🔍 验证结果:', {
            transactionType: formData.transaction_type,
            isValid: errors.length === 0,
            errors: errors
        });

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    validateFieldRealTime(field) {
        if (!field) return;

        const fieldGroup = field.closest('.form-group');
        if (!fieldGroup) return;

        // 清除之前的错误状态
        this.clearFieldError(field);

        // 基础验证
        if (field.required && !field.value.trim()) {
            this.showFieldError(fieldGroup, '此字段为必填项');
            return;
        }

        // 字段特定验证
        switch (field.id) {
            case 'annualRate':
                const rate = parseFloat(field.value);
                if (field.value && (isNaN(rate) || rate <= 0)) {
                    this.showFieldError(fieldGroup, '年利率必须大于0');
                } else if (field.value && rate > 50) {
                    this.showFieldError(fieldGroup, '年利率不能超过50%');
                }
                break;
            
            case 'fiStartDate':
                if (field.value) {
                    const maturityDate = document.getElementById('maturityDate')?.value;
                    if (maturityDate && new Date(field.value) >= new Date(maturityDate)) {
                        this.showFieldError(fieldGroup, '起息日期必须早于到期日期');
                    }
                }
                break;
            
            case 'maturityDate':
                if (field.value) {
                    const startDate = document.getElementById('fiStartDate')?.value;
                    if (startDate && new Date(field.value) <= new Date(startDate)) {
                        this.showFieldError(fieldGroup, '到期日期必须晚于起息日期');
                    }
                }
                break;
        }
    }

    clearFieldError(field) {
        const fieldGroup = field.closest('.form-group');
        if (fieldGroup) {
            fieldGroup.classList.remove('has-error');
            const existingError = fieldGroup.querySelector('.field-error');
            if (existingError) existingError.remove();
        }
    }

    showFieldError(fieldGroup, message) {
        fieldGroup.classList.add('has-error');
        
        // 移除已存在的错误信息
        const existingError = fieldGroup.querySelector('.field-error');
        if (existingError) existingError.remove();
        
        // 添加新的错误信息
        const errorElement = document.createElement('div');
        errorElement.className = 'field-error';
        errorElement.textContent = message;
        fieldGroup.appendChild(errorElement);
    }

    // ==================== 数据加载 ====================

    /**
     * 填充编辑模式下的固定收益字段数据
     * @param {Object} transactionData - 包含固定收益详情的交易数据
     */
    async populateFixedIncomeFields(transactionData) {
        console.log('🔄 开始填充固定收益字段数据:', transactionData);
        
        try {
            // 获取完整的交易详情（包含固定收益字段）
            let fullTransactionData = transactionData;
            
            // 如果传入的数据不包含固定收益字段，从API获取完整数据
            if (!transactionData.annual_rate && !transactionData.start_date && !transactionData.maturity_date) {
                console.log('📡 获取完整交易数据...');
                const response = await fetch(`/api/transactions/${transactionData.id}`);
                if (response.ok) {
                    fullTransactionData = await response.json();
                    console.log('✅ 获取到完整交易数据:', fullTransactionData);
                } else {
                    console.warn('⚠️ 无法获取完整交易数据，使用基础数据');
                }
            }
            
            // 填充固定收益字段
            if (fullTransactionData.annual_rate !== undefined && fullTransactionData.annual_rate !== null) {
                const annualRateField = document.getElementById('annualRate');
                if (annualRateField) {
                    annualRateField.value = fullTransactionData.annual_rate;
                    console.log('📝 填充年利率:', fullTransactionData.annual_rate);
                }
            }
            
            if (fullTransactionData.start_date) {
                const startDateField = document.getElementById('fiStartDate');
                if (startDateField) {
                    startDateField.value = fullTransactionData.start_date;
                    console.log('📝 填充起息日期:', fullTransactionData.start_date);
                }
            }
            
            if (fullTransactionData.maturity_date) {
                const maturityDateField = document.getElementById('maturityDate');
                if (maturityDateField) {
                    maturityDateField.value = fullTransactionData.maturity_date;
                    console.log('📝 填充到期日期:', fullTransactionData.maturity_date);
                }
            }
            
            if (fullTransactionData.interest_type) {
                const interestTypeField = document.getElementById('interestType');
                if (interestTypeField) {
                    interestTypeField.value = fullTransactionData.interest_type;
                    console.log('📝 填充利息类型:', fullTransactionData.interest_type);
                }
            }
            
            if (fullTransactionData.payment_frequency) {
                const paymentFrequencyField = document.getElementById('paymentFrequency');
                if (paymentFrequencyField) {
                    paymentFrequencyField.value = fullTransactionData.payment_frequency;
                    console.log('📝 填充付息频率:', fullTransactionData.payment_frequency);
                }
            }
            
            if (fullTransactionData.face_value !== undefined && fullTransactionData.face_value !== null) {
                const faceValueField = document.getElementById('faceValue');
                if (faceValueField) {
                    faceValueField.value = fullTransactionData.face_value;
                    console.log('📝 填充面值:', fullTransactionData.face_value);
                }
            }
            
            if (fullTransactionData.coupon_rate !== undefined && fullTransactionData.coupon_rate !== null) {
                const couponRateField = document.getElementById('couponRate');
                if (couponRateField) {
                    couponRateField.value = fullTransactionData.coupon_rate;
                    console.log('📝 填充票面利率:', fullTransactionData.coupon_rate);
                }
            }
            
            // 计算并填充存款期限（根据起息日期和到期日期反推）
            if (fullTransactionData.start_date && fullTransactionData.maturity_date) {
                const startDate = new Date(fullTransactionData.start_date);
                const maturityDate = new Date(fullTransactionData.maturity_date);
                const monthsDiff = this.calculateMonthsBetween(startDate, maturityDate);
                
                const depositTermField = document.getElementById('depositTerm');
                if (depositTermField) {
                    // 匹配标准期限选项
                    const standardTerms = {
                        1: '1',
                        3: '3',
                        6: '6',
                        12: '12',
                        24: '24',
                        36: '36',
                        60: '60'
                    };
                    
                    if (standardTerms[monthsDiff]) {
                        depositTermField.value = standardTerms[monthsDiff];
                        console.log('📝 填充存款期限:', monthsDiff + '个月');
                    } else {
                        console.log('⚠️ 非标准期限，无法自动填充:', monthsDiff + '个月');
                    }
                }
            }
            
            // 填充汇率字段（编辑模式下很重要）
            if (fullTransactionData.exchange_rate !== undefined && fullTransactionData.exchange_rate !== null) {
                const exchangeRateField = document.getElementById('exchangeRate');
                if (exchangeRateField) {
                    exchangeRateField.value = fullTransactionData.exchange_rate;
                    console.log('💱 填充交易汇率:', fullTransactionData.exchange_rate);
                }
            }
            
            // 根据交易类型显示相应的字段
            if (fullTransactionData.type) {
                this.adjustFieldsForTransactionType(fullTransactionData.type);
            }
            
            // 更新汇率预览显示
            this.updateExchangeRatePreview();
            
            //console.log('✅ 固定收益字段数据填充完成');
            
        } catch (error) {
            console.error('❌ 填充固定收益字段失败:', error);
        }
    }

    // ==================== 工具方法 ====================

    isFixedIncomeField(element) {
        const fixedIncomeFieldIds = [
            'annualRate', 'fiStartDate', 'maturityDate', 
            'depositTerm', 'interestType', 'paymentFrequency'
        ];
        return fixedIncomeFieldIds.includes(element.id);
    }

    getFixedIncomeFormData() {
        if (!this.uiState.isFixedIncomeMode) return {};

        const currentTransactionType = this.uiState.currentTransactionType;
        
        // 利息交易使用极简数据收集
        if (currentTransactionType === 'INTEREST') {
            console.log('📝 利息交易模式：收集简化数据');
            return {
                transaction_type: 'INTEREST'
                // 币种和汇率将在handleInterestTransaction中自动获取
                // 不收集固定收益相关字段
            };
        }

        // 非利息交易收集完整数据
        const data = {
            annual_rate: document.getElementById('annualRate')?.value,
            start_date: document.getElementById('fiStartDate')?.value,
            maturity_date: document.getElementById('maturityDate')?.value,
            deposit_term: document.getElementById('depositTerm')?.value,
            interest_type: document.getElementById('interestType')?.value || 'SIMPLE',
            payment_frequency: document.getElementById('paymentFrequency')?.value || 'MATURITY',
            transaction_type: document.getElementById('transactionType')?.value || ''
        };

        console.log('📝 非利息交易模式：收集完整数据', data);
        return data;
    }

    // ==================== 外汇定期存款专用方法 ====================

    /**
     * 更新汇率预览信息
     */
    updateExchangeRatePreview() {
        const amountField = document.getElementById('transactionAmount');
        const currencyField = document.getElementById('transactionCurrency');
        const exchangeRateField = document.getElementById('exchangeRate');
        const previewGroup = document.getElementById('exchangeRatePreviewGroup');
        const previewContainer = document.getElementById('exchangeRatePreviewContainer');

        if (!amountField || !currencyField) return;

        const amount = parseFloat(amountField.value) || 0;
        // 获取实际的币种代码，而不是显示文本
        const currencyCode = currencyField.getAttribute('data-currency-code') || 
                           currencyField.value.split(' ')[0] || // 从"CNY - 人民币"中提取"CNY"
                           currencyField.value;
        const exchangeRate = parseFloat(exchangeRateField?.value) || 0;

        console.log('💱 汇率预览更新:', {
            amount,
            currencyCode,
            exchangeRate,
            fieldValue: currencyField.value
        });

        // 如果是人民币，隐藏汇率预览
        if (currencyCode === 'CNY') {
            console.log('🇨🇳 检测到人民币，隐藏汇率预览');
            if (previewGroup) previewGroup.style.display = 'none';
            if (previewContainer) previewContainer.style.display = 'none';
            return;
        }

        // 显示汇率预览容器和组
        if (previewContainer) previewContainer.style.display = 'block';
        if (previewGroup) previewGroup.style.display = 'block';

        // 更新显示信息
        const foreignAmountSpan = document.getElementById('foreignCurrencyAmount');
        const exchangeRateSpan = document.getElementById('currentExchangeRate');
        const cnyEquivalentSpan = document.getElementById('cnyEquivalent');

        if (foreignAmountSpan) {
            const currencySymbol = this.getCurrencySymbol(currencyCode);
            foreignAmountSpan.textContent = `${currencySymbol}${amount.toFixed(2)}`;
        }

        if (exchangeRateSpan) {
            exchangeRateSpan.textContent = exchangeRate > 0 ? `1 ${currencyCode} = ${exchangeRate} CNY` : '待输入';
        }

        if (cnyEquivalentSpan) {
            const cnyEquivalent = amount * exchangeRate;
            cnyEquivalentSpan.textContent = `¥${cnyEquivalent.toFixed(2)}`;
        }
    }

    /**
     * 处理币种变化（固定收益专用）
     */
    handleCurrencyChangeForFixedIncome() {
        const currencyField = document.getElementById('transactionCurrency');
        const exchangeRateGroup = document.getElementById('exchangeRateGroup');
        const exchangeRateField = document.getElementById('exchangeRate');

        if (!currencyField) return;

        // 获取实际的币种代码，而不是显示文本
        const currencyCode = currencyField.getAttribute('data-currency-code') || 
                           currencyField.value.split(' ')[0] || // 从"CNY - 人民币"中提取"CNY"
                           currencyField.value;

        console.log('💱 币种变化处理（固定收益）:', {
            currencyCode,
            fieldValue: currencyField.value,
            isFixedIncomeMode: this.uiState.isFixedIncomeMode
        });

        // 如果是人民币，隐藏汇率字段
        if (currencyCode === 'CNY') {
            console.log('🇨🇳 检测到人民币，隐藏汇率字段');
            if (exchangeRateGroup) exchangeRateGroup.style.display = 'none';
            if (exchangeRateField) exchangeRateField.value = '1.0';
        } else {
            // 外币显示汇率字段
            console.log('🌍 检测到外币，显示汇率字段');
            if (exchangeRateGroup) exchangeRateGroup.style.display = 'block';
            // 自动获取汇率（如果有该功能）
            this.autoFillExchangeRate(currencyCode);
        }

        // 更新汇率预览
        this.updateExchangeRatePreview();
    }

    /**
     * 自动填充汇率
     */
    async autoFillExchangeRate(currency) {
        if (currency === 'CNY') return;

        // 检查是否为编辑模式，编辑模式下不自动覆盖汇率
        if (this.transactionManager && this.transactionManager.editingTransactionId) {
            console.log('✏️ 编辑模式：不自动填充汇率，保持现有汇率');
            return;
        }

        try {
            const exchangeRate = await this.getExchangeRate(currency);
            const exchangeRateField = document.getElementById('exchangeRate');
            
            if (exchangeRateField && exchangeRate > 0) {
                exchangeRateField.value = exchangeRate.toFixed(4);
                console.log(`🌍 自动填充汇率（新增模式）: 1 ${currency} = ${exchangeRate} CNY`);
                
                // 更新预览
                this.updateExchangeRatePreview();
            }
        } catch (error) {
            console.warn('⚠️ 自动获取汇率失败:', error);
        }
    }

    /**
     * 获取币种符号
     */
    getCurrencySymbol(currency) {
        const symbols = {
            'CNY': '¥',
            'USD': '$',
            'HKD': 'HK$',
            'EUR': '€'
        };
        return symbols[currency] || currency;
    }

    resetFixedIncomeFields() {
        console.log('🔄 开始重置固定收益字段');
        //console.trace('resetFixedIncomeFields 调用堆栈');
        
        const fixedIncomeFields = [
            'annualRate', 'fiStartDate', 'maturityDate', 
            'depositTerm', 'interestType', 'paymentFrequency'
        ];

        fixedIncomeFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                //console.log(`🗑️ 重置字段 ${fieldId}: ${field.value} → ''`);
                field.value = '';
                field.removeAttribute('data-user-set'); // 清除用户设置标记
                this.clearFieldError(field);
            }
        });

        // 隐藏利息预览和汇率预览
        const previewSection = document.getElementById('interestPreview');
        if (previewSection) {
            previewSection.style.display = 'none';
        }

        const exchangePreviewGroup = document.getElementById('exchangeRatePreviewGroup');
        if (exchangePreviewGroup) {
            exchangePreviewGroup.style.display = 'none';
        }

        const exchangePreviewContainer = document.getElementById('exchangeRatePreviewContainer');
        if (exchangePreviewContainer) {
            exchangePreviewContainer.style.display = 'none';
        }

        // 重置UI状态
        this.uiState.isFixedIncomeMode = false;
        this.uiState.currentTransactionType = null;
        
        console.log('✅ 固定收益字段重置完成');
    }
}

// 导出为全局变量，供TransactionManager使用
if (typeof window !== 'undefined') {
    window.FixedIncomeManager = FixedIncomeManager;
} 