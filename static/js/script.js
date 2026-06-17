/**
 * 视频转文字工具 - 前端JavaScript
 */

// 全局变量
let selectedFiles = []; // 改为数组支持多文件
let tasks = [];
let wsConnections = {};
let refreshInterval = null;

// DOM元素引用
let uploadArea, videoFileInput, uploadButton, taskList, refreshButton;
let previewModal, previewAudio, previewText, downloadAudioBtn, downloadTextBtn;

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initElements();
    setupEventListeners();
    loadTasks();

    // 设置智能定时刷新
    startSmartRefresh();
});

// 初始化DOM元素
function initElements() {
    console.log('🎯 Initializing DOM elements');
    uploadArea = document.getElementById('uploadArea');
    videoFileInput = document.getElementById('videoFile');
    uploadButton = document.getElementById('uploadButton');
    taskList = document.getElementById('taskList');
    refreshButton = document.getElementById('refreshButton');

    console.log('📋 DOM elements initialized:');
    console.log('   - uploadArea:', uploadArea ? '✅' : '❌');
    console.log('   - videoFileInput:', videoFileInput ? '✅' : '❌');
    console.log('   - uploadButton:', uploadButton ? '✅' : '❌');
    console.log('   - taskList:', taskList ? '✅' : '❌');
    console.log('   - refreshButton:', refreshButton ? '✅' : '❌');

    // 初始化模态框相关元素
    const modalElement = document.getElementById('previewModal');
    if (modalElement) {
        previewModal = new bootstrap.Modal(modalElement);
        previewAudio = document.getElementById('previewAudio');
        previewText = document.getElementById('previewText');
        downloadAudioBtn = document.getElementById('downloadAudioBtn');
        downloadTextBtn = document.getElementById('downloadTextBtn');
        console.log('   - modal elements:', previewModal ? '✅' : '❌');
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 点击上传区域选择文件
    if (uploadArea) {
        uploadArea.addEventListener('click', handleUploadAreaClick);
    }

    // 文件选择变化
    if (videoFileInput) {
        videoFileInput.addEventListener('change', handleFileInputChange);
    }

    // 上传按钮点击
    if (uploadButton) {
        uploadButton.addEventListener('click', uploadFile);
    }

    // 刷新按钮点击
    if (refreshButton) {
        refreshButton.addEventListener('click', loadTasks);
    }

    // 拖放功能
    setupDragAndDrop();
}

// 处理上传区域点击
function handleUploadAreaClick() {
    videoFileInput.click();
}

// 处理文件输入变化
function handleFileInputChange(e) {
    if (e.target.files.length > 0) {
        selectedFiles = Array.from(e.target.files);
        updateUploadAreaWithFiles();
        uploadButton.disabled = false;
    }
}

// 设置拖放功能
function setupDragAndDrop() {
    if (!uploadArea) return;

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');

        if (e.dataTransfer.files.length > 0) {
            selectedFiles = Array.from(e.dataTransfer.files);
            videoFileInput.files = e.dataTransfer.files;
            updateUploadAreaWithFiles();
            uploadButton.disabled = false;
        }
    });
}

// 更新上传区域显示文件信息
function updateUploadAreaWithFiles() {
    if (!uploadArea || selectedFiles.length === 0) return;

    const totalSize = selectedFiles.reduce((sum, file) => sum + file.size, 0);
    const fileNames = selectedFiles.length === 1 
        ? selectedFiles[0].name 
        : `${selectedFiles.length} 个文件`;

    uploadArea.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="upload-icon-compact me-3" style="background: rgba(72, 187, 120, 0.15);">
                <i class="bi bi-file-earmark-check-fill" style="color: #48bb78;"></i>
            </div>
            <div class="flex-grow-1">
                <h6 class="mb-1" style="color: #48bb78;">${escapeHtml(fileNames)}</h6>
                <small class="text-muted">总大小: ${formatFileSize(totalSize)} | 点击重新选择</small>
            </div>
        </div>
    `;
}

// 上传文件（分片上传，支持大文件）
async function uploadFile() {
    if (selectedFiles.length === 0) {
        showAlert('warning', '请先选择文件');
        return;
    }

    const allowedTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska', 'video/webm', 'video/x-msvideo'];
    for (const file of selectedFiles) {
        if (!allowedTypes.some(type => file.type === type || file.name.match(/\.(mp4|avi|mov|mkv|webm)$/i))) {
            showAlert('warning', `文件 ${file.name} 格式不支持，请选择视频文件`);
            return;
        }
    }

    uploadButton.disabled = true;
    const originalButtonText = uploadButton.innerHTML;

    let successCount = 0;
    let failCount = 0;

    for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        const CHUNK_SIZE = 10 * 1024 * 1024; // 10MB per chunk
        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
        const uploadId = crypto.randomUUID();

        try {
            // 上传各分片
            for (let ci = 0; ci < totalChunks; ci++) {
                const pct = Math.round(((ci + 1) / totalChunks) * 100);
                uploadButton.innerHTML = `<span class="spinner-border spinner-border-sm"></span> 上传中 (${i + 1}/${selectedFiles.length}) ${pct}%`;

                const blob = file.slice(ci * CHUNK_SIZE, (ci + 1) * CHUNK_SIZE);
                const fd = new FormData();
                fd.append('file', blob, file.name);
                fd.append('upload_id', uploadId);
                fd.append('chunk_index', ci);
                fd.append('total_chunks', totalChunks);
                fd.append('filename', file.name);

                const res = await fetch('/upload/chunk', { method: 'POST', body: fd });
                if (!res.ok) {
                    const err = await res.json().catch(() => ({}));
                    throw new Error(err.detail || `分片 ${ci} 上传失败: ${res.status}`);
                }
            }

            // 合并分片
            uploadButton.innerHTML = `<span class="spinner-border spinner-border-sm"></span> 合并中 (${i + 1}/${selectedFiles.length})...`;
            const mfd = new FormData();
            mfd.append('upload_id', uploadId);
            mfd.append('filename', file.name);
            mfd.append('total_chunks', totalChunks);

            const mres = await fetch('/upload/merge', { method: 'POST', body: mfd });
            if (!mres.ok) {
                const err = await mres.json().catch(() => ({}));
                throw new Error(err.detail || `合并失败: ${mres.status}`);
            }

            const result = await mres.json();
            if (result.success) {
                successCount++;
                connectWebSocket(result.task_id);
            } else {
                throw new Error(result.message || '上传失败');
            }

        } catch (error) {
            console.error(`Upload error for ${file.name}:`, error);
            failCount++;
            showAlert('danger', `${file.name} 上传失败: ${error.message}`);
        }
    }

    if (successCount > 0) {
        showAlert('success', `成功上传 ${successCount} 个文件${failCount > 0 ? `，${failCount} 个失败` : ''}`);
        resetUploadArea();
        setTimeout(async () => { await loadTasks(); }, 500);
    }

    uploadButton.disabled = false;
    uploadButton.innerHTML = originalButtonText;
}

// 重置上传区域
function resetUploadArea() {
    selectedFiles = [];
    videoFileInput.value = '';

    if (uploadArea) {
        uploadArea.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="upload-icon-compact me-3">
                    <i class="bi bi-cloud-arrow-up"></i>
                </div>
                <div class="flex-grow-1">
                    <h6 class="mb-1">点击或拖放视频文件</h6>
                    <small class="text-muted">支持 MP4, AVI, MOV, MKV | 可多选</small>
                </div>
            </div>
        `;
    }
}

// 智能刷新控制
function startSmartRefresh() {
    // 清除现有的定时器
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // 检查是否有进行中的任务
    const hasActiveTasks = tasks.some(task => 
        task.status === 'pending' || 
        task.status === 'processing' || 
        task.status === 'extracting_audio' || 
        task.status === 'transcribing' || 
        task.status === 'saving_results'
    );
    
    if (hasActiveTasks) {
        // 有进行中的任务，每5秒刷新一次
        refreshInterval = setInterval(loadTasks, 5000);
        console.log('📡 Smart refresh: Active tasks detected, refreshing every 5s');
    } else {
        // 没有进行中的任务，每30秒刷新一次
        refreshInterval = setInterval(loadTasks, 30000);
        console.log('💤 Smart refresh: No active tasks, refreshing every 30s');
    }
}

// 更新或添加任务到列表（避免重复）
function updateOrAddTask(taskData) {
    const taskIndex = tasks.findIndex(t => t.id === taskData.id);
    
    if (taskIndex !== -1) {
        // 任务已存在，更新它
        tasks[taskIndex] = { ...tasks[taskIndex], ...taskData };
        console.log(`🔄 Task ${taskData.id} updated`);
    } else {
        // 任务不存在，添加到列表开头
        tasks.unshift(taskData);
        console.log(`➕ Task ${taskData.id} added to list`);
    }
}

// 加载任务列表
async function loadTasks() {
    console.log('🔄 loadTasks called');
    
    // 只有当refreshButton存在时才更新其状态
    if (refreshButton) {
        refreshButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> 加载中...';
        refreshButton.disabled = true;
    }

    try {
        const response = await fetch('/tasks');
        
        if (response.ok) {
            const data = await response.json();
            console.log(`📋 Tasks loaded: ${data.length} tasks`);
            
            // 直接替换任务列表，避免重复
            tasks = data;
            
            renderTaskList();
            
            // 加载完成后，重新评估刷新频率
            startSmartRefresh();
        } else {
            const errorText = await response.text();
            console.error('Server error:', errorText);
            throw new Error(`加载任务失败: ${response.status}`);
        }
    } catch (error) {
        console.error('❌ 加载任务失败:', error);
        showAlert('danger', `加载任务列表失败: ${error.message}`);
    } finally {
        // 无论如何都要重置刷新按钮状态（如果存在）
        if (refreshButton) {
            refreshButton.disabled = false;
            refreshButton.innerHTML = '<i class="bi bi-arrow-clockwise"></i> 刷新';
        }
    }
}

// 渲染任务列表
function renderTaskList() {
    console.log('renderTaskList called');
    console.log('taskList:', taskList);
    console.log('tasks:', tasks);
    console.log('tasks.length:', tasks ? tasks.length : 'undefined');
    
    if (!taskList) {
        console.error('taskList is null');
        return;
    }

    try {
        if (!tasks || tasks.length === 0) {
        console.log('No tasks to display');
        taskList.innerHTML = `
            <div class="col-12">
                <div class="empty-state">
                    <i class="bi bi-inbox"></i>
                    <p>暂无转换任务，请上传视频文件开始使用</p>
                </div>
            </div>
        `;
        return;
    }

    console.log('Creating task cards');
    const tasksHtml = tasks.map(task => createTaskCard(task)).join('');
    console.log('tasksHtml length:', tasksHtml.length);
    taskList.innerHTML = tasksHtml;
    console.log('Task list updated');

    // 为每个任务卡片添加动画
    document.querySelectorAll('.task-card').forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('task-animation');
    });
    } catch (error) {
        console.error('Error rendering task list:', error);
        showAlert('danger', `渲染任务列表失败: ${error.message}`);
    }
}

// 创建任务卡片HTML
function createTaskCard(task) {
    return `
        <div class="col-md-6 col-lg-4 mb-3">
            <div class="card task-card h-100">
                <div class="card-body d-flex flex-column">
                    <h6 class="card-title text-truncate" title="${task.original_filename}">
                        <i class="bi bi-file-earmark-play"></i> ${escapeHtml(task.original_filename)}
                    </h6>
                    
                    <div class="mb-3">
                        <span class="badge ${getStatusBadgeClass(task.status)} status-badge">
                            ${getStatusText(task.status)}
                        </span>
                        <small class="text-muted float-end">
                            ${formatTime(task.created_at)}
                        </small>
                    </div>
                    
                    <div class="mb-3">
                        <div class="d-flex justify-content-between mb-1">
                            <small>转换进度</small>
                            <small>${task.progress}%</small>
                        </div>
                        <div class="progress">
                            <div class="progress-bar ${getProgressBarClass(task.status)}" 
                                 style="width: ${task.progress}%">
                            </div>
                        </div>
                    </div>
                    
                    ${task.error_message ? `
                        <div class="alert alert-danger alert-sm mb-3">
                            <small><i class="bi bi-exclamation-triangle"></i> ${escapeHtml(task.error_message)}</small>
                        </div>
                    ` : ''}
                    
                    <div class="mt-auto d-grid gap-2">
                        ${task.status === 'completed' ? `
                            <button class="btn btn-success btn-sm" onclick="window.previewTask('${task.id}')">
                                <i class="bi bi-eye"></i> 预览结果
                            </button>
                        ` : ''}
                        
                        ${task.audio_url ? `
                            <a href="${task.audio_url}" class="btn btn-primary btn-sm" download>
                                <i class="bi bi-music-note"></i> 下载音频
                            </a>
                        ` : ''}
                        
                        ${task.transcript_url ? `
                            <a href="${task.transcript_url}" class="btn btn-primary btn-sm" download>
                                <i class="bi bi-file-text"></i> 下载文字
                            </a>
                        ` : ''}

                        ${task.srt_url ? `
                            <a href="${task.srt_url}" class="btn btn-info btn-sm" download>
                                <i class="bi bi-file-earmark-text"></i> 下载SRT字幕
                            </a>
                        ` : ''}
                        
                        <button class="btn btn-outline-danger btn-sm" onclick="window.deleteTask('${task.id}')">
                            <i class="bi bi-trash"></i> 删除
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// 预览任务结果
window.previewTask = async function(taskId) {
    try {
        // 获取预览文本
        const previewResponse = await fetch(`/download/preview/${taskId}`);
        if (!previewResponse.ok) {
            throw new Error('获取预览内容失败');
        }

        const previewData = await previewResponse.json();

        // 设置预览内容
        if (previewText) {
            previewText.textContent = previewData.full_text || '无内容';
        }

        // 获取任务信息
        const task = tasks.find(t => t.id === taskId);
        
        // 设置音频预览
        if (previewAudio) {
            if (task && task.audio_url) {
                previewAudio.src = task.audio_url;
                previewAudio.load();
                previewAudio.parentElement.style.display = 'block';
            } else {
                previewAudio.src = '';
                previewAudio.parentElement.style.display = 'none';
            }
        }

        // 设置下载按钮
        if (downloadAudioBtn) {
            if (task && task.audio_url) {
                downloadAudioBtn.href = task.audio_url;
                downloadAudioBtn.download = `${task.original_filename.replace(/\.[^/.]+$/, "")}.mp3`;
                downloadAudioBtn.style.display = 'inline-block';
                downloadAudioBtn.classList.remove('disabled');
            } else {
                downloadAudioBtn.style.display = 'none';
            }
        }

        if (downloadTextBtn) {
            if (task && task.transcript_url) {
                downloadTextBtn.href = task.transcript_url;
                downloadTextBtn.download = `${task.original_filename.replace(/\.[^/.]+$/, "")}.txt`;
                downloadTextBtn.style.display = 'inline-block';
                downloadTextBtn.classList.remove('disabled');
            } else {
                downloadTextBtn.style.display = 'none';
            }
        }

        // 显示模态框
        if (previewModal) {
            previewModal.show();
        }

    } catch (error) {
        console.error('预览失败:', error);
        showAlert('danger', '预览失败: ' + error.message);
    }
};

// 删除任务
window.deleteTask = async function(taskId) {
    if (!confirm('确定要删除这个任务吗？相关的音频和文本文件也会被删除。')) {
        return;
    }

    try {
        const response = await fetch(`/tasks/${taskId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showAlert('success', '删除成功');
            // 从本地任务列表中移除
            tasks = tasks.filter(t => t.id !== taskId);
            renderTaskList();

            // 关闭WebSocket连接
            if (wsConnections[taskId]) {
                wsConnections[taskId].close();
                delete wsConnections[taskId];
            }
        } else {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || '删除失败');
        }
    } catch (error) {
        console.error('删除失败:', error);
        showAlert('danger', `删除失败: ${error.message}`);
    }
};

// 连接到WebSocket
function connectWebSocket(taskId) {
    // 如果已经存在连接，先关闭
    if (wsConnections[taskId]) {
        wsConnections[taskId].close();
    }

    // 获取WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${taskId}`;
    console.log(`Attempting to connect WebSocket to: ${wsUrl}`);

    try {
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log(`✅ WebSocket connected for task ${taskId}`);

            // 发送初始状态请求
            ws.send(JSON.stringify({
                type: "get_status",
                task_id: taskId
            }));
        };

        ws.onmessage = (event) => {
            console.log(`📩 WebSocket message received for task ${taskId}:`, event.data);
            try {
                const data = JSON.parse(event.data);
                console.log(`📋 Parsed WebSocket message:`, data);

                // 检查是否是进度更新消息
                if (data.type === 'progress_update') {
                    console.log(`📊 Progress update received for task ${taskId}: ${data.progress}%`);
                    // 使用包含进度数据的任务信息更新
                    const taskData = data.task_data;
                    
                    // 更新或添加任务到本地列表
                    updateOrAddTask(taskData);
                    
                    // 重新渲染任务列表
                    console.log(`🎨 Calling renderTaskList()`);
                    renderTaskList();
                    console.log(`✅ renderTaskList() completed`);
                } else {
                    // 处理其他类型的消息（如状态更新）
                    console.log(`📝 Status update received for task ${taskId}: ${data.status}`);
                    
                    // 更新或添加任务到本地列表
                    updateOrAddTask(data);
                    
                    // 重新渲染任务列表
                    renderTaskList();
                }

                // 如果任务完成，关闭WebSocket连接
                if (data.status === 'completed' || data.status === 'failed') {
                    console.log(`🏁 Task ${taskId} completed/failed, scheduling WebSocket close`);
                    setTimeout(() => {
                        if (wsConnections[taskId]) {
                            console.log(`🔌 Closing WebSocket for task ${taskId}`);
                            wsConnections[taskId].close();
                            delete wsConnections[taskId];
                            console.log(`✅ WebSocket closed and removed from connections list`);
                        }
                    }, 5000); // 5秒后关闭连接
                }

            } catch (error) {
                console.error('❌ WebSocket消息解析失败:', error);
                console.error('❌ 原始消息:', event.data);
            }
        };

        ws.onerror = (error) => {
            console.error(`❌ WebSocket error for task ${taskId}:`, error);
        };

        ws.onclose = (event) => {
            console.log(`🔌 WebSocket disconnected for task ${taskId}`, event);
            delete wsConnections[taskId];
            console.log(`✅ WebSocket removed from connections list`);
        };

        wsConnections[taskId] = ws;
        console.log(`✅ WebSocket connection object created and stored for task ${taskId}`);

    } catch (error) {
        console.error('WebSocket连接失败:', error);
    }
}

// 辅助函数
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatTime(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        return '未知时间';
    }
}

function getStatusText(status) {
    const statusMap = {
        'pending': '等待中',
        'processing': '处理中',
        'extracting_audio': '提取音频',
        'transcribing': '转录音频',
        'saving_results': '保存结果',
        'completed': '已完成',
        'failed': '失败'
    };
    return statusMap[status] || status;
}

function getStatusBadgeClass(status) {
    const classMap = {
        'pending': 'bg-secondary',
        'processing': 'bg-primary',
        'extracting_audio': 'bg-info',
        'transcribing': 'bg-warning',
        'saving_results': 'bg-info',
        'completed': 'bg-success',
        'failed': 'bg-danger'
    };
    return classMap[status] || 'bg-secondary';
}

function getProgressBarClass(status) {
    const classMap = {
        'pending': 'bg-secondary',
        'processing': 'progress-bar-animated progress-bar-striped bg-primary',
        'extracting_audio': 'progress-bar-animated progress-bar-striped bg-info',
        'transcribing': 'progress-bar-animated progress-bar-striped bg-warning',
        'saving_results': 'progress-bar-animated progress-bar-striped bg-info',
        'completed': 'bg-success',
        'failed': 'bg-danger'
    };
    return classMap[status] || 'bg-secondary';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 显示提示消息
function showAlert(type, message) {
    const alertId = 'global-alert-' + Date.now();

    const alertDiv = document.createElement('div');
    alertDiv.id = alertId;
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 500px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;

    alertDiv.innerHTML = `
        <div class="d-flex align-items-start">
            <div class="flex-grow-1">
                ${message}
            </div>
            <button type="button" class="btn-close ms-2" onclick="document.getElementById('${alertId}').remove()"></button>
        </div>
    `;

    document.body.appendChild(alertDiv);

    // 自动移除
    setTimeout(() => {
        const element = document.getElementById(alertId);
        if (element) {
            element.remove();
        }
    }, 5000);
}

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    // 清除定时器
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }

    // 关闭所有WebSocket连接
    Object.values(wsConnections).forEach(ws => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close();
        }
    });

    wsConnections = {};
});

// 导出到全局作用域
window.resetUploadArea = resetUploadArea;
window.loadTasks = loadTasks;