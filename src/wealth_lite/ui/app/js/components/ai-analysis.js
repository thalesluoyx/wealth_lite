/**
 * AI分析组件
 * 
 * 功能：
 * 1. AI配置管理（API Key设置、模型选择）
 * 2. 快照分析（单个快照分析）
 * 3. 多轮对话交互
 * 4. 分析结果展示
 * 5. PDF报告导出
 */

import { formatCurrency } from '../utils.js';

// 注释掉jsPDF导入，改为使用全局变量
// import { jsPDF } from 'jspdf';
// import 'jspdf-autotable';

class AIAnalysisManager {
    constructor() {
        this.apiKey = localStorage.getItem('openrouter_api_key') || '';
        this.selectedModel = localStorage.getItem('ai_model') || 'deepseek/deepseek-chat-v3-0324:free:online';
        this.currentConversationId = null;
        this.currentSnapshotId = null;
        this.analysisResult = null;
        this.isAnalyzing = false;
        this.conversationHistory = [];
        
        // 系统提示类型和用户提示类型
        this.systemPromptType = localStorage.getItem('system_prompt_type') || 'default';
        this.userPromptType = localStorage.getItem('user_prompt_type') || 'default';
        
        // 从URL参数获取快照ID
        this.urlParams = new URLSearchParams(window.location.search);
        this.urlSnapshotId = this.urlParams.get('snapshot_id');
        
        // 绑定DOM元素
        this.bindElements();
        
        // 初始化事件监听
        this.initEventListeners();
        
        // 初始化AI配置
        this.loadAIConfigs();
    }
    
    /**
     * 绑定DOM元素
     */
    bindElements() {
        // AI配置面板
        this.configPanel = document.getElementById('ai-config-panel');
        this.apiKeyInput = document.getElementById('ai-api-key');
        this.modelSelect = document.getElementById('ai-model-select');
        this.saveConfigBtn = document.getElementById('save-ai-config');
        
        // 系统提示类型和用户提示类型选择
        this.systemPromptTypeSelect = document.getElementById('system-prompt-type');
        this.userPromptTypeSelect = document.getElementById('user-prompt-type');
        
        // 分析控制面板
        this.snapshotSelect = document.getElementById('snapshot-select');
        this.promptInput = document.getElementById('ai-prompt-input');
        this.analyzeBtn = document.getElementById('analyze-btn');
        
        // 结果展示区
        this.resultPanel = document.getElementById('ai-result-panel');
        
        // 基本信息部分
        this.basicInfoSummary = document.getElementById('basic-info-summary');
        this.basicInfoContent = document.getElementById('basic-info-content');
        
        // 投资组合概览部分
        this.analysisSummary = document.getElementById('analysis-summary');
        this.portfolioOverviewContent = document.getElementById('portfolio-overview-content');
        
        // 风险评估部分
        this.riskAssessmentSummary = document.getElementById('risk-assessment-summary');
        this.riskAssessmentContent = document.getElementById('risk-assessment-content');
        
        // 投资建议部分
        this.investmentAdviceSummary = document.getElementById('investment-advice-summary');
        this.investmentAdviceContent = document.getElementById('investment-advice-content');
        
        // 切换按钮
        this.toggleButtons = document.querySelectorAll('.toggle-btn');
        
        // 进度指示器
        this.progressIndicator = document.getElementById('analysis-progress');
        
        // 对话区
        this.conversationPanel = document.getElementById('conversation-panel');
        this.messagesList = document.getElementById('messages-list');
        this.userMessageInput = document.getElementById('user-message');
        this.sendMessageBtn = document.getElementById('send-message-btn');
        this.clearConversationBtn = document.getElementById('clear-conversation-btn');
        
        // 导出按钮
        this.exportPdfBtn = document.getElementById('export-pdf-btn');
    }
    
    /**
     * 初始化事件监听
     */
    initEventListeners() {
        // AI配置保存
        if (this.saveConfigBtn) {
            this.saveConfigBtn.addEventListener('click', () => this.saveAIConfig());
        }
        
        // 分析按钮
        if (this.analyzeBtn) {
            this.analyzeBtn.addEventListener('click', () => this.startAnalysis());
        }
        
        // 比较模式切换
        if (this.compareToggle) {
            this.compareToggle.addEventListener('change', (e) => {
                this.isCompareMode = e.target.checked;
                this.toggleCompareMode(this.isCompareMode);
            });
        }
        
        // 系统提示类型和用户提示类型选择
        if (this.systemPromptTypeSelect) {
            this.systemPromptTypeSelect.addEventListener('change', (e) => {
                this.systemPromptType = e.target.value;
                localStorage.setItem('system_prompt_type', this.systemPromptType);
            });
        }
        
        if (this.userPromptTypeSelect) {
            this.userPromptTypeSelect.addEventListener('change', (e) => {
                this.userPromptType = e.target.value;
                localStorage.setItem('user_prompt_type', this.userPromptType);
            });
        }
        
        // 初始化展开/收起按钮
        this.initToggleButtons();
        
        // 发送消息
        if (this.sendMessageBtn) {
            this.sendMessageBtn.addEventListener('click', () => this.sendUserMessage());
        }
        
        // 用户消息输入框回车发送
        if (this.userMessageInput) {
            this.userMessageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendUserMessage();
                }
            });
        }
        
        // 清除对话
        if (this.clearConversationBtn) {
            this.clearConversationBtn.addEventListener('click', () => this.clearConversation());
        }
        
        // 导出PDF
        if (this.exportPdfBtn) {
            this.exportPdfBtn.addEventListener('click', () => this.exportToPdf());
        }
    }
    
    /**
     * 初始化展开/收起按钮
     */
    initToggleButtons() {
        if (!this.toggleButtons) {
            this.toggleButtons = document.querySelectorAll('.toggle-btn');
        }
        
        this.toggleButtons.forEach(button => {
            button.addEventListener('click', () => {
                const section = button.getAttribute('data-section');
                const content = document.getElementById(`${section}-content`);
                
                if (content) {
                    if (content.style.display === 'none') {
                        content.style.display = 'block';
                        button.textContent = '收起';
                    } else {
                        content.style.display = 'none';
                        button.textContent = '展开';
                    }
                }
            });
        });
    }
    
    /**
     * 加载AI配置
     */
    async loadAIConfigs() {
        try {
            // 从后端获取AI配置
            const response = await fetch('/api/ai/configs');
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || '获取AI配置失败');
            }
            
            const configs = data.data?.configs || [];
            
            // 获取默认配置
            let defaultConfig = null;
            if (Array.isArray(configs) && configs.length > 0) {
                defaultConfig = configs.find(config => config.is_default) || configs[0];
            }
            
            if (defaultConfig) {
                // 自动使用默认配置
                this.apiKey = defaultConfig.cloud_api_key || this.apiKey;
                this.selectedModel = defaultConfig.cloud_model_name || this.selectedModel;
                
                // 更新localStorage
                localStorage.setItem('openrouter_api_key', this.apiKey);
                localStorage.setItem('ai_model', this.selectedModel);
            }
            
            // 填充模型选择下拉框
            if (this.modelSelect) {
                this.modelSelect.innerHTML = '';
                
                // 添加OpenRouter模型
                const openRouterGroup = document.createElement('optgroup');
                openRouterGroup.label = 'OpenRouter模型';
                
                const deepseekOption = document.createElement('option');
                deepseekOption.value = 'deepseek/deepseek-chat-v3-0324:free:online';
                deepseekOption.textContent = 'DeepSeek Chat v3';
                deepseekOption.selected = this.selectedModel === 'deepseek/deepseek-chat-v3-0324:free:online';
                openRouterGroup.appendChild(deepseekOption);
                
                const qwenOption = document.createElement('option');
                qwenOption.value = 'qwen/qwen3-235b-a22b:free';
                qwenOption.textContent = 'Qwen 3 (235B)';
                qwenOption.selected = this.selectedModel === 'qwen/qwen3-235b-a22b:free';
                openRouterGroup.appendChild(qwenOption);
                
                this.modelSelect.appendChild(openRouterGroup);
                
                // 添加本地模型（如果有）
                if (Array.isArray(configs) && configs.some(c => c.ai_type === 'LOCAL')) {
                    const localGroup = document.createElement('optgroup');
                    localGroup.label = '本地模型';
                    
                    configs.filter(c => c.ai_type === 'LOCAL').forEach(config => {
                        const option = document.createElement('option');
                        option.value = `local:${config.local_model_name}`;
                        option.textContent = config.config_name;
                        option.selected = this.selectedModel === `local:${config.local_model_name}`;
                        localGroup.appendChild(option);
                    });
                    
                    this.modelSelect.appendChild(localGroup);
                }
            }
            
            // 填充API Key
            if (this.apiKeyInput) {
                this.apiKeyInput.value = this.apiKey;
            }
            
            // 加载提示类型选项
            await this.loadPromptTypes();
            
            // 加载快照选择
            this.loadSnapshots();
            
        } catch (error) {
            console.error('加载AI配置失败:', error);
            this.showNotification('加载AI配置失败', 'error');
            
            // 即使配置加载失败，也尝试加载快照
            this.loadSnapshots();
        }
    }
    
    /**
     * 加载提示类型选项
     */
    async loadPromptTypes() {
        try {
            // 从后端获取提示类型
            const response = await fetch('/api/ai/prompt-types');
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || '获取提示类型失败');
            }
            
            const promptTypes = data.data || {};
            
            // 填充系统提示类型选择
            if (this.systemPromptTypeSelect && promptTypes.system_prompts) {
                this.systemPromptTypeSelect.innerHTML = '';
                
                Object.entries(promptTypes.system_prompts).forEach(([key, name]) => {
                    const option = document.createElement('option');
                    option.value = key;
                    option.textContent = name;
                    option.selected = this.systemPromptType === key;
                    this.systemPromptTypeSelect.appendChild(option);
                });
            }
            
            // 填充用户提示类型选择
            if (this.userPromptTypeSelect && promptTypes.user_prompts) {
                this.userPromptTypeSelect.innerHTML = '';
                
                Object.entries(promptTypes.user_prompts).forEach(([key, name]) => {
                    const option = document.createElement('option');
                    option.value = key;
                    option.textContent = name;
                    option.selected = this.userPromptType === key;
                    this.userPromptTypeSelect.appendChild(option);
                });
            }
            
        } catch (error) {
            console.error('加载提示类型失败:', error);
        }
    }
    
    /**
     * 加载快照列表
     */
    async loadSnapshots() {
        try {
            // 从后端获取快照列表
            const response = await fetch('/api/snapshots');
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || '获取快照列表失败');
            }
            
            const snapshots = data.data?.snapshots || [];
            
            // 填充快照选择下拉框
            if (this.snapshotSelect) {
                this.snapshotSelect.innerHTML = '';
                
                // 添加一个空选项
                const emptyOption = document.createElement('option');
                emptyOption.value = '';
                emptyOption.textContent = '-- 选择要分析的快照 --';
                this.snapshotSelect.appendChild(emptyOption);
                
                snapshots.forEach(snapshot => {
                    const option = document.createElement('option');
                    option.value = snapshot.snapshot_id;
                    const date = new Date(snapshot.snapshot_date);
                    const formattedDate = date.toLocaleDateString('zh-CN');
                    option.textContent = `${formattedDate} - ${formatCurrency(snapshot.total_value)}`;
                    
                    // 如果URL中有快照ID，则自动选择该快照
                    if (this.urlSnapshotId && this.urlSnapshotId === snapshot.snapshot_id) {
                        option.selected = true;
                        this.currentSnapshotId = snapshot.snapshot_id;
                    }
                    
                    this.snapshotSelect.appendChild(option);
                });
                
                // 如果URL中有快照ID但没有匹配的快照，则默认选择最新的快照
                if (this.urlSnapshotId && !this.currentSnapshotId && snapshots.length > 0) {
                    this.currentSnapshotId = snapshots[0].snapshot_id;
                    this.snapshotSelect.value = this.currentSnapshotId;
                }
            }
            
            // 如果URL中有快照ID，则选择该快照但不自动开始分析
            if (this.urlSnapshotId && this.currentSnapshotId) {
                // 设置默认提示
                if (this.promptInput) {
                    this.promptInput.value = '分析我的投资组合风险水平和资产配置是否合理';
                }
                
                // 不再自动开始分析，让用户手动点击"开始分析"按钮
                console.log('已选择快照，等待用户点击"开始分析"按钮');
            }
            
        } catch (error) {
            console.error('加载快照列表失败:', error);
            this.showNotification('加载快照列表失败', 'error');
        }
    }
    
    /**
     * 保存AI配置
     */
    saveAIConfig() {
        if (this.apiKeyInput && this.modelSelect) {
            const newApiKey = this.apiKeyInput.value.trim();
            const newModel = this.modelSelect.value;
            
            // 保存到localStorage
            localStorage.setItem('openrouter_api_key', newApiKey);
            localStorage.setItem('ai_model', newModel);
            
            // 更新当前值
            this.apiKey = newApiKey;
            this.selectedModel = newModel;
            
            // 显示成功通知
            this.showNotification('AI配置已保存', 'success');
        }
    }
    
    /**
     * 更新后端AI配置
     */
    async updateBackendConfig() {
        try {
            // 准备配置数据
            const configData = {
                cloud_api_key: this.apiKey,
                cloud_model_name: this.selectedModel.startsWith('local:') ? '' : this.selectedModel,
                local_model_name: this.selectedModel.startsWith('local:') ? this.selectedModel.split(':')[1] : '',
                ai_type: this.selectedModel.startsWith('local:') ? 'LOCAL' : 'CLOUD'
            };
            
            // 调用后端API更新配置
            const response = await fetch('/api/ai/configs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(configData)
            });
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || '更新AI配置失败');
            }
            
            return data.data.config_id;
            
        } catch (error) {
            console.error('更新AI配置失败:', error);
            this.showNotification('更新AI配置失败', 'error');
            return null;
        }
    }
    
    /**
     * 获取选中的配置ID
     */
    getSelectedConfigId() {
        // 如果有API Key，则使用自定义配置
        if (this.apiKey) {
            return 'custom';
        }
        
        // 否则使用默认配置
        return 'default';
    }
    
    /**
     * 开始分析
     */
    async startAnalysis() {
        if (this.isAnalyzing) return;
        
        // 获取选中的快照ID
        const snapshotId = this.snapshotSelect ? this.snapshotSelect.value : this.currentSnapshotId;
        if (!snapshotId) {
            this.showNotification('请选择要分析的快照', 'warning');
            return;
        }
        
        // 获取用户提示
        const userPrompt = this.promptInput ? this.promptInput.value.trim() : '';
        
        // 设置分析状态
        this.isAnalyzing = true;
        this.showAnalyzingState(true);
        
        try {
            // 更新后端配置
            const configId = await this.updateBackendConfig();
            
            // 准备分析请求数据
            const analysisData = {
                snapshot1_id: snapshotId,
                config_id: configId,  // 添加配置ID
                user_prompt: userPrompt,
                api_key: this.apiKey,
                model: this.selectedModel,
                system_prompt_type: this.systemPromptType,
                user_prompt_type: this.userPromptType
            };
            
            // 调用后端API进行分析
            const response = await fetch('/api/ai/analysis/snapshots', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(analysisData)
            });
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || '分析失败');
            }
            
            // 保存分析结果
            this.analysisResult = data.data;
            this.currentConversationId = data.data.conversation_id;
            
            // 显示分析结果
            this.displayAnalysisResult(this.analysisResult);
            
            // 更新对话历史
            this.loadConversationHistory();
            
        } catch (error) {
            console.error('分析失败:', error);
            this.showNotification(`分析失败: ${error.message}`, 'error');
        } finally {
            // 重置分析状态
            this.isAnalyzing = false;
            this.showAnalyzingState(false);
        }
    }
    
    /**
     * 显示分析中状态
     */
    showAnalyzingState(isAnalyzing) {
        if (this.analyzeBtn) {
            this.analyzeBtn.disabled = isAnalyzing;
            this.analyzeBtn.textContent = isAnalyzing ? '分析中...' : '开始分析';
        }
        
        // 显示或隐藏进度指示器
        if (this.progressIndicator) {
            this.progressIndicator.style.display = isAnalyzing ? 'flex' : 'none';
        }
    }
    
    /**
     * 显示分析结果
     */
    displayAnalysisResult(result) {
        if (!this.resultPanel || !result) {
            return;
        }
        
        // 保存分析结果
        this.analysisResult = result;
        
        // 显示结果面板
        this.resultPanel.style.display = 'block';
        
        // 1. 更新基本信息部分
        if (this.basicInfoSummary) {
            const basicInfo = this.generateBasicInfoSummary(result);
            this.basicInfoSummary.textContent = basicInfo;
        }
        
        if (this.basicInfoContent) {
            // 直接从快照数据生成基本信息，不使用AI生成的内容
            const basicInfoDetail = this.generateBasicInfoDetail(result);
            this.basicInfoContent.innerHTML = marked.parse(basicInfoDetail);
            // 确保基本信息内容默认隐藏
            this.basicInfoContent.style.display = 'none';
            
            // 确保对应的展开按钮显示"展开"
            const basicInfoToggleBtn = document.querySelector('[data-section="basic-info"]');
            if (basicInfoToggleBtn) {
                basicInfoToggleBtn.textContent = '展开';
            }
        }
        
        // 2. 更新投资组合概览部分
        if (this.analysisSummary && result.analysis_summary) {
            this.analysisSummary.textContent = result.analysis_summary;
        }
        
        if (this.portfolioOverviewContent) {
            // 从完整分析内容中提取投资组合概览部分
            const overviewContent = this.extractSectionFromAnalysis(result.analysis_content, '投资组合概览');
            // 使用marked.parse来正确渲染markdown内容
            this.portfolioOverviewContent.innerHTML = marked.parse(overviewContent || '');
            // 确保内容默认隐藏
            this.portfolioOverviewContent.style.display = 'none';
            
            // 确保对应的展开按钮显示"展开"
            const overviewToggleBtn = document.querySelector('[data-section="portfolio-overview"]');
            if (overviewToggleBtn) {
                overviewToggleBtn.textContent = '展开';
            }
        }
        
        // 3. 更新风险评估部分
        if (this.riskAssessmentSummary && result.risk_assessment) {
            this.riskAssessmentSummary.textContent = result.risk_assessment;
        }
        
        if (this.riskAssessmentContent) {
            // 从完整分析内容中提取风险评估部分
            const riskContent = this.extractSectionFromAnalysis(result.analysis_content, '风险评估');
            this.riskAssessmentContent.innerHTML = marked.parse(riskContent || '');
            // 确保内容默认隐藏
            this.riskAssessmentContent.style.display = 'none';
            
            // 确保对应的展开按钮显示"展开"
            const riskToggleBtn = document.querySelector('[data-section="risk-assessment"]');
            if (riskToggleBtn) {
                riskToggleBtn.textContent = '展开';
            }
        }
        
        // 4. 更新投资建议部分
        if (this.investmentAdviceSummary && result.investment_advice) {
            this.investmentAdviceSummary.textContent = result.investment_advice;
        }
        
        if (this.investmentAdviceContent) {
            // 从完整分析内容中提取投资建议部分
            const adviceContent = this.extractSectionFromAnalysis(result.analysis_content, '投资建议');
            this.investmentAdviceContent.innerHTML = marked.parse(adviceContent || '');
            // 确保内容默认隐藏
            this.investmentAdviceContent.style.display = 'none';
            
            // 确保对应的展开按钮显示"展开"
            const adviceToggleBtn = document.querySelector('[data-section="investment-advice"]');
            if (adviceToggleBtn) {
                adviceToggleBtn.textContent = '展开';
            }
        }
        
        // 显示对话面板
        if (this.conversationPanel) {
            this.conversationPanel.style.display = 'block';
        }
        
        // 滚动到结果区域
        this.resultPanel.scrollIntoView({ behavior: 'smooth' });
    }
    
    /**
     * 生成基本信息摘要
     */
    generateBasicInfoSummary(result) {
        if (!result.snapshot_date || !result.total_value) {
            return '基本信息不可用';
        }
        
        const date = new Date(result.snapshot_date).toLocaleDateString('zh-CN');
        const totalValue = formatCurrency(result.total_value);
        const returnRate = result.total_return_rate ? `${(result.total_return_rate * 100).toFixed(2)}%` : 'N/A';
        
        return `快照日期: ${date}, 总资产: ${totalValue}, 总收益率: ${returnRate}`;
    }
    
    /**
     * 生成基本信息详情
     */
    generateBasicInfoDetail(result) {
        if (!result.snapshot_date || !result.total_value) {
            return '# 基本信息\n\n基本信息不可用';
        }
        
        const date = new Date(result.snapshot_date).toLocaleDateString('zh-CN');
        const totalValue = formatCurrency(result.total_value);
        const totalCost = result.total_cost ? formatCurrency(result.total_cost) : 'N/A';
        const totalReturn = result.total_return ? formatCurrency(result.total_return) : 'N/A';
        const returnRate = result.total_return_rate ? `${(result.total_return_rate * 100).toFixed(2)}%` : 'N/A';
        
        let markdown = `# 投资组合基本信息\n\n`;
        markdown += `- **快照日期**: ${date}\n`;
        markdown += `- **总资产**: ${totalValue}\n`;
        markdown += `- **总成本**: ${totalCost}\n`;
        markdown += `- **总收益**: ${totalReturn}\n`;
        markdown += `- **总收益率**: ${returnRate}\n\n`;
        
        // 如果有资产配置信息，添加资产配置
        if (result.asset_allocation) {
            markdown += `## 资产配置\n\n`;
            
            // 直接从快照数据中获取资产配置信息
            const allocation = result.asset_allocation;
            
            if (typeof allocation === 'object') {
                // 如果是对象形式，直接使用
                const cash = allocation.cash || 0;
                const fixedIncome = allocation.fixed_income || 0;
                const equity = allocation.equity || 0;
                const realEstate = allocation.real_estate || 0;
                const commodity = allocation.commodity || 0;
                
                markdown += `- **现金**: ${formatCurrency(cash)} (${this.calculatePercentage(cash, result.total_value)})\n`;
                markdown += `- **固定收益**: ${formatCurrency(fixedIncome)} (${this.calculatePercentage(fixedIncome, result.total_value)})\n`;
                markdown += `- **股票**: ${formatCurrency(equity)} (${this.calculatePercentage(equity, result.total_value)})\n`;
                markdown += `- **房地产**: ${formatCurrency(realEstate)} (${this.calculatePercentage(realEstate, result.total_value)})\n`;
                markdown += `- **商品**: ${formatCurrency(commodity)} (${this.calculatePercentage(commodity, result.total_value)})\n`;
            }
        }
        
        // 添加持仓数量信息
        if (result.position_snapshots) {
            markdown += `\n## 持仓信息\n\n`;
            markdown += `- **持仓数量**: ${result.position_snapshots.length}个\n`;
        }
        
        return markdown;
    }
    
    /**
     * 计算百分比
     */
    calculatePercentage(value, total) {
        if (!value || !total || total === 0) {
            return '0%';
        }
        return `${((value / total) * 100).toFixed(2)}%`;
    }
    
    /**
     * 从分析内容中提取特定部分
     */
    extractSectionFromAnalysis(content, sectionName) {
        if (!content) {
            return '';
        }
        
        // 尝试找到该部分的标题
        const regex = new RegExp(`(#+)\\s*${sectionName}[\\s\\S]*?((?=#+\\s*[^#])|$)`, 'i');
        const match = content.match(regex);
        
        if (match && match[0]) {
            return match[0].trim();
        }
        
        return '';
    }
    
    /**
     * 加载对话历史
     */
    async loadConversationHistory() {
        if (!this.currentConversationId) {
            return;
        }
        
        try {
            // 从后端获取对话历史
            const response = await fetch(`/api/ai/conversation/${this.currentConversationId}`);
            const history = await response.json();
            
            // 更新对话历史
            this.conversationHistory = history;
            
            // 显示对话历史
            this.displayConversationHistory();
            
        } catch (error) {
            console.error('加载对话历史失败:', error);
        }
    }
    
    /**
     * 显示对话历史
     */
    displayConversationHistory() {
        if (!this.messagesList) {
            return;
        }
        
        // 清空消息列表
        this.messagesList.innerHTML = '';
        
        // 添加历史消息
        this.conversationHistory.forEach(message => {
            const messageElement = document.createElement('div');
            messageElement.className = `message ${message.role === 'user' ? 'user-message' : 'ai-message'}`;
            
            const contentElement = document.createElement('div');
            contentElement.className = 'message-content';
            
            // 使用marked.js渲染Markdown（对于AI消息）
            if (message.role === 'assistant') {
                contentElement.innerHTML = marked.parse(message.content);
            } else {
                contentElement.textContent = message.content;
            }
            
            messageElement.appendChild(contentElement);
            this.messagesList.appendChild(messageElement);
        });
        
        // 滚动到底部
        this.messagesList.scrollTop = this.messagesList.scrollHeight;
    }
    
    /**
     * 发送用户消息
     */
    async sendUserMessage() {
        if (!this.userMessageInput || !this.currentConversationId) {
            return;
        }
        
        const message = this.userMessageInput.value.trim();
        if (!message) {
            return;
        }
        
        // 清空输入框
        this.userMessageInput.value = '';
        
        // 添加用户消息到UI
        this.addMessageToUI('user', message);
        
        try {
            // 显示AI正在输入状态
            this.addTypingIndicator();
            
            // 发送消息到后端
            const response = await fetch('/api/ai/conversation/continue', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    conversation_id: this.currentConversationId,
                    message: message
                })
            });
            
            if (!response.ok) {
                throw new Error(`发送失败: ${response.statusText}`);
            }
            
            // 解析结果
            const result = await response.json();
            
            // 移除输入指示器
            this.removeTypingIndicator();
            
            // 添加AI回复到UI
            this.addMessageToUI('assistant', result.response);
            
        } catch (error) {
            console.error('发送消息失败:', error);
            this.showNotification('发送消息失败: ' + error.message, 'error');
            
            // 移除输入指示器
            this.removeTypingIndicator();
        }
    }
    
    /**
     * 添加消息到UI
     */
    addMessageToUI(role, content) {
        if (!this.messagesList) {
            return;
        }
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${role === 'user' ? 'user-message' : 'ai-message'}`;
        
        const contentElement = document.createElement('div');
        contentElement.className = 'message-content';
        
        // 使用marked.js渲染Markdown（对于AI消息）
        if (role === 'assistant') {
            contentElement.innerHTML = marked.parse(content);
        } else {
            contentElement.textContent = content;
        }
        
        messageElement.appendChild(contentElement);
        this.messagesList.appendChild(messageElement);
        
        // 滚动到底部
        this.messagesList.scrollTop = this.messagesList.scrollHeight;
        
        // 添加到历史记录
        this.conversationHistory.push({ role, content });
    }
    
    /**
     * 添加正在输入指示器
     */
    addTypingIndicator() {
        if (!this.messagesList) {
            return;
        }
        
        const indicatorElement = document.createElement('div');
        indicatorElement.className = 'message ai-message typing-indicator';
        indicatorElement.id = 'typing-indicator';
        
        const dotContainer = document.createElement('div');
        dotContainer.className = 'typing-dots';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            dot.className = 'typing-dot';
            dotContainer.appendChild(dot);
        }
        
        indicatorElement.appendChild(dotContainer);
        this.messagesList.appendChild(indicatorElement);
        
        // 滚动到底部
        this.messagesList.scrollTop = this.messagesList.scrollHeight;
    }
    
    /**
     * 移除正在输入指示器
     */
    removeTypingIndicator() {
        if (!this.messagesList) {
            return;
        }
        
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    /**
     * 清除对话
     */
    async clearConversation() {
        if (!this.currentConversationId) {
            return;
        }
        
        try {
            // 发送清除请求到后端
            const response = await fetch(`/api/ai/conversation/${this.currentConversationId}/clear`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`清除失败: ${response.statusText}`);
            }
            
            // 清空对话历史
            this.conversationHistory = [];
            
            // 清空UI
            if (this.messagesList) {
                this.messagesList.innerHTML = '';
            }
            
            // 显示成功通知
            this.showNotification('对话已清除', 'success');
            
        } catch (error) {
            console.error('清除对话失败:', error);
            this.showNotification('清除对话失败: ' + error.message, 'error');
        }
    }
    
    /**
     * 导出为PDF
     */
    exportToPdf() {
        if (!this.analysisResult) {
            this.showNotification('没有分析结果可导出', 'warning');
            return;
        }
        
        try {
            // 使用全局变量jspdf
            if (typeof jspdf === 'undefined') {
                this.showNotification('PDF导出功能不可用，请确保已加载jsPDF库', 'error');
                return;
            }
            
            // 创建PDF文档
            const doc = new jspdf.jsPDF();
            
            // 添加标题
            doc.setFontSize(18);
            doc.text('投资组合AI分析报告', 105, 20, { align: 'center' });
            
            // 添加生成时间
            doc.setFontSize(10);
            doc.text(`生成时间: ${new Date().toLocaleString()}`, 105, 30, { align: 'center' });
            
            // 1. 添加基本信息
            let yPos = 40;
            doc.setFontSize(14);
            doc.text('1. 投资组合基本信息', 20, yPos);
            doc.setFontSize(12);
            
            const basicInfo = this.generateBasicInfoSummary(this.analysisResult);
            doc.text(basicInfo, 20, yPos + 10, {
                maxWidth: 170
            });
            
            // 2. 添加投资组合概览
            yPos += 30;
            doc.setFontSize(14);
            doc.text('2. 投资组合概览', 20, yPos);
            doc.setFontSize(12);
            doc.text(this.analysisResult.analysis_summary || '无概览信息', 20, yPos + 10, {
                maxWidth: 170
            });
            
            // 3. 添加风险评估
            yPos += 40;
            doc.setFontSize(14);
            doc.text('3. 风险评估', 20, yPos);
            doc.setFontSize(12);
            doc.text(this.analysisResult.risk_assessment || '无风险评估', 20, yPos + 10, {
                maxWidth: 170
            });
            
            // 4. 添加投资建议
            yPos += 40;
            doc.setFontSize(14);
            doc.text('4. 投资建议', 20, yPos);
            doc.setFontSize(12);
            doc.text(this.analysisResult.investment_advice || '无投资建议', 20, yPos + 10, {
                maxWidth: 170
            });
            
            // 添加对话历史（如果有）
            if (this.conversationHistory && this.conversationHistory.length > 0) {
                // 添加新页面
                doc.addPage();
                
                doc.setFontSize(16);
                doc.text('对话历史', 105, 20, { align: 'center' });
                
                let chatYPos = 40;
                this.conversationHistory.forEach((message, index) => {
                    // 如果页面空间不足，添加新页面
                    if (chatYPos > 250) {
                        doc.addPage();
                        chatYPos = 20;
                    }
                    
                    const role = message.role === 'user' ? '用户' : 'AI';
                    const roleColor = message.role === 'user' ? '#0d47a1' : '#333333';
                    
                    // 设置角色颜色
                    doc.setTextColor(roleColor);
                    doc.setFontSize(11);
                    doc.text(`${role}:`, 20, chatYPos);
                    
                    // 恢复默认颜色
                    doc.setTextColor('#000000');
                    doc.setFontSize(10);
                    
                    // 处理可能的多行内容
                    const content = message.content || '';
                    const contentLines = doc.splitTextToSize(content, 160);
                    
                    doc.text(contentLines, 30, chatYPos);
                    
                    // 更新Y位置，为下一条消息腾出空间
                    chatYPos += 10 + (contentLines.length * 5);
                });
            }
            
            // 保存PDF
            doc.save('投资组合分析报告.pdf');
            
            // 显示成功通知
            this.showNotification('PDF报告已导出', 'success');
            
        } catch (error) {
            console.error('导出PDF失败:', error);
            this.showNotification('导出PDF失败: ' + error.message, 'error');
        }
    }
    
    /**
     * 显示通知
     */
    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // 添加到文档
        document.body.appendChild(notification);
        
        // 显示通知
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // 自动关闭
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
}

export default AIAnalysisManager; 