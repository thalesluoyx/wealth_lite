/**
 * 资产管理模块
 * 处理资产的增删改查操作
 */

class AssetManager {
    constructor(app = null) {
        this.app = app;
        this.assets = [];
        this.editingAssetId = null;
        
        // 枚举数据（从API获取）
        this.enums = null;
        
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.loadEnums();
        this.loadAssets();
    }

    async loadEnums() {
        try {
            console.log('Loading enums from static file...');
            // 优先从静态JSON文件加载
            const response = await fetch('/static/data/enums.json');
            if (response.ok) {
                this.enums = await response.json();
                console.log('Enums loaded from static file:', this.enums);
                return;
            } else {
                console.warn('Static enums file not found, trying API...');
            }
        } catch (error) {
            console.warn('Error loading static enums file:', error);
        }

        // 备用方案：从API加载
        try {
            const response = await fetch('/api/enums');
            if (response.ok) {
                this.enums = await response.json();
                console.log('Enums loaded from API:', this.enums);
            } else {
                console.error('Failed to load enums from API');
                this.showNotification('加载枚举数据失败', 'error');
                this.enums = this.getDefaultEnums();
            }
        } catch (error) {
            console.error('Error loading enums from API:', error);
            this.showNotification('网络错误，使用默认数据', 'warning');
            this.enums = this.getDefaultEnums();
        }
    }

    getDefaultEnums() {
        // 备用的枚举数据，防止API失败时使用
        return {
            asset_subtype_mapping: {
                'CASH': [
                    { value: 'CHECKING_ACCOUNT', text: '活期存款' },
                    { value: 'MONEY_MARKET_FUND', text: '货币市场基金' }
                ],
                'FIXED_INCOME': [
                    { value: 'TIME_DEPOSIT', text: '定期存款' },
                    { value: 'FOREIGN_CURRENCY_DEPOSIT', text: '外币定期存款' },
                    { value: 'BANK_WEALTH_PRODUCT', text: '银行理财' },
                    { value: 'GOVERNMENT_BOND', text: '政府债券' },
                    { value: 'CORPORATE_BOND', text: '企业债券' }
                ],
                'EQUITY': [
                    { value: 'DOMESTIC_STOCK', text: 'A股股票' },
                    { value: 'FOREIGN_STOCK', text: '海外股票' },
                    { value: 'MUTUAL_FUND', text: '公募基金' },
                    { value: 'ETF', text: '交易所基金' }
                ] 
            }
        };
    }

    bindEvents() {
        // 新增资产按钮
        const addAssetBtn = document.getElementById('addAssetBtn');
        if (addAssetBtn) {
            addAssetBtn.addEventListener('click', () => {
                this.openAssetModal();
            });
        }

        // 模态窗口关闭
        const closeModal = document.getElementById('closeAssetManagementModal');
        if (closeModal) {
            closeModal.addEventListener('click', () => {
                this.closeAssetModal();
            });
        }

        const cancelBtn = document.getElementById('cancelAssetManagementBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.closeAssetModal();
            });
        }

        // 资产表单提交
        const form = document.getElementById('assetManagementForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveAsset();
            });
        }

        // 资产类型变化事件
        const assetTypeSelect = document.getElementById('assetManagementType');
        if (assetTypeSelect) {
            assetTypeSelect.addEventListener('change', (e) => {
                this.onAssetTypeChange(e.target.value);
            });
        }
    }

    async loadAssets() {
        try {
            console.log('Loading assets...');
            const response = await fetch('/api/assets');
            if (response.ok) {
                this.assets = await response.json();
                console.log('Assets loaded:', this.assets);
                this.renderAssets();
            } else {
                console.error('Failed to load assets');
                this.showNotification('加载资产失败', 'error');
            }
        } catch (error) {
            console.error('Error loading assets:', error);
            this.showNotification('网络错误，请稍后重试', 'error');
        }
    }

    openAssetModal(asset = null) {
        const modal = document.getElementById('assetManagementModal');
        const title = document.getElementById('assetModalTitle');
        const form = document.getElementById('assetManagementForm');
        
        if (!modal || !title || !form) {
            console.error('Modal elements not found');
            return;
        }
        
        if (asset) {
            // 编辑模式
            title.textContent = '编辑资产';
            this.editingAssetId = asset.id;
            this.populateForm(asset);
        } else {
            // 新增模式
            title.textContent = '新增资产';
            this.editingAssetId = null;
            form.reset();
        }
        
        modal.classList.add('show');
    }

    closeAssetModal() {
        const modal = document.getElementById('assetManagementModal');
        if (modal) {
            modal.classList.remove('show');
        }
        this.editingAssetId = null;
        
        const form = document.getElementById('assetManagementForm');
        if (form) {
            form.reset();
        }
    }

    onAssetTypeChange(assetType) {
        const subTypeGroup = document.getElementById('assetSubTypeGroup');
        const subTypeSelect = document.getElementById('assetManagementSubType');
        
        if (!subTypeGroup || !subTypeSelect || !this.enums) return;

        const subTypes = this.enums.asset_subtype_mapping[assetType];
        if (assetType && subTypes) {
            // 显示子类型选择器
            subTypeGroup.style.display = 'block';
            
            // 清空并重新填充子类型选项
            subTypeSelect.innerHTML = '<option value="">请选择资产子类型...</option>';
            
            subTypes.forEach(subType => {
                const option = document.createElement('option');
                option.value = subType.value;
                option.textContent = subType.text;
                subTypeSelect.appendChild(option);
            });
            
            // 设置为必填
            subTypeSelect.required = true;
        } else {
            // 隐藏子类型选择器
            subTypeGroup.style.display = 'none';
            subTypeSelect.required = false;
            subTypeSelect.value = '';
        }
    }

    populateForm(asset) {
        const nameInput = document.getElementById('assetManagementName');
        const typeSelect = document.getElementById('assetManagementType');
        const subTypeSelect = document.getElementById('assetManagementSubType');
        const currencySelect = document.getElementById('assetManagementCurrency');
        const descriptionTextarea = document.getElementById('assetManagementDescription');
        
        if (nameInput) nameInput.value = asset.name || '';
        if (typeSelect) {
            typeSelect.value = asset.asset_type || '';
            // 触发类型变化事件以显示子类型
            this.onAssetTypeChange(asset.asset_type);
        }
        if (subTypeSelect && asset.asset_subtype) {
            subTypeSelect.value = asset.asset_subtype;
        }
        if (currencySelect) currencySelect.value = asset.currency || '';
        if (descriptionTextarea) descriptionTextarea.value = asset.description || '';
    }

    async saveAsset() {
        console.log('==========saveAsset in assets.js ');
        const nameInput = document.getElementById('assetManagementName');
        const typeSelect = document.getElementById('assetManagementType');
        const subTypeSelect = document.getElementById('assetManagementSubType');
        const currencySelect = document.getElementById('assetManagementCurrency');
        const descriptionTextarea = document.getElementById('assetManagementDescription');
        
        if (!nameInput || !typeSelect || !currencySelect) {
            this.showNotification('表单元素未找到', 'error');
            return;
        }

        const formData = {
            name: nameInput.value,
            asset_type: typeSelect.value,
            currency: currencySelect.value,
            description: descriptionTextarea ? descriptionTextarea.value : ''
        };

        // 添加资产子类型（如果选择了）
        if (subTypeSelect && subTypeSelect.value) {
            formData.asset_subtype = subTypeSelect.value;
        }

        // 验证必填字段
        if (!formData.name || !formData.asset_type || !formData.currency) {
            this.showNotification('请填写所有必填字段', 'error');
            return;
        }

        // 如果显示了子类型选择器且为必填，验证子类型
        if (subTypeSelect && subTypeSelect.required && !subTypeSelect.value) {
            this.showNotification('请选择资产子类型', 'error');
            return;
        }
        console.log('==========saveAsset2 ');
        try {
            let response;
            if (this.editingAssetId) {
                console.log('==========更新资产: ', this.editingAssetId);
                // 更新资产
                response = await fetch(`/api/assets/${this.editingAssetId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
            } else {
                console.log('==========创建新资产 ');
                // 创建新资产
                response = await fetch('/api/assets', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
            }

            if (response.ok) {
                this.closeAssetModal();
                await this.loadAssets();
                this.showNotification(this.editingAssetId ? '资产更新成功' : '资产创建成功', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.detail || '操作失败', 'error');
            }
        } catch (error) {
            console.error('Error saving asset:', error);
            this.showNotification('网络错误，请稍后重试', 'error');
        }
    }

    async deleteAsset(assetId) {
        if (!confirm('确定要删除这个资产吗？删除后无法恢复。')) {
            return;
        }

        try {
            const response = await fetch(`/api/assets/${assetId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                await this.loadAssets();
                this.showNotification('资产删除成功', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.detail || '删除失败', 'error');
            }
        } catch (error) {
            console.error('Error deleting asset:', error);
            this.showNotification('网络错误，请稍后重试', 'error');
        }
    }

    renderAssets() {
        const tbody = document.getElementById('assetsTableBody');
        const emptyDiv = document.getElementById('assetsEmpty');
        const countSpan = document.getElementById('assetCount');
        
        console.log('Rendering assets, tbody found:', !!tbody);
        
        if (!tbody) {
            console.error('Assets table body not found');
            return;
        }
        
        if (this.assets.length === 0) {
            tbody.innerHTML = '';
            if (emptyDiv) emptyDiv.style.display = 'block';
        } else {
            if (emptyDiv) emptyDiv.style.display = 'none';
            tbody.innerHTML = this.assets.map(asset => this.renderAssetRow(asset)).join('');
        }

        // 更新资产数量
        if (countSpan) {
            countSpan.textContent = `共 ${this.assets.length} 个资产`;
        }

        // 重新初始化图标
        if (this.app && this.app.initializeIcons) {
            this.app.initializeIcons();
        } else if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    renderAssetRow(asset) {
        const createdDate = new Date(asset.created_at).toLocaleDateString('zh-CN');
        const assetTypeClass = asset.asset_type.toLowerCase().replace('_', '-');
        const subTypeText = this.getAssetSubTypeText(asset.asset_subtype);
        
        return `
            <tr>
                <td>
                    <div class="asset-name">${asset.name}</div>
                </td>
                <td>
                    <span class="asset-type ${assetTypeClass}">
                        ${this.getAssetTypeText(asset.asset_type)}
                    </span>
                </td>
                <td>
                    <span class="asset-subtype">
                        ${subTypeText !== '-' ? subTypeText : ''}
                    </span>
                </td>
                <td>
                    <span class="currency-badge">${asset.currency}</span>
                </td>
                <td>
                    <span class="created-date">${createdDate}</span>
                </td>
                <td>
                    <div class="asset-description" title="${asset.description || ''}">
                        ${asset.description || '-'}
                    </div>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-action edit" onclick="window.assetManager.openAssetModal(${JSON.stringify(asset).replace(/"/g, '&quot;')})">
                            <i data-lucide="edit"></i>
                            编辑
                        </button>
                        <button class="btn-action delete" onclick="window.assetManager.deleteAsset('${asset.id}')">
                            <i data-lucide="trash-2"></i>
                            删除
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    getAssetTypeText(type) {
        const typeMap = {
            'CASH': '现金及等价物',
            'FIXED_INCOME': '固定收益类',
            'EQUITY': '权益类'
        };
        return typeMap[type] || type;
    }

    getAssetSubTypeText(subType) {
        if (!subType) return '-';
        
        // 如果没有枚举数据，直接返回原值
        if (!this.enums) {
            return subType;
        }
        
        // 使用API获取的枚举数据 - 注意这里的结构是对象
        if (this.enums.asset_subtypes && this.enums.asset_subtypes[subType]) {
            const subTypeData = this.enums.asset_subtypes[subType];
            return subTypeData.display_name || subTypeData.text || subTypeData.value || subType;
        }
        
        // 备用方案：在子类型映射中查找
        for (const [assetType, subTypes] of Object.entries(this.enums.asset_subtype_mapping || {})) {
            const found = subTypes.find(st => st.value === subType);
            if (found) {
                return found.text;
            }
        }
        
        // 如果都找不到，返回原值
        return subType;
    }

    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // 添加到页面
        document.body.appendChild(notification);
        
        // 自动移除
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.remove();
            }
        }, 3000);
    }
}

// 导出给其他模块使用
window.AssetManager = AssetManager;