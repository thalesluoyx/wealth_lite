/**
 * 投资组合快照功能 JavaScript
 */

class PortfolioManager {
    constructor() {
        this.currentPage = 'auto'; // 当前显示的快照类型
        this.selectedSnapshots = {}; // 选中的快照用于对比
        this.currentAiConfig = null; // 当前AI配置
        this.isLoading = false;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadPortfolioOverview();
        this.loadSnapshots();
        this.loadAiConfig();
    }

    bindEvents() {
        // 创建快照按钮
        document.getElementById('createSnapshotBtn')?.addEventListener('click', () => {
            this.showCreateSnapshotModal();
        });

        // 快照类型切换
        document.getElementById('autoSnapshotsTab')?.addEventListener('click', (e) => {
            this.switchSnapshotType('auto', e.target);
        });
        
        document.getElementById('manualSnapshotsTab')?.addEventListener('click', (e) => {
            this.switchSnapshotType('manual', e.target);
        });

        // 快照对比
        document.getElementById('compareSnapshotsBtn')?.addEventListener('click', () => {
            this.compareSnapshots();
        });

        document.getElementById('clearComparisonBtn')?.addEventListener('click', () => {
            this.clearComparison();
        });

        // AI分析
        document.getElementById('aiAnalyzeBtn')?.addEventListener('click', () => {
            this.analyzeWithAI();
        });

        document.getElementById('changeAiTypeBtn')?.addEventListener('click', () => {
            this.showAiConfigModal();
        });

        // 模态窗口事件
        this.bindModalEvents();
    }

    bindModalEvents() {
        // 创建快照模态窗口
        const createSnapshotModal = document.getElementById('createSnapshotModal');
        const closeSnapshotModal = document.getElementById('closeSnapshotModal');
        const cancelSnapshotBtn = document.getElementById('cancelSnapshotBtn');
        const createSnapshotForm = document.getElementById('createSnapshotForm');

        [closeSnapshotModal, cancelSnapshotBtn].forEach(btn => {
            btn?.addEventListener('click', () => this.hideCreateSnapshotModal());
        });

        createSnapshotForm?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createSnapshot(e);
        });

        // AI配置模态窗口
        const aiConfigModal = document.getElementById('aiConfigModal');
        const closeAiConfigModal = document.getElementById('closeAiConfigModal');
        const cancelAiConfigBtn = document.getElementById('cancelAiConfigBtn');
        const saveAiConfigBtn = document.getElementById('saveAiConfigBtn');

        [closeAiConfigModal, cancelAiConfigBtn].forEach(btn => {
            btn?.addEventListener('click', () => this.hideAiConfigModal());
        });

        saveAiConfigBtn?.addEventListener('click', () => {
            this.saveAiConfig();
        });

        // AI类型切换
        document.querySelectorAll('input[name="aiType"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.toggleAiConfigSection(e.target.value);
            });
        });

        // Temperature滑块
        const temperatureRange = document.getElementById('aiTemperature');
        const temperatureValue = document.getElementById('temperatureValue');
        
        temperatureRange?.addEventListener('input', (e) => {
            temperatureValue.textContent = e.target.value;
        });

        // 快照详情模态窗口
        const snapshotDetailModal = document.getElementById('snapshotDetailModal');
        const closeSnapshotDetailModal = document.getElementById('closeSnapshotDetailModal');
        const closeSnapshotDetailBtn = document.getElementById('closeSnapshotDetailBtn');

        [closeSnapshotDetailModal, closeSnapshotDetailBtn].forEach(btn => {
            btn?.addEventListener('click', () => this.hideSnapshotDetailModal());
        });

        // 点击模态窗口外部关闭
        [createSnapshotModal, aiConfigModal, snapshotDetailModal].forEach(modal => {
            modal?.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
        });
    }

    // ==================== 投资组合概览 ====================
    async loadPortfolioOverview() {
        try {
            // 使用相对路径，通过代理访问API
            const response = await fetch('/api/portfolio/current');
            const data = await response.json();
            
            if (data.success) {
                this.updatePortfolioOverview(data.data);
            } else {
                throw new Error(data.message || '获取投资组合数据失败');
            }
        } catch (error) {
            console.error('加载投资组合概览失败:', error);
            this.showError('加载投资组合数据失败');
            
            // 使用模拟数据作为备用
            this.updatePortfolioOverview({
                total_value: 1250000.00,
                total_return: 250000.00,
                total_return_rate: 0.25
            });
        }
    }

    updatePortfolioOverview(portfolio) {
        document.getElementById('portfolioTotalValue').textContent = 
            this.formatCurrency(portfolio.total_value || 0);
        document.getElementById('portfolioTotalReturn').textContent = 
            this.formatCurrency(portfolio.total_return || 0);
        document.getElementById('portfolioReturnRate').textContent = 
            this.formatPercentage(portfolio.total_return_rate || 0);
    }

    // ==================== 快照管理 ====================
    async loadSnapshots() {
        try {
            const response = await fetch(`/api/snapshots?type=${this.currentPage}&limit=50`);
            const data = await response.json();
            
            if (data.success) {
                this.renderSnapshots(data.data.snapshots || []);
                this.updateSnapshotStats(data.data.stats || {});
            } else {
                throw new Error(data.message || '获取快照数据失败');
            }
        } catch (error) {
            console.error('加载快照数据失败:', error);
            this.showError('加载快照数据失败');
        }
    }

    renderSnapshots(snapshots) {
        const tbody = document.getElementById('snapshotsTableBody');
        const emptyDiv = document.getElementById('snapshotsEmpty');
        
        if (!tbody) return;

        if (snapshots.length === 0) {
            tbody.innerHTML = '';
            emptyDiv.style.display = 'block';
            return;
        }

        emptyDiv.style.display = 'none';
        
        tbody.innerHTML = snapshots.map(snapshot => `
            <tr class="snapshot-row" data-snapshot-id="${snapshot.snapshot_id}">
                <td>${this.formatDate(snapshot.snapshot_date)}</td>
                <td>
                    <span class="snapshot-type-badge ${snapshot.snapshot_type.toLowerCase()}">
                        <i data-lucide="${snapshot.snapshot_type === 'AUTO' ? 'zap' : 'user'}"></i>
                        ${snapshot.snapshot_type === 'AUTO' ? '自动' : '手动'}
                    </span>
                </td>
                <td>${this.formatCurrency(snapshot.total_value)}</td>
                <td class="${snapshot.total_return_rate >= 0 ? 'positive' : 'negative'}">
                    ${this.formatPercentage(snapshot.total_return_rate)}
                </td>
                <td class="snapshot-notes" title="${snapshot.notes || ''}">
                    ${snapshot.notes ? 
                        (snapshot.notes.length > 20 ? snapshot.notes.substring(0, 20) + '...' : snapshot.notes) : 
                        '-'
                    }
                </td>
                <td>
                    <div class="snapshot-actions">
                        <button class="btn-action" onclick="portfolioManager.viewSnapshotDetail('${snapshot.snapshot_id}')">
                            查看详情
                        </button>
                        <button class="btn-action" onclick="portfolioManager.selectSnapshotForComparison('${snapshot.snapshot_id}')">
                            选择对比
                        </button>
                        <button class="btn-action analyze" onclick="portfolioManager.analyzeSnapshot('${snapshot.snapshot_id}')">
                            AI分析
                        </button>
                        ${snapshot.snapshot_type === 'MANUAL' && !snapshot.is_today ? 
                            `<button class="btn-action delete" onclick="portfolioManager.deleteSnapshot('${snapshot.snapshot_id}')">删除</button>` : 
                            ''
                        }
                    </div>
                </td>
            </tr>
        `).join('');

        // 重新初始化图标
        lucide.createIcons();
    }

    switchSnapshotType(type, tabElement) {
        // 更新标签状态
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        tabElement.classList.add('active');
        
        this.currentPage = type;
        this.loadSnapshots();
    }

    // ==================== 创建快照 ====================
    async showCreateSnapshotModal() {
        // 加载当前投资组合状态用于预览
        try {
            const response = await fetch('/api/portfolio/current');
            const data = await response.json();
            
            if (data.success) {
                this.updateSnapshotPreview(data.data);
            }
            
            // 检查今日是否已有手动快照
            await this.checkTodaySnapshot();
            
            document.getElementById('createSnapshotModal').style.display = 'flex';
        } catch (error) {
            console.error('准备快照创建失败:', error);
            this.showError('无法创建快照');
        }
    }

    hideCreateSnapshotModal() {
        document.getElementById('createSnapshotModal').style.display = 'none';
        document.getElementById('snapshotNotes').value = '';
        document.getElementById('snapshotWarning').style.display = 'none';
    }

    updateSnapshotPreview(portfolio) {
        document.getElementById('previewTotalValue').textContent = 
            this.formatCurrency(portfolio.total_value || 0);
        document.getElementById('previewTotalReturn').textContent = 
            this.formatCurrency(portfolio.total_return || 0);
        document.getElementById('previewReturnRate').textContent = 
            this.formatPercentage(portfolio.total_return_rate || 0);
    }

    async checkTodaySnapshot() {
        try {
            const response = await fetch('/api/snapshots/today/manual');
            const data = await response.json();
            
            if (data.success && data.data.snapshot) {
                document.getElementById('snapshotWarning').style.display = 'flex';
            }
        } catch (error) {
            console.error('检查今日快照失败:', error);
        }
    }

    async createSnapshot(e) {
        if (this.isLoading) return;
        const submitBtn = e?.submitter || document.querySelector('#createSnapshotForm button[type="submit"]');
        if (!submitBtn) return;
        const originalText = submitBtn.textContent;
        submitBtn.textContent = '创建中...';
        submitBtn.disabled = true;

        try {
            const notes = document.getElementById('snapshotNotes').value.trim();
            
            const response = await fetch('/api/snapshots', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    notes: notes
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.hideCreateSnapshotModal();
                this.showSuccess('快照创建成功');
                this.loadSnapshots();
                this.loadPortfolioOverview();
            } else {
                throw new Error(data.message || '创建快照失败');
            }
        } catch (error) {
            console.error('创建快照失败:', error);
            this.showError(error.message || '创建快照失败');
        } finally {
            this.isLoading = false;
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    }

    // ==================== 快照对比 ====================
    /**
     * 选择快照进行对比
     * @param {string} snapshotId 快照ID
     */
    selectSnapshotForComparison(snapshotId) {
        const snapshot = this.getSnapshotFromTable(snapshotId);
        if (!snapshot) return;

        if (!this.selectedSnapshots.snapshot1) {
            this.selectedSnapshots.snapshot1 = snapshot;
            this.updateSelectedSnapshotDisplay('selectedSnapshot1', snapshot);
            this.showNotification(`已选择第一个快照: ${this.formatDate(snapshot.snapshot_date)}`, 'info');
        } else if (!this.selectedSnapshots.snapshot2) {
            this.selectedSnapshots.snapshot2 = snapshot;
            this.updateSelectedSnapshotDisplay('selectedSnapshot2', snapshot);
            this.showNotification(`已选择第二个快照: ${this.formatDate(snapshot.snapshot_date)}`, 'info');
            
            // 询问用户是否进行AI对比分析
            if (confirm('您已选择两个快照，是否进行AI对比分析？')) {
                this.analyzeCompareSnapshots();
            }
        } else {
            // 如果已经选择了两个，替换第一个
            this.selectedSnapshots.snapshot1 = this.selectedSnapshots.snapshot2;
            this.selectedSnapshots.snapshot2 = snapshot;
            this.updateSelectedSnapshotDisplay('selectedSnapshot1', this.selectedSnapshots.snapshot1);
            this.updateSelectedSnapshotDisplay('selectedSnapshot2', snapshot);
            this.showNotification(`已更新选择的快照: ${this.formatDate(snapshot.snapshot_date)}`, 'info');
        }

        this.updateComparisonButtonState();
    }
    
    /**
     * 分析对比快照
     */
    analyzeCompareSnapshots() {
        if (!this.selectedSnapshots.snapshot1 || !this.selectedSnapshots.snapshot2) {
            this.showNotification('请先选择两个快照进行对比', 'warning');
            return;
        }
        
        // 打开AI分析页面，并传递两个快照ID
        window.location.href = `ai-analysis.html?snapshot_id=${this.selectedSnapshots.snapshot1.snapshot_id}&compare_snapshot_id=${this.selectedSnapshots.snapshot2.snapshot_id}`;
    }

    getSnapshotFromTable(snapshotId) {
        const row = document.querySelector(`tr[data-snapshot-id="${snapshotId}"]`);
        if (!row) return null;

        const cells = row.cells;
        return {
            snapshot_id: snapshotId,
            snapshot_date: cells[0].textContent,
            snapshot_type: cells[1].textContent.includes('自动') ? 'AUTO' : 'MANUAL',
            total_value: this.parseCurrency(cells[2].textContent),
            total_return_rate: this.parsePercentage(cells[3].textContent)
        };
    }

    updateSelectedSnapshotDisplay(containerId, snapshot) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="snapshot-info">
                <div class="snapshot-date">${snapshot.snapshot_date}</div>
                <div class="snapshot-value">${this.formatCurrency(snapshot.total_value)}</div>
            </div>
        `;
        container.classList.add('has-snapshot');
    }

    updateComparisonButtonState() {
        const compareBtn = document.getElementById('compareSnapshotsBtn');
        const clearBtn = document.getElementById('clearComparisonBtn');
        const aiAnalyzeBtn = document.getElementById('aiAnalyzeBtn');
        
        const hasTwo = this.selectedSnapshots.snapshot1 && this.selectedSnapshots.snapshot2;
        
        compareBtn.disabled = !hasTwo;
        clearBtn.style.display = (this.selectedSnapshots.snapshot1 || this.selectedSnapshots.snapshot2) ? 'block' : 'none';
        aiAnalyzeBtn.disabled = !hasTwo;
    }

    clearComparison() {
        this.selectedSnapshots = {};
        document.getElementById('selectedSnapshot1').innerHTML = '<div class="placeholder">点击快照列表中的快照进行选择</div>';
        document.getElementById('selectedSnapshot2').innerHTML = '<div class="placeholder">选择第二个快照进行对比</div>';
        document.getElementById('selectedSnapshot1').classList.remove('has-snapshot');
        document.getElementById('selectedSnapshot2').classList.remove('has-snapshot');
        document.getElementById('comparisonResults').style.display = 'none';
        this.updateComparisonButtonState();
    }

    async compareSnapshots() {
        if (!this.selectedSnapshots.snapshot1 || !this.selectedSnapshots.snapshot2) {
            this.showError('请选择两个快照进行对比');
            return;
        }

        try {
            const response = await fetch('/api/snapshots/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    snapshot1_id: this.selectedSnapshots.snapshot1.snapshot_id,
                    snapshot2_id: this.selectedSnapshots.snapshot2.snapshot_id
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayComparisonResults(data.data);
            } else {
                throw new Error(data.message || '对比分析失败');
            }
        } catch (error) {
            console.error('快照对比失败:', error);
            this.showError(error.message || '对比分析失败');
        }
    }

    displayComparisonResults(comparison) {
        const resultsDiv = document.getElementById('comparisonResults');
        
        // 更新基础对比数据
        document.getElementById('valueChange').textContent = 
            this.formatCurrency(comparison.value_change.absolute);
        document.getElementById('changeRate').textContent = 
            this.formatPercentage(comparison.value_change.rate);
        document.getElementById('timePeriod').textContent = 
            `${comparison.period.days}天`;

        // 添加正负颜色
        const valueChangeEl = document.getElementById('valueChange');
        const changeRateEl = document.getElementById('changeRate');
        
        [valueChangeEl, changeRateEl].forEach(el => {
            el.classList.remove('positive', 'negative');
            el.classList.add(comparison.value_change.absolute >= 0 ? 'positive' : 'negative');
        });

        // 更新详细对比数据
        const detailsDiv = document.getElementById('comparisonDetails');
        detailsDiv.innerHTML = this.generateComparisonDetails(comparison);

        resultsDiv.style.display = 'block';
    }

    generateComparisonDetails(comparison) {
        return `
            <h4>资产类型变化</h4>
            <div class="comparison-grid">
                ${Object.entries(comparison.type_changes || {}).map(([type, change]) => `
                    <div class="comparison-item">
                        <div class="comparison-label">${this.getAssetTypeName(type)}</div>
                        <div class="comparison-value ${change >= 0 ? 'positive' : 'negative'}">
                            ${this.formatCurrency(Math.abs(change))}
                            (${change >= 0 ? '+' : '-'}${this.formatPercentage(Math.abs(change / comparison.snapshot1.total_value))})
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // ==================== AI分析 ====================
    async loadAiConfig() {
        try {
            const response = await fetch('/api/ai/configs');
            const data = await response.json();
            
            if (data.success) {
                this.currentAiConfig = data.data.default_config;
                this.updateAiConfigDisplay();
            }
        } catch (error) {
            console.error('加载AI配置失败:', error);
        }
    }

    updateAiConfigDisplay() {
        const typeDisplay = document.getElementById('currentAiType');
        if (typeDisplay && this.currentAiConfig) {
            typeDisplay.textContent = this.currentAiConfig.ai_type === 'LOCAL' ? '本地AI' : '云端AI';
        }
    }

    showAiConfigModal() {
        // 预填充当前配置
        if (this.currentAiConfig) {
            document.querySelector(`input[name="aiType"][value="${this.currentAiConfig.ai_type}"]`).checked = true;
            this.toggleAiConfigSection(this.currentAiConfig.ai_type);
        }
        
        document.getElementById('aiConfigModal').style.display = 'flex';
    }

    hideAiConfigModal() {
        document.getElementById('aiConfigModal').style.display = 'none';
    }

    toggleAiConfigSection(aiType) {
        const localConfig = document.getElementById('localAiConfig');
        const cloudConfig = document.getElementById('cloudAiConfig');
        
        if (aiType === 'LOCAL') {
            localConfig.style.display = 'block';
            cloudConfig.style.display = 'none';
        } else {
            localConfig.style.display = 'none';
            cloudConfig.style.display = 'block';
        }
    }

    async saveAiConfig() {
        const aiType = document.querySelector('input[name="aiType"]:checked').value;
        const config = {
            ai_type: aiType,
            temperature: parseFloat(document.getElementById('aiTemperature').value),
            max_tokens: parseInt(document.getElementById('aiMaxTokens').value)
        };

        if (aiType === 'LOCAL') {
            config.local_model_name = document.getElementById('localModelName').value;
            config.local_api_port = parseInt(document.getElementById('localApiPort').value);
        } else {
            config.cloud_provider = document.getElementById('cloudProvider').value;
            config.cloud_api_key = document.getElementById('cloudApiKey').value;
            config.cloud_model_name = document.getElementById('cloudModelName').value;
        }

        try {
            const response = await fetch('/api/ai/configs/switch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.hideAiConfigModal();
                this.showSuccess('AI配置已更新');
                this.loadAiConfig();
            } else {
                throw new Error(data.message || '保存配置失败');
            }
        } catch (error) {
            console.error('保存AI配置失败:', error);
            this.showError(error.message || '保存配置失败');
        }
    }

    async analyzeWithAI() {
        if (!this.selectedSnapshots.snapshot1 || !this.selectedSnapshots.snapshot2) {
            this.showError('请先选择两个快照进行对比');
            return;
        }

        const statusDiv = document.getElementById('aiStatus');
        const resultsDiv = document.getElementById('aiAnalysisResults');
        const analyzeBtn = document.getElementById('aiAnalyzeBtn');
        
        // 显示加载状态
        statusDiv.style.display = 'flex';
        resultsDiv.style.display = 'none';
        analyzeBtn.disabled = true;

        try {
            const response = await fetch('/api/ai/analysis/snapshots', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    snapshot1_id: this.selectedSnapshots.snapshot1.snapshot_id,
                    snapshot2_id: this.selectedSnapshots.snapshot2.snapshot_id,
                    config_id: this.currentAiConfig?.config_id
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayAiAnalysisResults(data.data);
            } else {
                throw new Error(data.message || 'AI分析失败');
            }
        } catch (error) {
            console.error('AI分析失败:', error);
            this.showError(error.message || 'AI分析失败');
        } finally {
            statusDiv.style.display = 'none';
            analyzeBtn.disabled = false;
        }
    }

    displayAiAnalysisResults(analysis) {
        document.getElementById('analysisSummary').textContent = 
            analysis.analysis_summary || '暂无分析摘要';
        document.getElementById('investmentAdvice').textContent = 
            analysis.investment_advice || '暂无投资建议';
        document.getElementById('riskAssessment').textContent = 
            analysis.risk_assessment || '暂无风险评估';
        
        document.getElementById('aiAnalysisResults').style.display = 'block';
    }

    // ==================== 快照详情 ====================
    async viewSnapshotDetail(snapshotId) {
        try {
            const response = await fetch(`/api/snapshots/${snapshotId}`);
            const data = await response.json();
            
            if (data.success) {
                
                this.showSnapshotDetailModal(data.data.snapshot);
            } else {
                throw new Error(data.message || '获取快照详情失败');
            }
        } catch (error) {
            console.error('加载快照详情失败:', error);
            this.showError('获取快照详情失败');
        }
    }

    showSnapshotDetailModal(snapshot) {
        // 更新模态窗口标题
        document.getElementById('snapshotDetailTitle').textContent = 
            `快照详情 - ${this.formatDate(snapshot.snapshot_date)}`;

        // 更新基本信息
        document.getElementById('detailTotalValue').textContent = 
            this.formatCurrency(snapshot.total_value);
        document.getElementById('detailTotalCost').textContent = 
            this.formatCurrency(snapshot.total_cost);
        document.getElementById('detailTotalReturn').textContent = 
            this.formatCurrency(snapshot.total_return);
        document.getElementById('detailReturnRate').textContent = 
            this.formatPercentage(snapshot.total_return_rate);

        // 渲染资产配置
    
        this.renderSnapshotAllocation(snapshot.asset_allocation || {});
        // 更新持仓详情，传入总价值用于占比计算
        this.renderSnapshotPositions(snapshot.position_snapshots || [], snapshot.total_value);

        // 显示模态窗口
        document.getElementById('snapshotDetailModal').style.display = 'flex';
    }

    hideSnapshotDetailModal() {
        document.getElementById('snapshotDetailModal').style.display = 'none';
    }

    renderSnapshotPositions(positions, totalValue = 0) {
        const tbody = document.getElementById('snapshotPositionsBody');
        if (!tbody) return;
        // 调试输出，便于排查后端返回结构
        if (positions && positions.length > 0) {
            console.log('快照持仓详情原始数据:', positions);
        }
        tbody.innerHTML = positions.map(position => {
            // 优先从position.asset取值
            const assetName = (position.asset && (position.asset.asset_name || position.asset.name)) || position.asset_name || position.name || '未知';
            const assetType = (position.asset && (position.asset.asset_type || position.asset.type)) || position.asset_type || position.type || '未知';
            const currentValue = parseFloat(position.current_value ?? position.value ?? position.currentValue ?? 0);
            // 自动计算占比
            const allocation = totalValue > 0 ? (currentValue / totalValue) * 100 : 0;
            return `
                <tr>
                    <td>${assetName}</td>
                    <td>${this.getAssetTypeName(assetType)}</td>
                    <td>${this.formatCurrency(currentValue)}</td>
                    <td>${this.formatPercentage(allocation)}</td>
                </tr>
            `;
        }).join('');
    }

    // 渲染快照资产配置
    renderSnapshotAllocation(allocation) {
        const chartContainer = document.getElementById('snapshotAllocationChart');
        if (!chartContainer) return;
        // 调试输出
        console.log('快照资产配置原始数据:', allocation);
        // 清空旧图表
        if (this.snapshotAllocationChart) {
            this.snapshotAllocationChart.destroy();
        }
        // 统一将所有值转为数值类型
        const types = Object.keys(allocation);
        const values = types.map(t => parseFloat(allocation[t]) || 0);
        if (!types.length || !values.some(v => v > 0)) {
            chartContainer.parentElement.innerHTML = '<div style="text-align:center;color:#888;padding:32px 0;">暂无资产配置数据</div>';
            return;
        }
        // 资产类型中文名
        const typeNames = {
            'CASH': '现金及等价物',
            'FIXED_INCOME': '固定收益类',
            'EQUITY': '权益类',
            'REAL_ESTATE': '房地产',
            'COMMODITY': '商品'
        };
        // 颜色
        const colors = ['#60a5fa','#34d399','#fbbf24','#f472b6','#a78bfa','#f87171','#facc15'];
        // Chart.js 饼图
        this.snapshotAllocationChart = new Chart(chartContainer, {
            type: 'doughnut',
            data: {
                labels: types.map(t => typeNames[t] || t),
                datasets: [{
                    data: values,
                    backgroundColor: colors.slice(0, types.length),
                    borderWidth: 1
                }]
            },
            options: {
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            label: ctx => `${ctx.label}: ${ctx.raw}`
                        }
                    }
                },
                cutout: '60%',
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    // ==================== 删除快照 ====================
    async deleteSnapshot(snapshotId) {
        if (!confirm('确定要删除这个快照吗？删除后无法恢复。')) {
            return;
        }

        try {
            const response = await fetch(`/api/snapshots/${snapshotId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('快照已删除');
                this.loadSnapshots();
                // 如果删除的快照被选中用于对比，清除选择
                if (this.selectedSnapshots.snapshot1?.snapshot_id === snapshotId ||
                    this.selectedSnapshots.snapshot2?.snapshot_id === snapshotId) {
                    this.clearComparison();
                }
            } else {
                throw new Error(data.message || '删除快照失败');
            }
        } catch (error) {
            console.error('删除快照失败:', error);
            this.showError(error.message || '删除快照失败');
        }
    }

    /**
     * 分析快照
     * @param {string} snapshotId 快照ID
     */
    analyzeSnapshot(snapshotId) {
        // 打开AI分析页面，并传递快照ID
        window.location.href = `ai-analysis.html?snapshot_id=${snapshotId}`;
    }

    // ==================== 工具方法 ====================
    formatCurrency(amount) {
        return new Intl.NumberFormat('zh-CN', {
            style: 'currency',
            currency: 'CNY',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount || 0);
    }

    formatPercentage(rate) {
        return new Intl.NumberFormat('zh-CN', {
            style: 'percent',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format((rate || 0) / 100);
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('zh-CN');
    }

    parseCurrency(currencyString) {
        return parseFloat(currencyString.replace(/[¥,]/g, '')) || 0;
    }

    parsePercentage(percentageString) {
        return parseFloat(percentageString.replace('%', '')) || 0;
    }

    getAssetTypeName(type) {
        const typeNames = {
            'CASH': '现金及等价物',
            'FIXED_INCOME': '固定收益类',
            'EQUITY': '权益类',
            'REAL_ESTATE': '房地产',
            'COMMODITY': '商品'
        };
        return typeNames[type] || type;
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // 简单的通知实现，可以替换为更好的通知组件
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            transition: all 0.3s ease;
            background: ${type === 'success' ? '#059669' : type === 'error' ? '#dc2626' : '#3b82f6'};
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    updateSnapshotStats(stats) {
        const statsDiv = document.getElementById('snapshotStats');
        if (!statsDiv || !stats) return;
        statsDiv.innerHTML = `
            <span>总快照数：<b>${stats.total || 0}</b></span>
            <span style="margin-left:16px;">自动快照：<b>${stats.auto || 0}</b></span>
            <span style="margin-left:16px;">手动快照：<b>${stats.manual || 0}</b></span>
            <span style="margin-left:16px;">最新快照：<b>${stats.latest_date || '--'}</b></span>
        `;
    }
}

// 初始化投资组合管理器
let portfolioManager;

document.addEventListener('DOMContentLoaded', () => {
    portfolioManager = new PortfolioManager();
});

// 导出全局引用
window.portfolioManager = portfolioManager; 
window.portfolioManager = portfolioManager; 