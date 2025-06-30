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

        // 创建各个字段组
        this.createAnnualRateField(container);
        this.createDateFields(container);
        this.createTermField(container);
        this.createInterestTypeField(container);
        this.createPaymentFrequencyField(container);
        this.createInterestCalculator(container);
        
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

    createAnnualRateField(container) {
        const fieldGroup = document.createElement('div');
        fieldGroup.className = 'form-group';
        fieldGroup.id = 'annualRateGroup';
        fieldGroup.innerHTML = `
            <label for="annualRate" class="form-label">年利率<span class="required">*</span></label>
            <div class="input-group">
                <input type="number" 
                       id="annualRate" 
                       name="annualRate" 
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
            <label for="startDate" class="form-label">起息日期<span class="required">*</span></label>
            <input type="date" 
                   id="startDate" 
                   name="startDate" 
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
                   name="maturityDate" 
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
            <select id="depositTerm" name="depositTerm" class="form-select">
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
            <select id="interestType" name="interestType" class="form-select">
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
            <select id="paymentFrequency" name="paymentFrequency" class="form-select">
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

    // ==================== 事件绑定 ====================

    bindEvents() {
        try {
            // 注意：不要直接绑定全局元素（assetSelect, transactionType）的事件
            // 这些事件由TransactionManager处理，然后调用相应的方法
            
            // 存款期限变化自动计算到期日
            document.getElementById('depositTerm')?.addEventListener('change', () => {
                this.calculateMaturityDate();
            });

            // 起息日期变化重新计算到期日
            document.getElementById('startDate')?.addEventListener('change', () => {
                this.calculateMaturityDate();
            });

            // 字段变化时计算利息预览
            ['annualRate', 'startDate', 'maturityDate', 'interestType'].forEach(fieldId => {
                document.getElementById(fieldId)?.addEventListener('input', () => {
                    this.calculateInterestPreview();
                });
                document.getElementById(fieldId)?.addEventListener('change', () => {
                    this.calculateInterestPreview();
                });
            });

            // 实时验证
            ['annualRate', 'startDate', 'maturityDate'].forEach(fieldId => {
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

    handleAssetTypeChange(assetType) {
        console.log('🏦 FixedIncomeManager: 收到资产类型变化通知:', assetType);
        
        if (assetType === 'FIXED_INCOME') {
            console.log('✅ 显示固定收益字段');
            this.showFixedIncomeFields();
        } else {
            console.log('❌ 隐藏固定收益字段');
            this.hideFixedIncomeFields();
        }
    }

    handleTransactionTypeChange(transactionType) {
        this.uiState.currentTransactionType = transactionType;
        this.adjustFieldsForTransactionType(transactionType);
    }

    adjustFieldsForTransactionType(transactionType) {
        const container = document.getElementById('fixedIncomeFieldsContainer');
        if (!container || !this.uiState.isFixedIncomeMode) return;

        console.log('🔧 根据交易类型调整字段显示:', transactionType);

        // 根据交易类型调整字段显示
        switch (transactionType) {
            case 'DEPOSIT':
                // 存入交易显示所有字段
                console.log('📋 显示所有固定收益字段 (存入交易)');
                this.showAllFixedIncomeFields();
                break;
            case 'INTEREST':
                // 利息交易只显示基本字段
                console.log('📋 显示基本固定收益字段 (利息交易)');
                this.showBasicFixedIncomeFields();
                break;
            case 'WITHDRAW':
                // 提取交易只显示基本字段
                console.log('📋 显示基本固定收益字段 (提取交易)');
                this.showBasicFixedIncomeFields();
                break;
            default:
                // 默认情况（包括null或空值）显示所有字段
                console.log('📋 显示所有固定收益字段 (默认)');
                this.showAllFixedIncomeFields();
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
            this.adjustFieldsForTransactionType(this.uiState.currentTransactionType);
            
            // 设置必填字段的required属性
            this.setFixedIncomeFieldsRequired(true);
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
        const requiredFields = ['annualRate', 'startDate', 'maturityDate'];
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
    }

    showAllFixedIncomeFields() {
        const fieldIds = ['annualRateGroup', 'startDateGroup', 'maturityDateGroup', 
                         'depositTermGroup', 'interestTypeGroup', 'paymentFrequencyGroup'];
        fieldIds.forEach(id => {
            const field = document.getElementById(id);
            if (field) field.style.display = 'block';
        });
    }

    showBasicFixedIncomeFields() {
        // 隐藏复杂字段，只显示基本字段
        const hideFields = ['depositTermGroup', 'interestTypeGroup', 'paymentFrequencyGroup'];
        hideFields.forEach(id => {
            const field = document.getElementById(id);
            if (field) field.style.display = 'none';
        });
    }

    // ==================== 计算逻辑 ====================

    calculateMaturityDate() {
        try {
            const termSelect = document.getElementById('depositTerm');
            const startDateInput = document.getElementById('startDate');
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

    calculateInterestPreview() {
        try {
            // 获取当前表单数据
            const amount = parseFloat(document.getElementById('transactionAmount')?.value);
            const annualRate = parseFloat(document.getElementById('annualRate')?.value);
            const startDate = document.getElementById('startDate')?.value;
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
            switch (formData.transactionType) {
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
            annual_rate: parseFloat(formData.annualRate),
            start_date: formData.startDate,
            maturity_date: formData.maturityDate,
            interest_type: formData.interestType || 'SIMPLE',
            payment_frequency: formData.paymentFrequency || 'MATURITY',
            face_value: parseFloat(formData.amount),
            coupon_rate: parseFloat(formData.annualRate)
        };

        // 计算预期收益并添加到备注
        if (formData.annualRate && formData.startDate && formData.maturityDate) {
            try {
                const interestInfo = this.calculateInterest({
                    principal: parseFloat(formData.amount),
                    annualRate: parseFloat(formData.annualRate),
                    startDate: new Date(formData.startDate),
                    endDate: new Date(formData.maturityDate),
                    interestType: formData.interestType || 'SIMPLE'
                });

                const originalNotes = formData.notes || '';
                const interestNote = `预期收益: ¥${interestInfo.totalInterest.toFixed(2)}, 到期总额: ¥${interestInfo.totalAmount.toFixed(2)}`;
                transactionData.notes = originalNotes ? `${originalNotes}\n${interestNote}` : interestNote;
            } catch (error) {
                console.warn('预期收益计算失败:', error);
            }
        }

        return await this.transactionManager.saveTransaction(transactionData);
    }

    async handleInterestTransaction(formData) {
        const transactionData = {
            ...formData,
            transaction_type: 'INTEREST'
        };

        return await this.transactionManager.saveTransaction(transactionData);
    }

    async handleWithdrawalTransaction(formData) {
        const transactionData = {
            ...formData,
            transaction_type: 'WITHDRAW'
        };

        return await this.transactionManager.saveTransaction(transactionData);
    }

    // ==================== 验证逻辑 ====================

    validateFixedIncomeTransaction(formData) {
        const errors = [];

        // 基础验证
        if (!formData.amount || parseFloat(formData.amount) <= 0) {
            errors.push('交易金额必须大于0');
        }

        if (!formData.transactionDate) {
            errors.push('交易日期不能为空');
        }

        // 存入交易的特殊验证
        if (formData.transactionType === 'DEPOSIT') {
            if (!formData.annualRate || parseFloat(formData.annualRate) <= 0) {
                errors.push('年利率必须大于0');
            }

            if (formData.annualRate && parseFloat(formData.annualRate) > 50) {
                errors.push('年利率不能超过50%');
            }

            if (!formData.startDate) {
                errors.push('起息日期不能为空');
            }

            if (!formData.maturityDate) {
                errors.push('到期日期不能为空');
            }

            if (formData.startDate && formData.maturityDate && 
                new Date(formData.maturityDate) <= new Date(formData.startDate)) {
                errors.push('到期日期必须晚于起息日期');
            }

            // 日期合理性验证
            if (formData.startDate && new Date(formData.startDate) > new Date()) {
                const today = new Date().toISOString().split('T')[0];
                if (formData.startDate > today) {
                    errors.push('起息日期不能晚于今天');
                }
            }
        }

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
            
            case 'startDate':
                if (field.value) {
                    const maturityDate = document.getElementById('maturityDate')?.value;
                    if (maturityDate && new Date(field.value) >= new Date(maturityDate)) {
                        this.showFieldError(fieldGroup, '起息日期必须早于到期日期');
                    }
                }
                break;
            
            case 'maturityDate':
                if (field.value) {
                    const startDate = document.getElementById('startDate')?.value;
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

    // ==================== 工具方法 ====================

    isFixedIncomeField(element) {
        const fixedIncomeFieldIds = [
            'annualRate', 'startDate', 'maturityDate', 
            'depositTerm', 'interestType', 'paymentFrequency'
        ];
        return fixedIncomeFieldIds.includes(element.id);
    }

    getFixedIncomeFormData() {
        if (!this.uiState.isFixedIncomeMode) return {};

        return {
            annualRate: document.getElementById('annualRate')?.value,
            startDate: document.getElementById('startDate')?.value,
            maturityDate: document.getElementById('maturityDate')?.value,
            depositTerm: document.getElementById('depositTerm')?.value,
            interestType: document.getElementById('interestType')?.value || 'SIMPLE',
            paymentFrequency: document.getElementById('paymentFrequency')?.value || 'MATURITY'
        };
    }

    resetFixedIncomeFields() {
        const fixedIncomeFields = [
            'annualRate', 'startDate', 'maturityDate', 
            'depositTerm', 'interestType', 'paymentFrequency'
        ];

        fixedIncomeFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.value = '';
                this.clearFieldError(field);
            }
        });

        // 隐藏利息预览
        const previewSection = document.getElementById('interestPreview');
        if (previewSection) {
            previewSection.style.display = 'none';
        }

        // 重置UI状态
        this.uiState.isFixedIncomeMode = false;
        this.uiState.currentTransactionType = null;
    }
}

// 导出为全局变量，供TransactionManager使用
if (typeof window !== 'undefined') {
    window.FixedIncomeManager = FixedIncomeManager;
} 