/**
 * Stagewise Toolbar - 非入侵性UI元素选择和AI修改工具
 * 使用方法：在任何HTML页面中添加 <script src="stagewise-toolbar.js"></script>
 */

class StagewiseToolbar {
    constructor(options = {}) {
        this.options = {
            enabled: true,
            autoInit: true,
            position: 'top-right',
            theme: 'dark',
            projectPath: options.projectPath || window.location.pathname,
            ...options
        };
        
        this.selectedElement = null;
        this.isSelecting = false;
        this.toolbar = null;
        this.isInitialized = false;
        
        if (this.options.autoInit) {
            this.init();
        }
    }
    
    init() {
        if (this.isInitialized) return;
        
        console.log('🎯 初始化 Stagewise 工具栏...');
        
        // 等待DOM加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
        
        this.isInitialized = true;
    }
    
    setup() {
        this.createStyles();
        this.createToolbar();
        this.createToggleButton();
        this.bindEvents();
        
        console.log('✅ Stagewise 工具栏已就绪');
    }
    
    createStyles() {
        const styles = `
            /* Stagewise 工具栏样式 */
            .stagewise-highlight {
                outline: 3px solid #4fd1c7 !important;
                outline-offset: 2px !important;
                cursor: pointer !important;
                transition: outline 0.2s ease !important;
            }
            
            .stagewise-selected {
                outline: 3px solid #f56565 !important;
                outline-offset: 2px !important;
                background: rgba(245, 101, 101, 0.1) !important;
            }
            
            .stagewise-toolbar {
                position: fixed;
                top: 60px;
                right: 10px;
                background: #2d3748;
                color: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.3);
                z-index: 999999;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 14px;
                max-width: 320px;
                min-width: 280px;
                display: none;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
            }
            
            .stagewise-toggle {
                position: fixed;
                top: 10px;
                right: 10px;
                background: #4fd1c7;
                color: #1a202c;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: bold;
                font-size: 12px;
                z-index: 999999;
                box-shadow: 0 4px 12px rgba(79, 209, 199, 0.3);
                transition: all 0.2s ease;
            }
            
            .stagewise-toggle:hover {
                background: #38b2ac;
                transform: translateY(-1px);
            }
            
            .stagewise-toggle.active {
                background: #e53e3e;
                color: white;
            }
        `;
        
        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }
    
    createToggleButton() {
        const toggle = document.createElement('button');
        toggle.className = 'stagewise-toggle';
        toggle.textContent = '🎯 启用 Stagewise';
        toggle.onclick = () => this.toggleSelection();
        
        document.body.appendChild(toggle);
        this.toggleButton = toggle;
    }
    
    createToolbar() {
        const toolbar = document.createElement('div');
        toolbar.className = 'stagewise-toolbar';
        toolbar.innerHTML = `
            <div style="margin-bottom: 12px; font-weight: bold; color: #4fd1c7; display: flex; align-items: center; gap: 8px;">
                🎯 Stagewise
                <span style="font-size: 10px; background: #1a202c; padding: 2px 6px; border-radius: 3px;">v1.0</span>
            </div>
            <div class="selected-info" style="margin-bottom: 12px; padding: 8px; background: #1a202c; border-radius: 4px; font-size: 12px; color: #a0aec0;">
                点击页面元素来选择
            </div>
            <textarea class="comment-input" placeholder="描述您想要的修改..." 
                style="width: 100%; height: 70px; margin-bottom: 12px; padding: 8px; border: none; border-radius: 4px; resize: vertical; font-size: 12px; background: #f7fafc; color: #2d3748;"></textarea>
            <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                <button class="send-btn" style="flex: 1; padding: 8px; background: #4fd1c7; color: #1a202c; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 12px;">
                    发送给 Cursor AI
                </button>
                <button class="close-btn" style="padding: 8px 12px; background: #e53e3e; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                    ✕
                </button>
            </div>
            <div style="font-size: 10px; color: #718096; text-align: center;">
                选择模式: <span class="status-indicator" style="color: #4fd1c7;">已启用</span>
            </div>
        `;
        
        document.body.appendChild(toolbar);
        this.toolbar = toolbar;
        
        // 绑定工具栏按钮事件
        toolbar.querySelector('.send-btn').onclick = () => this.sendToAI();
        toolbar.querySelector('.close-btn').onclick = () => this.hideToolbar();
    }
    
    bindEvents() {
        // 鼠标事件
        this.onMouseOver = (e) => this.handleMouseOver(e);
        this.onMouseOut = (e) => this.handleMouseOut(e);
        this.onClick = (e) => this.handleClick(e);
        
        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'S') {
                e.preventDefault();
                this.toggleSelection();
            }
            if (e.key === 'Escape' && this.isSelecting) {
                this.disableSelection();
            }
        });
    }
    
    toggleSelection() {
        if (this.isSelecting) {
            this.disableSelection();
        } else {
            this.enableSelection();
        }
    }
    
    enableSelection() {
        this.isSelecting = true;
        this.toggleButton.textContent = '🎯 关闭 Stagewise';
        this.toggleButton.classList.add('active');
        
        document.addEventListener('mouseover', this.onMouseOver);
        document.addEventListener('mouseout', this.onMouseOut);
        document.addEventListener('click', this.onClick, true);
        
        document.body.style.cursor = 'crosshair';
        console.log('✅ Stagewise 选择模式已启用');
    }
    
    disableSelection() {
        this.isSelecting = false;
        this.toggleButton.textContent = '🎯 启用 Stagewise';
        this.toggleButton.classList.remove('active');
        
        document.removeEventListener('mouseover', this.onMouseOver);
        document.removeEventListener('mouseout', this.onMouseOut);
        document.removeEventListener('click', this.onClick, true);
        
        document.body.style.cursor = '';
        this.hideToolbar();
        this.clearSelection();
        console.log('⏹️ Stagewise 选择模式已关闭');
    }
    
    handleMouseOver(e) {
        if (!this.isSelecting || this.isToolbarElement(e.target)) return;
        e.target.classList.add('stagewise-highlight');
    }
    
    handleMouseOut(e) {
        if (!this.isSelecting) return;
        e.target.classList.remove('stagewise-highlight');
    }
    
    handleClick(e) {
        if (this.isToolbarElement(e.target)) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        this.selectElement(e.target);
    }
    
    selectElement(element) {
        // 清除之前的选择
        this.clearSelection();
        
        // 选择新元素
        this.selectedElement = element;
        element.classList.add('stagewise-selected');
        element.classList.remove('stagewise-highlight');
        
        // 更新工具栏信息
        const elementInfo = this.getElementInfo(element);
        this.toolbar.querySelector('.selected-info').innerHTML = `
            <strong>已选择:</strong> ${elementInfo.selector}<br>
            <small style="color: #718096;">${elementInfo.description}</small>
        `;
        
        // 显示工具栏
        this.showToolbar();
        
        console.log('✅ 元素已选择:', element, elementInfo);
    }
    
    getElementInfo(element) {
        const tagName = element.tagName.toLowerCase();
        const className = element.className ? '.' + element.className.split(' ').filter(c => !c.startsWith('stagewise')).join('.') : '';
        const id = element.id ? '#' + element.id : '';
        const selector = `${tagName}${id}${className}`;
        
        let description = '';
        if (element.textContent && element.textContent.trim()) {
            description = element.textContent.trim().substring(0, 50) + (element.textContent.length > 50 ? '...' : '');
        } else if (element.alt) {
            description = `图片: ${element.alt}`;
        } else if (element.placeholder) {
            description = `输入框: ${element.placeholder}`;
        } else {
            description = `${tagName} 元素`;
        }
        
        return { selector, description };
    }
    
    showToolbar() {
        this.toolbar.style.display = 'block';
        this.toolbar.style.animation = 'fadeIn 0.3s ease';
    }
    
    hideToolbar() {
        this.toolbar.style.display = 'none';
        this.clearSelection();
    }
    
    clearSelection() {
        if (this.selectedElement) {
            this.selectedElement.classList.remove('stagewise-selected');
            this.selectedElement = null;
        }
        
        // 清除所有高亮
        document.querySelectorAll('.stagewise-highlight').forEach(el => {
            el.classList.remove('stagewise-highlight');
        });
    }
    
    sendToAI() {
        const comment = this.toolbar.querySelector('.comment-input').value.trim();
        
        if (!this.selectedElement || !comment) {
            alert('请先选择元素并添加修改说明');
            return;
        }
        
        const elementInfo = {
            tagName: this.selectedElement.tagName,
            className: this.selectedElement.className,
            id: this.selectedElement.id,
            textContent: this.selectedElement.textContent?.substring(0, 200),
            outerHTML: this.selectedElement.outerHTML?.substring(0, 500),
            selector: this.getElementInfo(this.selectedElement).selector
        };
        
        const requestData = {
            element: elementInfo,
            comment: comment,
            timestamp: new Date().toISOString(),
            pageUrl: window.location.href,
            projectPath: this.options.projectPath,
            context: `Stagewise UI 修改请求 - ${document.title}`,
            // 添加更多上下文信息
            filePath: 'ui/demo_modules.html',
            elementPosition: this.getElementPosition(this.selectedElement)
        };
        
        console.log('🤖 发送给 Cursor AI 的请求:', requestData);
        
        // 尝试多种方式发送到 Cursor
        let sent = false;
        
        // 方式1: 检查 Cursor 插件的 sendToEditor 方法
        if (window.stagewise && typeof window.stagewise.sendToEditor === 'function' && window.stagewise.sendToEditor !== this.sendToAI) {
            try {
                window.stagewise.sendToEditor(requestData);
                this.showSuccess(`✅ 已通过 Cursor 插件发送修改请求！\n\n元素: ${elementInfo.selector}\n说明: ${comment}`);
                sent = true;
            } catch (error) {
                console.error('方式1失败:', error);
            }
        }
        
        // 方式2: 检查 Cursor 的其他可能接口
        if (!sent && window.cursor && window.cursor.sendToAI) {
            try {
                window.cursor.sendToAI(requestData);
                this.showSuccess(`✅ 已通过 Cursor 接口发送修改请求！\n\n元素: ${elementInfo.selector}\n说明: ${comment}`);
                sent = true;
            } catch (error) {
                console.error('方式2失败:', error);
            }
        }
        
        // 方式3: 尝试通过 postMessage 发送到 Cursor
        if (!sent) {
            try {
                // 发送到可能的 Cursor 扩展
                window.postMessage({
                    type: 'STAGEWISE_REQUEST',
                    data: requestData,
                    source: 'stagewise-toolbar'
                }, '*');
                
                // 也尝试向父窗口发送（如果在 iframe 中）
                if (window.parent !== window) {
                    window.parent.postMessage({
                        type: 'STAGEWISE_REQUEST',
                        data: requestData,
                        source: 'stagewise-toolbar'
                    }, '*');
                }
                
                console.log('📡 已通过 postMessage 发送请求');
                this.showDemo(requestData, true);
                sent = true;
            } catch (error) {
                console.error('方式3失败:', error);
            }
        }
        
        // 如果所有方式都失败，显示演示模式
        if (!sent) {
            this.showDemo(requestData, false);
        }
        
        // 清理
        this.toolbar.querySelector('.comment-input').value = '';
        this.hideToolbar();
    }
    
    getElementPosition(element) {
        const rect = element.getBoundingClientRect();
        return {
            x: rect.left,
            y: rect.top,
            width: rect.width,
            height: rect.height,
            scrollX: window.scrollX,
            scrollY: window.scrollY
        };
    }
    
    showSuccess(message) {
        alert(message);
    }
    
    showError(message) {
        alert(message);
    }
    
    showDemo(requestData, postMessageSent = false) {
        if (postMessageSent) {
            alert(`📡 Stagewise 请求已发送\n\n选择的元素: ${requestData.element.selector}\n修改说明: ${requestData.comment}\n\n💡 请求已通过 postMessage 发送。如果 Cursor 插件正在监听，您应该会在 Cursor 中看到相应的修改建议。\n\n🔍 请检查 Cursor 中是否有新的 AI 对话或建议。`);
        } else {
            alert(`📝 Stagewise 演示模式\n\n选择的元素: ${requestData.element.selector}\n修改说明: ${requestData.comment}\n\n💡 无法连接到 Cursor 插件。请确保：\n1. Cursor 正在运行\n2. stagewise 插件已安装并激活\n3. 当前页面可以与 Cursor 通信\n\n详细信息已记录到控制台。`);
        }
    }
    
    isToolbarElement(element) {
        return element.closest('.stagewise-toolbar') || 
               element.closest('.stagewise-toggle') || 
               element.classList.contains('stagewise-toolbar') ||
               element.classList.contains('stagewise-toggle');
    }
    
    // 公共API
    enable() {
        this.enableSelection();
    }
    
    disable() {
        this.disableSelection();
    }
    
    destroy() {
        this.disableSelection();
        if (this.toolbar) this.toolbar.remove();
        if (this.toggleButton) this.toggleButton.remove();
        
        // 移除样式
        document.querySelectorAll('style').forEach(style => {
            if (style.textContent.includes('stagewise-highlight')) {
                style.remove();
            }
        });
    }
}

// 自动初始化（仅在开发环境）
if (typeof window !== 'undefined') {
    const isDevelopment = window.location.hostname === 'localhost' || 
                         window.location.hostname === '127.0.0.1' ||
                         window.location.hostname === '';
    
    if (isDevelopment) {
        // 保存可能存在的 Cursor 插件接口
        const existingStagewise = window.stagewise;
        
        // 创建全局实例，但保留原有的 Cursor 插件接口
        window.stagewise = window.stagewise || {};
        
        // 如果存在 Cursor 插件的 sendToEditor 方法，保留它
        if (existingStagewise && existingStagewise.sendToEditor) {
            window.stagewise.sendToEditor = existingStagewise.sendToEditor;
        }
        
        // 创建工具栏实例
        window.stagewise.toolbar = new StagewiseToolbar({
            projectPath: '/e%3A/Work/workspace/wealth_lite'
        });
        
        console.log('🎯 Stagewise 工具栏已加载 (按 Ctrl+Shift+S 快速切换)');
        
        // 检查 Cursor 插件状态
        if (window.stagewise.sendToEditor && typeof window.stagewise.sendToEditor === 'function') {
            console.log('✅ 检测到 Cursor 插件接口');
        } else {
            console.log('⚠️ 未检测到 Cursor 插件接口，将使用演示模式');
        }
        
        // 添加 postMessage 监听器以处理可能的 Cursor 响应
        window.addEventListener('message', (event) => {
            if (event.data && event.data.type === 'STAGEWISE_RESPONSE') {
                console.log('📨 收到 Cursor 响应:', event.data);
                alert(`✅ Cursor 已处理您的请求！\n\n${event.data.message || '请查看 Cursor 中的 AI 助手响应。'}`);
            }
        });
    }
} 