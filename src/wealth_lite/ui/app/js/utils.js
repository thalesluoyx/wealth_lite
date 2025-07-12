/**
 * 通用工具函数
 */

/**
 * 格式化货币
 * @param {number} value 金额
 * @param {string} currency 货币代码，默认CNY
 * @param {number} decimals 小数位数，默认2
 * @returns {string} 格式化后的货币字符串
 */
export function formatCurrency(value, currency = 'CNY', decimals = 2) {
    if (value === null || value === undefined) {
        return '-';
    }
    
    const formatter = new Intl.NumberFormat('zh-CN', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
    
    return formatter.format(value);
}

/**
 * 格式化百分比
 * @param {number} value 百分比值
 * @param {number} decimals 小数位数，默认2
 * @returns {string} 格式化后的百分比字符串
 */
export function formatPercent(value, decimals = 2) {
    if (value === null || value === undefined) {
        return '-';
    }
    
    return `${value.toFixed(decimals)}%`;
}

/**
 * 格式化日期
 * @param {string|Date} date 日期
 * @param {string} format 格式，默认'YYYY-MM-DD'
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date, format = 'YYYY-MM-DD') {
    if (!date) {
        return '-';
    }
    
    const d = new Date(date);
    
    if (isNaN(d.getTime())) {
        return '-';
    }
    
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');
    
    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes)
        .replace('ss', seconds);
}

/**
 * 截断文本
 * @param {string} text 文本
 * @param {number} maxLength 最大长度
 * @returns {string} 截断后的文本
 */
export function truncateText(text, maxLength = 50) {
    if (!text) {
        return '';
    }
    
    if (text.length <= maxLength) {
        return text;
    }
    
    return `${text.substring(0, maxLength)}...`;
}

/**
 * 防抖函数
 * @param {Function} func 要执行的函数
 * @param {number} wait 等待时间（毫秒）
 * @returns {Function} 防抖处理后的函数
 */
export function debounce(func, wait = 300) {
    let timeout;
    
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 节流函数
 * @param {Function} func 要执行的函数
 * @param {number} limit 限制时间（毫秒）
 * @returns {Function} 节流处理后的函数
 */
export function throttle(func, limit = 300) {
    let inThrottle;
    
    return function executedFunction(...args) {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => {
                inThrottle = false;
            }, limit);
        }
    };
}

/**
 * 生成UUID
 * @returns {string} UUID字符串
 */
export function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

/**
 * 从对象数组中获取唯一值
 * @param {Array} array 对象数组
 * @param {string} key 键名
 * @returns {Array} 唯一值数组
 */
export function getUniqueValues(array, key) {
    return [...new Set(array.map(item => item[key]))];
}

/**
 * 将对象数组按键分组
 * @param {Array} array 对象数组
 * @param {string} key 键名
 * @returns {Object} 分组后的对象
 */
export function groupBy(array, key) {
    return array.reduce((result, item) => {
        const groupKey = item[key];
        if (!result[groupKey]) {
            result[groupKey] = [];
        }
        result[groupKey].push(item);
        return result;
    }, {});
}

/**
 * 将查询参数对象转换为URL查询字符串
 * @param {Object} params 查询参数对象
 * @returns {string} URL查询字符串
 */
export function toQueryString(params) {
    return Object.keys(params)
        .filter(key => params[key] !== undefined && params[key] !== null && params[key] !== '')
        .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
        .join('&');
}

/**
 * 从URL查询字符串解析查询参数对象
 * @param {string} queryString URL查询字符串
 * @returns {Object} 查询参数对象
 */
export function parseQueryString(queryString) {
    if (!queryString) {
        return {};
    }
    
    const query = queryString.startsWith('?') ? queryString.substring(1) : queryString;
    
    return query.split('&').reduce((params, param) => {
        const [key, value] = param.split('=');
        if (key) {
            params[decodeURIComponent(key)] = decodeURIComponent(value || '');
        }
        return params;
    }, {});
}

/**
 * 深拷贝对象
 * @param {*} obj 要拷贝的对象
 * @returns {*} 拷贝后的对象
 */
export function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') {
        return obj;
    }
    
    if (obj instanceof Date) {
        return new Date(obj.getTime());
    }
    
    if (obj instanceof Array) {
        return obj.map(item => deepClone(item));
    }
    
    if (obj instanceof Object) {
        const copy = {};
        Object.keys(obj).forEach(key => {
            copy[key] = deepClone(obj[key]);
        });
        return copy;
    }
    
    return obj;
} 