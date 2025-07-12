/**
 * AI分析组件
 * 
 * 功能：
 * 1. AI配置管理（API Key设置、模型选择）
 * 2. 快照分析（单个快照分析、快照对比分析）
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
        this.secondSnapshotId = null;
        this.analysisResult = null;
        this.isCompareMode = false;
        this.isAnalyzing = false;
        this.conversationHistory = [];
        
        // 系统提示类型和用户提示类型
        this.systemPromptType = localStorage.getItem('system_prompt_type') || 'default';
        this.userPromptType = localStorage.getItem('user_prompt_type') || 'default';
        
        // 从URL参数获取快照ID
        this.urlParams = new URLSearchParams(window.location.search);
        this.urlSnapshotId = this.urlParams.get('snapshot_id');
        this.urlCompareSnapshotId = this.urlParams.get('compare_snapshot_id');
        
        // 如果URL中有对比快照ID，则设置为对比模式
        if (this.urlCompareSnapshotId) {
            this.isCompareMode = true;
            this.secondSnapshotId = this.urlCompareSnapshotId;
        }
        
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
        this.compareSnapshotSelect = document.getElementById('compare-snapshot-select');
        this.compareToggle = document.getElementById('compare-mode-toggle');
        this.promptInput = document.getElementById('ai-prompt-input');
        this.analyzeBtn = document.getElementById('analyze-btn');
        
        // 结果展示区
        this.resultPanel = document.getElementById('ai-result-panel');
        this.analysisContent = document.getElementById('analysis-content');
        this.summarySection = document.getElementById('analysis-summary');
        this.adviceSection = document.getElementById('investment-advice');
        this.riskSection = document.getElementById('risk-assessment');
        
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
            const response = await fetch('/api/snapshots?type=all&limit=50');
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || '获取快照列表失败');
            }
            
            const snapshots = data.data.snapshots || [];
            
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
            
            // 填充比较快照选择下拉框
            if (this.compareSnapshotSelect) {
                this.compareSnapshotSelect.innerHTML = '';
                
                // 添加一个空选项
                const emptyOption = document.createElement('option');
                emptyOption.value = '';
                emptyOption.textContent = '-- 选择比较快照 --';
                this.compareSnapshotSelect.appendChild(emptyOption);
                
                snapshots.forEach(snapshot => {
                    const option = document.createElement('option');
                    option.value = snapshot.snapshot_id;
                    const date = new Date(snapshot.snapshot_date);
                    const formattedDate = date.toLocaleDateString('zh-CN');
                    option.textContent = `${formattedDate} - ${formatCurrency(snapshot.total_value)}`;
                    
                    // 如果URL中有对比快照ID，则自动选择该快照
                    if (this.urlCompareSnapshotId && this.urlCompareSnapshotId === snapshot.snapshot_id) {
                        option.selected = true;
                        this.secondSnapshotId = snapshot.snapshot_id;
                    }
                    
                    this.compareSnapshotSelect.appendChild(option);
                });
                
                // 设置比较模式
                this.toggleCompareMode(this.isCompareMode);
            }
            
            // 如果URL中有快照ID，则自动开始分析
            if (this.urlSnapshotId && this.currentSnapshotId) {
                // 设置默认提示
                if (this.promptInput) {
                    if (this.isCompareMode && this.secondSnapshotId) {
                        this.promptInput.value = '分析这两个快照之间的资产配置变化和收益情况';
                    } else {
                        this.promptInput.value = '分析我的投资组合风险水平和资产配置是否合理';
                    }
                }
                
                // 延迟一点时间后自动开始分析
                setTimeout(() => {
                    this.startAnalysis();
                }, 500);
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
            
            // 确保使用云端AI
            const switchResponse = await fetch('/api/ai/configs/switch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ai_type: 'CLOUD' })
            });
            
            const switchData = await switchResponse.json();
            
            if (!switchData.success) {
                throw new Error(switchData.message || '切换AI类型失败');
            }
            
            return switchData.data.config_id;
            
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
     * 切换比较模式
     */
    toggleCompareMode(enabled) {
        if (this.compareSnapshotSelect) {
            this.compareSnapshotSelect.style.display = enabled ? 'block' : 'none';
        }
        
        // 如果是从URL参数中获取的对比模式，则设置compareToggle的状态
        if (this.compareToggle) {
            this.compareToggle.checked = enabled;
        }
        
        // 更新提示文本
        if (this.promptInput) {
            this.promptInput.placeholder = enabled 
                ? '输入对比分析需求，例如：分析两个快照之间的资产配置变化...'
                : '输入分析需求，例如：分析我的投资组合风险水平...';
        }
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
        
        // 如果是比较模式，还需要获取第二个快照ID
        let compareSnapshotId = null;
        if (this.isCompareMode) {
            compareSnapshotId = this.compareSnapshotSelect ? this.compareSnapshotSelect.value : null;
            if (!compareSnapshotId) {
                this.showNotification('请选择比较快照', 'warning');
                return;
            }
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
                snapshot2_id: compareSnapshotId,
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
        // 显示结果面板
        if (this.resultPanel) {
            this.resultPanel.style.display = 'block';
        }
        
        // 更新摘要部分
        if (this.summarySection) {
            this.summarySection.textContent = result.analysis_summary || '无摘要信息';
        }
        
        // 更新风险评估部分
        if (this.riskSection) {
            this.riskSection.textContent = result.risk_assessment || '无风险评估信息';
        }
        
        // 更新投资建议部分
        if (this.adviceSection) {
            this.adviceSection.textContent = result.investment_advice || '无投资建议';
        }
        
        // 更新完整分析内容
        if (this.analysisContent) {
            // 使用marked.js渲染Markdown
            this.analysisContent.innerHTML = marked.parse(result.analysis_content || '');
        }
        
        // 显示对话面板
        if (this.conversationPanel) {
            this.conversationPanel.style.display = 'block';
        }
        
        // 滚动到结果区域
        if (this.resultPanel) {
            this.resultPanel.scrollIntoView({ behavior: 'smooth' });
        }
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
            
            // 添加摘要
            doc.setFontSize(14);
            doc.text('投资组合概览', 20, 40);
            doc.setFontSize(12);
            doc.text(this.analysisResult.analysis_summary || '无摘要', 20, 50, {
                maxWidth: 170
            });
            
            // 添加风险评估
            let yPos = doc.previousAutoTable ? doc.previousAutoTable.finalY + 10 : 70;
            doc.setFontSize(14);
            doc.text('风险评估', 20, yPos);
            doc.setFontSize(12);
            doc.text(this.analysisResult.risk_assessment || '无风险评估', 20, yPos + 10, {
                maxWidth: 170
            });
            
            // 添加投资建议
            yPos = doc.previousAutoTable ? doc.previousAutoTable.finalY + 10 : yPos + 30;
            doc.setFontSize(14);
            doc.text('投资建议', 20, yPos);
            doc.setFontSize(12);
            doc.text(this.analysisResult.investment_advice || '无投资建议', 20, yPos + 10, {
                maxWidth: 170
            });
            
            // 添加完整分析内容
            yPos = doc.previousAutoTable ? doc.previousAutoTable.finalY + 10 : yPos + 30;
            doc.setFontSize(14);
            doc.text('详细分析', 20, yPos);
            
            // 将Markdown转换为纯文本
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = marked.parse(this.analysisResult.analysis_content);
            const plainText = tempDiv.textContent || tempDiv.innerText || '';
            
            doc.setFontSize(12);
            doc.text(plainText, 20, yPos + 10, {
                maxWidth: 170
            });
            
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