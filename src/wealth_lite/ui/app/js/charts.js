/**
 * WealthLite 图表管理器
 * 使用 Chart.js 实现韩文仪表板风格的图表
 */

// 非入侵性 Chart.js 兼容处理
if (typeof Chart === 'undefined') {
  try {
    if (typeof require !== 'undefined') {
      window.Chart = require('chart.js/auto');
    }
  } catch (e) {
    // 忽略，Chart 依然未定义时会在开发环境报错
  }
}

class ChartManager {
    constructor() {
        this.charts = {};
        this.chartColors = {
            primary: '#667eea',
            secondary: '#764ba2',
            accent: '#4facfe',
            success: '#10b981',
            warning: '#f59e0b',
            danger: '#ef4444',
            info: '#3b82f6',
            purple: '#8b5cf6'
        };
        
        this.init();
    }

    init() {
        // 等待DOM加载完成后初始化图表
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.destroyExistingCharts();
                this.initializeCharts();
            });
        } else {
            this.destroyExistingCharts();
            this.initializeCharts();
        }
    }

    initializeCharts() {
        this.createMainChart();
        this.createAssetTypeChart();
        this.createCashChart();
        this.createFixedIncomeChart();
        this.setupChartTooltip();
    }

    createMainChart() {
        const canvas = document.getElementById('mainChart');
        if (!canvas) return;
        
        // 销毁现有图表（如果存在）
        if (this.charts.main) {
            this.charts.main.destroy();
        }
        
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // 生成模拟的波浪形数据
        const data = this.generateWaveData();

        this.charts.main = new Chart(canvas, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: '现金',
                        data: data.cash,
                        borderColor: this.chartColors.success,
                        backgroundColor: this.createGradient(ctx, this.chartColors.success, 0.1),
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        pointHoverBackgroundColor: this.chartColors.success,
                        pointHoverBorderColor: '#ffffff',
                        pointHoverBorderWidth: 2
                    },
                    {
                        label: '定期存款',
                        data: data.deposits,
                        borderColor: this.chartColors.info,
                        backgroundColor: this.createGradient(ctx, this.chartColors.info, 0.1),
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        pointHoverBackgroundColor: this.chartColors.info,
                        pointHoverBorderColor: '#ffffff',
                        pointHoverBorderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false, // 使用自定义tooltip
                        external: (context) => {
                            this.updateCustomTooltip(context);
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                size: 12
                            }
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: '#f1f5f9',
                            borderDash: [2, 2]
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                size: 12
                            },
                            callback: function(value) {
                                return value.toLocaleString() + '元';
                            }
                        }
                    }
                },
                elements: {
                    point: {
                        hoverRadius: 8
                    }
                }
            }
        });
    }

    createCashChart() {
        const ctx = document.getElementById('cashChart');
        if (!ctx) return;

        this.charts.cash = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['活期存款', '余额宝', '现金'],
                datasets: [{
                    data: [1500000, 1200000, 534000],
                    backgroundColor: [
                        this.chartColors.success,
                        this.chartColors.accent,
                        this.chartColors.info
                    ],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ${value.toLocaleString()}元 (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    createAssetTypeChart() {
        const ctx = document.getElementById('assetTypeChart');
        if (!ctx) return;
        
        // 销毁现有图表（如果存在）
        if (this.charts.assetType) {
            this.charts.assetType.destroy();
        }

        this.charts.assetType = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['现金及等价物', '固定收益', '权益类'],
                datasets: [{
                    data: [0, 0, 0], // 初始化为0，后续通过updateAssetTypeChart更新
                    backgroundColor: [
                        this.chartColors.success,
                        this.chartColors.primary,
                        this.chartColors.warning
                    ],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
                                return `${context.label}: ${value.toLocaleString()}元 (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    createCashChart() {
        const ctx = document.getElementById('cashChart');
        if (!ctx) return;

        // 销毁现有图表（如果存在）
        if (this.charts.cash) {
            this.charts.cash.destroy();
        }

        this.charts.cash = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        this.chartColors.success,
                        this.chartColors.accent,
                        this.chartColors.info
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
                                return `${context.label}: ${value.toLocaleString()}元 (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    createFixedIncomeChart() {
        const ctx = document.getElementById('fixedIncomeChart');
        if (!ctx) return;

        // 销毁现有图表（如果存在）
        if (this.charts.fixedIncome) {
            this.charts.fixedIncome.destroy();
        }

        this.charts.fixedIncome = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        this.chartColors.primary,
                        this.chartColors.purple,
                        this.chartColors.warning
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
                                return `${context.label}: ${value.toLocaleString()}元 (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    setupChartTooltip() {
        const tooltip = document.getElementById('chartTooltip');
        if (tooltip) {
            // 默认显示tooltip
            setTimeout(() => {
                tooltip.classList.add('show');
            }, 1000);
        }
    }

    updateCustomTooltip(context) {
        const tooltip = document.getElementById('chartTooltip');
        if (!tooltip) return;

        const tooltipModel = context.tooltip;

        if (tooltipModel.opacity === 0) {
            tooltip.style.opacity = '0';
            return;
        }

        // 更新tooltip内容
        if (tooltipModel.body) {
            const bodyLines = tooltipModel.body.map(item => item.lines);
            const tooltipValues = tooltip.querySelector('.tooltip-values');
            
            if (tooltipValues) {
                tooltipValues.innerHTML = bodyLines.map((lines, i) => {
                    const colors = tooltipModel.labelColors[i];
                    return `
                        <div class="tooltip-item">
                            <span class="label">${tooltipModel.dataPoints[i].dataset.label}</span>
                            <span class="value">${lines[0]}</span>
                        </div>
                    `;
                }).join('');
            }
        }

        tooltip.style.opacity = '1';
        tooltip.classList.add('show');
    }

    generateWaveData() {
        const labels = [];
        const cash = [];
        const deposits = [];
        
        // 生成30天的数据
        for (let i = 0; i < 30; i++) {
            const date = new Date();
            date.setDate(date.getDate() - (29 - i));
            labels.push(date.getDate());
            
            // 生成波浪形数据
            const baseValue = 2000000;
            const waveAmplitude = 300000;
            const cashValue = baseValue + Math.sin(i * 0.3) * waveAmplitude + Math.random() * 100000;
            const depositValue = baseValue * 0.8 + Math.cos(i * 0.25) * waveAmplitude * 0.7 + Math.random() * 80000;
            
            cash.push(Math.round(cashValue));
            deposits.push(Math.round(depositValue));
        }
        
        return { labels, cash, deposits };
    }

    createGradient(ctx, color, opacity) {
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, color + Math.round(opacity * 255).toString(16).padStart(2, '0'));
        gradient.addColorStop(1, color + '00');
        return gradient;
    }

    updateTimeRange(range) {
        console.log(`更新图表时间范围: ${range}`);
        
        // 根据时间范围生成新数据
        let dataPoints;
        switch(range) {
            case '7d':
                dataPoints = 7;
                break;
            case '1m':
                dataPoints = 30;
                break;
            case '3m':
                dataPoints = 90;
                break;
            case '1y':
                dataPoints = 365;
                break;
            default:
                dataPoints = 30;
        }
        
        // 重新生成数据
        const newData = this.generateWaveDataForRange(dataPoints);
        
        // 更新主图表
        if (this.charts.main) {
            this.charts.main.data.labels = newData.labels;
            this.charts.main.data.datasets[0].data = newData.cash;
            this.charts.main.data.datasets[1].data = newData.deposits;
            this.charts.main.update('active');
        }
    }

    generateWaveDataForRange(dataPoints) {
        const labels = [];
        const cash = [];
        const deposits = [];
        
        for (let i = 0; i < dataPoints; i++) {
            const date = new Date();
            date.setDate(date.getDate() - (dataPoints - 1 - i));
            
            if (dataPoints <= 30) {
                labels.push(date.getDate());
            } else if (dataPoints <= 90) {
                labels.push(`${date.getMonth() + 1}/${date.getDate()}`);
            } else {
                labels.push(`${date.getMonth() + 1}月`);
            }
            
            const baseValue = 2000000;
            const waveAmplitude = 300000;
            const frequency = dataPoints > 90 ? 0.1 : 0.3;
            
            const cashValue = baseValue + Math.sin(i * frequency) * waveAmplitude + Math.random() * 100000;
            const depositValue = baseValue * 0.8 + Math.cos(i * frequency * 0.8) * waveAmplitude * 0.7 + Math.random() * 80000;
            
            cash.push(Math.round(cashValue));
            deposits.push(Math.round(depositValue));
        }
        
        return { labels, cash, deposits };
    }

    // 响应式图表调整
    handleResize() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.resize();
            }
        });
    }

    // 销毁所有图表
    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }

    destroyExistingCharts() {
        // 销毁所有现有的Chart.js实例
        if (typeof Chart !== 'undefined') {
            // Chart.js 3.x+ 方式：通过 Chart.registry 获取所有实例
            const canvases = document.querySelectorAll('canvas');
            canvases.forEach(canvas => {
                const chart = Chart.getChart(canvas);
                if (chart) {
                    chart.destroy();
                }
            });
        }
        
        // 清空我们自己的图表记录
        this.charts = {};
    }

    // 获取图表实例
    getChart(name) {
        return this.charts[name];
    }

    // 更新图表主题
    updateTheme(isDark = false) {
        // 更新图表主题
        Object.values(this.charts).forEach(chart => {
            if (chart.options && chart.options.scales) {
                const textColor = isDark ? '#ffffff' : '#94a3b8';
                const gridColor = isDark ? '#374151' : '#f1f5f9';
                
                if (chart.options.scales.x) {
                    chart.options.scales.x.ticks.color = textColor;
                    chart.options.scales.x.grid.color = gridColor;
                }
                if (chart.options.scales.y) {
                    chart.options.scales.y.ticks.color = textColor;
                    chart.options.scales.y.grid.color = gridColor;
                }
                
                chart.update();
            }
        });
    }

    updateAssetTypeChart(positions) {
        if (!this.charts.assetType || !positions) return;

        // 按资产类型分组统计
        const assetTypeData = {};
        positions.forEach(position => {
            const type = position.type || 'UNKNOWN';
            const typeText = this.getAssetTypeText(type);
            const amount = position.amount || 0;
            
            if (!assetTypeData[typeText]) {
                assetTypeData[typeText] = 0;
            }
            assetTypeData[typeText] += amount;
        });

        const labels = Object.keys(assetTypeData);
        const data = Object.values(assetTypeData);
        const total = data.reduce((sum, value) => sum + value, 0);

        // 更新图表数据
        this.charts.assetType.data.labels = labels;
        this.charts.assetType.data.datasets[0].data = data;
        this.charts.assetType.update();

        // 更新中心显示的总金额
        const centerAmount = document.getElementById('assetTypeAmount');
        if (centerAmount) {
            centerAmount.textContent = total.toLocaleString();
        }
    }

    updateCashChart(positions) {
        if (!this.charts.cash || !positions) return;

        // 过滤出现金及等价物类型的资产
        const cashPositions = positions.filter(position => {
            const type = position.type || '';
            return type.toLowerCase() === 'cash' || type === 'CASH';
        });

        // 按资产子类型分组统计
        const cashData = {};
        cashPositions.forEach(position => {
            const subType = position.asset_subtype || position.name || '未分类';
            const amount = position.amount || 0;
            
            if (!cashData[subType]) {
                cashData[subType] = 0;
            }
            cashData[subType] += amount;
        });

        const labels = Object.keys(cashData);
        const data = Object.values(cashData);
        const total = data.reduce((sum, value) => sum + value, 0);

        // 更新图表数据
        this.charts.cash.data.labels = labels;
        this.charts.cash.data.datasets[0].data = data;
        this.charts.cash.update();

        // 更新中心显示的总金额
        const centerAmount = document.getElementById('cashAmount');
        if (centerAmount) {
            centerAmount.textContent = total.toLocaleString();
        }
    }

    updateFixedIncomeChart(positions) {
        if (!this.charts.fixedIncome || !positions) return;

        // 过滤出固定收益类型的资产
        const fixedIncomePositions = positions.filter(position => {
            const type = position.type || '';
            return type.toLowerCase() === 'fixed_income' || type === 'FIXED_INCOME';
        });

        // 按资产子类型分组统计
        const fixedIncomeData = {};
        fixedIncomePositions.forEach(position => {
            const subType = position.asset_subtype || position.name || '未分类';
            const amount = position.amount || 0;
            
            if (!fixedIncomeData[subType]) {
                fixedIncomeData[subType] = 0;
            }
            fixedIncomeData[subType] += amount;
        });

        const labels = Object.keys(fixedIncomeData);
        const data = Object.values(fixedIncomeData);
        const total = data.reduce((sum, value) => sum + value, 0);

        // 更新图表数据
        this.charts.fixedIncome.data.labels = labels;
        this.charts.fixedIncome.data.datasets[0].data = data;
        this.charts.fixedIncome.update();

        // 更新中心显示的总金额
        const centerAmount = document.getElementById('fixedAmount');
        if (centerAmount) {
            centerAmount.textContent = total.toLocaleString();
        }
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
        return typeMap[type] || '其他';
    }
}

// 窗口大小改变时调整图表
window.addEventListener('resize', () => {
    if (window.chartManager) {
        window.chartManager.handleResize();
    }
});

// 当DOM加载完成后初始化图表管理器
document.addEventListener('DOMContentLoaded', () => {
    window.chartManager = new ChartManager();
});

// 导出类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartManager;
} 