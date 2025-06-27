// 全局变量
window.SuperRAG = {
    // 配置
    config: {
        apiTimeout: 30000,
        maxMessageLength: 10000,
        supportedFileTypes: ['.pdf', '.docx', '.txt', '.md']
    },
    
    // 工具函数
    utils: {},
    
    // UI组件
    ui: {},
    
    // 文本选择功能
    textSelection: {}
};

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    initializeSidebar();
});

// 应用初始化
function initializeApp() {
    console.log('SuperRAG应用初始化...');
    
    // 初始化代码高亮
    if (typeof hljs !== 'undefined') {
        hljs.highlightAll();
    }
    
    // 初始化工具提示
    initializeTooltips();
    
    // 初始化文件上传
    initializeFileUpload();
    
    // 初始化通用事件监听
    initializeEventListeners();
    
    console.log('SuperRAG应用初始化完成');
}

// 初始化侧边栏
function initializeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarTrigger = document.getElementById('sidebarTrigger');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const mainContent = document.querySelector('.main-content');
    
    let sidebarTimeout;
    
    if (!sidebar) return;
    
    // 显示侧边栏
    function showSidebar() {
        clearTimeout(sidebarTimeout);
        sidebar.classList.add('show');
        
        // 在桌面端调整主内容区域
        if (window.innerWidth > 768) {
            mainContent?.classList.add('sidebar-open');
        }
    }
    
    // 隐藏侧边栏
    function hideSidebar() {
        sidebarTimeout = setTimeout(() => {
            sidebar.classList.remove('show');
            mainContent?.classList.remove('sidebar-open');
        }, 300); // 300ms延迟，避免误操作
    }
    
    // 立即隐藏侧边栏
    function hideSidebarImmediate() {
        clearTimeout(sidebarTimeout);
        sidebar.classList.remove('show');
        mainContent?.classList.remove('sidebar-open');
    }
    
    // 切换侧边栏（用于按钮点击）
    function toggleSidebar() {
        if (sidebar.classList.contains('show')) {
            hideSidebarImmediate();
        } else {
            showSidebar();
        }
    }
    
    // 鼠标事件监听
    if (sidebarTrigger) {
        sidebarTrigger.addEventListener('mouseenter', showSidebar);
    }
    
    sidebar.addEventListener('mouseenter', () => {
        clearTimeout(sidebarTimeout);
    });
    
    sidebar.addEventListener('mouseleave', hideSidebar);
    
    // 按钮切换（保留手动控制功能）
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }
    
    // 点击遮罩关闭（移动端）
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', hideSidebarImmediate);
    }
    
    // 窗口大小改变时的处理
    window.addEventListener('resize', function() {
        if (window.innerWidth <= 768) {
            mainContent?.classList.remove('sidebar-open');
        } else if (sidebar.classList.contains('show')) {
            mainContent?.classList.add('sidebar-open');
        }
    });
    
    // 更新侧边栏导航活动状态
    updateSidebarNavigation();
}

// 更新侧边栏导航活动状态
function updateSidebarNavigation() {
    const currentPath = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('.sidebar-nav-item');
    
    sidebarLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href !== '#') {
            if ((href === '/' && currentPath === '/') || 
                (href !== '/' && currentPath.includes(href))) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        }
    });
}

// 初始化工具提示
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 初始化文件上传
function initializeFileUpload() {
    const uploadAreas = document.querySelectorAll('.upload-area');
    
    uploadAreas.forEach(area => {
        area.addEventListener('dragover', handleDragOver);
        area.addEventListener('dragleave', handleDragLeave);
        area.addEventListener('drop', handleFileDrop);
        area.addEventListener('click', () => {
            const fileInput = area.querySelector('input[type="file"]');
            if (fileInput) fileInput.click();
        });
    });
}

// 拖拽事件处理
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
}

function handleFileDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
}

// 文件上传处理
function handleFileUpload(file) {
    // 验证文件类型
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!SuperRAG.config.supportedFileTypes.includes(fileExtension)) {
        showAlert('不支持的文件类型。支持的格式：' + SuperRAG.config.supportedFileTypes.join(', '), 'warning');
        return;
    }
    
    // 验证文件大小（最大100MB）
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
        showAlert('文件大小超过限制（最大100MB）', 'warning');
        return;
    }
    
    // 创建FormData并上传
    const formData = new FormData();
    formData.append('file', file);
    
    uploadFileToServer(formData, file.name);
}

// 上传文件到服务器
function uploadFileToServer(formData, fileName) {
    // 显示上传进度
    const progressBar = showUploadProgress(fileName);
    
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('上传失败');
        }
        return response.json();
    })
    .then(data => {
        hideUploadProgress();
        showAlert('文件上传成功！', 'success');
        
        // 刷新文档列表
        if (typeof refreshDocumentList === 'function') {
            refreshDocumentList();
        }
    })
    .catch(error => {
        hideUploadProgress();
        showAlert('上传失败：' + error.message, 'danger');
    });
}

// 显示上传进度
function showUploadProgress(fileName) {
    const progressHtml = `
        <div class="upload-progress" id="uploadProgress">
            <div class="d-flex align-items-center">
                <div class="me-3">
                    <i class="bi bi-file-earmark-arrow-up text-primary"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="small text-muted">正在上传: ${fileName}</div>
                    <div class="progress" style="height: 4px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 100%"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 添加到页面
    const container = document.querySelector('.upload-area') || document.body;
    container.insertAdjacentHTML('afterend', progressHtml);
    
    return document.getElementById('uploadProgress');
}

// 隐藏上传进度
function hideUploadProgress() {
    const progressElement = document.getElementById('uploadProgress');
    if (progressElement) {
        progressElement.remove();
    }
}

// 通用事件监听
function initializeEventListeners() {
    // 导航链接活动状态
    updateActiveNavigation();
    
    // 图片懒加载
    initializeLazyLoading();
    
    // 返回顶部按钮
    initializeBackToTop();
}

// 更新导航活动状态（现在主要更新侧边栏）
function updateActiveNavigation() {
    updateSidebarNavigation();
}

// 初始化懒加载
function initializeLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

// 返回顶部功能
function initializeBackToTop() {
    // 创建返回顶部按钮
    const backToTopButton = document.createElement('button');
    backToTopButton.innerHTML = '<i class="bi bi-arrow-up"></i>';
    backToTopButton.className = 'btn btn-primary position-fixed';
    backToTopButton.style.cssText = `
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        display: none;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    `;
    backToTopButton.onclick = () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };
    
    document.body.appendChild(backToTopButton);
    
    // 滚动监听
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            backToTopButton.style.display = 'block';
        } else {
            backToTopButton.style.display = 'none';
        }
    });
}

// 显示警告消息
function showAlert(message, type = 'info', duration = 5000) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show position-fixed" 
             style="top: 80px; right: 20px; z-index: 9999; min-width: 300px;" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', alertHtml);
    
    // 自动移除
    if (duration > 0) {
        setTimeout(() => {
            const alert = document.querySelector('.alert:last-of-type');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, duration);
    }
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 格式化时间
function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    // 小于1分钟
    if (diff < 60000) {
        return '刚刚';
    }
    
    // 小于1小时
    if (diff < 3600000) {
        return Math.floor(diff / 60000) + '分钟前';
    }
    
    // 小于1天
    if (diff < 86400000) {
        return Math.floor(diff / 3600000) + '小时前';
    }
    
    // 小于7天
    if (diff < 604800000) {
        return Math.floor(diff / 86400000) + '天前';
    }
    
    // 超过7天显示完整日期
    return date.toLocaleDateString('zh-CN');
}

// 防抖函数
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 复制到剪贴板
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('已复制到剪贴板', 'success', 2000);
        }).catch(err => {
            console.error('复制失败:', err);
            fallbackCopyTextToClipboard(text);
        });
    } else {
        fallbackCopyTextToClipboard(text);
    }
}

// 兼容性复制方法
function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.position = 'fixed';
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showAlert('已复制到剪贴板', 'success', 2000);
    } catch (err) {
        showAlert('复制失败', 'danger', 2000);
    }
    
    document.body.removeChild(textArea);
}

// 验证邮箱格式
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// 验证URL格式
function validateURL(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

// 生成随机ID
function generateId(length = 8) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

// 深拷贝对象
function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') return obj;
    if (obj instanceof Date) return new Date(obj.getTime());
    if (obj instanceof Array) return obj.map(item => deepClone(item));
    if (typeof obj === 'object') {
        const clonedObj = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                clonedObj[key] = deepClone(obj[key]);
            }
        }
        return clonedObj;
    }
}

// 将函数添加到全局对象
Object.assign(window.SuperRAG.utils, {
    formatFileSize,
    formatTime,
    debounce,
    throttle,
    copyToClipboard,
    validateEmail,
    validateURL,
    generateId,
    deepClone,
    showAlert
});

// 导出到全局作用域以便其他脚本使用
window.showAlert = showAlert;
window.formatFileSize = formatFileSize;
window.formatTime = formatTime;
window.copyToClipboard = copyToClipboard; 