const API_BASE = '/api/logs';
let currentPage = 1;
let typeChart = null;
let hourlyChart = null;

// 页面加载时获取日志列表和统计信息
document.addEventListener('DOMContentLoaded', function() {
    loadLogs();
    loadLogStats();
});

// 加载日志列表
function loadLogs(page = 1) {
    currentPage = page;
    const deviceId = document.getElementById('logDeviceId').value;
    const logType = document.getElementById('logType').value;
    let startTime = document.getElementById('startTime').value;
    let endTime = document.getElementById('endTime').value;
    
    // 转换datetime-local格式为后端期望的格式
    // datetime-local返回格式: "YYYY-MM-DDTHH:mm"
    // 后端期望格式: "YYYY-MM-DDTHH:MM:SS" 或 "YYYY-MM-DD HH:MM:SS"
    if (startTime) {
        // 如果只有日期时间，添加秒数
        if (startTime.length === 16) {
            startTime += ':00';
        }
        // 将T替换为空格（后端支持两种格式）
        startTime = startTime.replace('T', ' ');
    }
    if (endTime) {
        if (endTime.length === 16) {
            endTime += ':00';
        }
        endTime = endTime.replace('T', ' ');
    }
    
    let url = `${API_BASE}?page=${page}&per_page=50`;
    if (deviceId) url += `&device_id=${encodeURIComponent(deviceId)}`;
    if (logType) url += `&log_type=${encodeURIComponent(logType)}`;
    if (startTime) url += `&start_time=${encodeURIComponent(startTime)}`;
    if (endTime) url += `&end_time=${encodeURIComponent(endTime)}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayLogs(data.data);
                displayPagination(data.pagination);
            } else {
                alert('加载日志失败: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('logTableBody').innerHTML = 
                '<tr><td colspan="6" class="text-center text-danger">加载失败，请检查服务器连接</td></tr>';
        });
}

// 显示日志列表
function displayLogs(logs) {
    const tbody = document.getElementById('logTableBody');
    
    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">暂无日志数据</td></tr>';
        return;
    }
    
    tbody.innerHTML = logs.map(log => {
        const typeClass = log.log_type === 'error' ? 'bg-danger' : 
                         log.log_type === 'warning' ? 'bg-warning' : 
                         log.log_type === 'status_change' ? 'bg-info' : 'bg-secondary';
        const typeText = log.log_type === 'error' ? '错误' : 
                        log.log_type === 'warning' ? '警告' : 
                        log.log_type === 'status_change' ? '状态变更' : '信息';
        const timestamp = log.timestamp ? new Date(log.timestamp).toLocaleString('zh-CN') : '-';
        const details = log.content?.details ? JSON.stringify(log.content.details) : '-';
        
        return `
            <tr>
                <td><small>${timestamp}</small></td>
                <td>${log.device_id}</td>
                <td><span class="badge ${typeClass}">${typeText}</span></td>
                <td>${log.content?.message || '-'}</td>
                <td><small class="text-muted">${details.length > 50 ? details.substring(0, 50) + '...' : details}</small></td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="deleteLog('${log._id}')">
                        <i class="bi bi-trash"></i> 删除
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// 显示分页
function displayPagination(pagination) {
    const paginationEl = document.getElementById('pagination');
    const pages = pagination.pages;
    
    if (pages <= 1) {
        paginationEl.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // 上一页
    html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="loadLogs(${currentPage - 1}); return false;">上一页</a>
    </li>`;
    
    // 页码
    for (let i = 1; i <= pages; i++) {
        if (i === 1 || i === pages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            html += `<li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="loadLogs(${i}); return false;">${i}</a>
            </li>`;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }
    
    // 下一页
    html += `<li class="page-item ${currentPage === pages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="loadLogs(${currentPage + 1}); return false;">下一页</a>
    </li>`;
    
    paginationEl.innerHTML = html;
}

// 删除日志
function deleteLog(logId) {
    if (!confirm('确定要删除这条日志吗？')) {
        return;
    }
    
    fetch(`${API_BASE}/${logId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('日志删除成功');
            loadLogs(currentPage);
        } else {
            alert('删除失败: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('删除失败');
    });
}

// 打开添加日志模态框
function openAddLogModal() {
    document.getElementById('logForm').reset();
}

// 保存日志
function saveLog() {
    const deviceId = document.getElementById('logDeviceIdInput').value;
    const logType = document.getElementById('logTypeInput').value;
    const message = document.getElementById('logMessage').value;
    const detailsText = document.getElementById('logDetails').value;
    
    let details = {};
    if (detailsText.trim()) {
        try {
            details = JSON.parse(detailsText);
        } catch (e) {
            alert('详细信息JSON格式错误');
            return;
        }
    }
    
    const logData = {
        device_id: deviceId,
        log_type: logType,
        message: message,
        details: details
    };
    
    fetch(API_BASE, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(logData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('日志添加成功');
            bootstrap.Modal.getInstance(document.getElementById('logModal')).hide();
            loadLogs();
            loadLogStats();
        } else {
            alert('添加失败: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('添加失败');
    });
}

// 重置筛选条件
function resetFilters() {
    document.getElementById('logDeviceId').value = '';
    document.getElementById('logType').value = '';
    document.getElementById('startTime').value = '';
    document.getElementById('endTime').value = '';
    loadLogs(1);
}

// 全文搜索
function searchLogs() {
    const keyword = document.getElementById('searchKeyword').value;
    if (!keyword.trim()) {
        alert('请输入搜索关键词');
        return;
    }
    
    fetch(`${API_BASE}/search?keyword=${encodeURIComponent(keyword)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayLogs(data.data);
                document.getElementById('pagination').innerHTML = '';
            } else {
                alert('搜索失败: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('搜索失败');
        });
}

// 加载日志统计信息
function loadLogStats() {
    let startTime = document.getElementById('startTime').value;
    let endTime = document.getElementById('endTime').value;
    
    // 转换datetime-local格式
    if (startTime) {
        if (startTime.length === 16) {
            startTime += ':00';
        }
        startTime = startTime.replace('T', ' ');
    }
    if (endTime) {
        if (endTime.length === 16) {
            endTime += ':00';
        }
        endTime = endTime.replace('T', ' ');
    }
    
    let url = `${API_BASE}/stats`;
    const params = [];
    if (startTime) params.push(`start_time=${encodeURIComponent(startTime)}`);
    if (endTime) params.push(`end_time=${encodeURIComponent(endTime)}`);
    if (params.length > 0) {
        url += '?' + params.join('&');
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCharts(data.data);
            } else {
                console.error('加载统计信息失败: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// 更新图表
function updateCharts(stats) {
    // 按类型统计图表
    const typeCtx = document.getElementById('typeChart').getContext('2d');
    if (typeChart) {
        typeChart.destroy();
    }
    
    const typeLabels = stats.by_type.map(item => {
        const typeMap = {
            'info': '信息',
            'warning': '警告',
            'error': '错误',
            'status_change': '状态变更'
        };
        return typeMap[item._id] || item._id;
    });
    const typeData = stats.by_type.map(item => item.count);
    
    typeChart = new Chart(typeCtx, {
        type: 'doughnut',
        data: {
            labels: typeLabels,
            datasets: [{
                data: typeData,
                backgroundColor: [
                    '#28a745',
                    '#ffc107',
                    '#dc3545',
                    '#17a2b8'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: '按类型统计'
                }
            }
        }
    });
    
    // 按小时统计图表
    const hourlyCtx = document.getElementById('hourlyChart').getContext('2d');
    if (hourlyChart) {
        hourlyChart.destroy();
    }
    
    const hourlyLabels = stats.hourly.map(item => {
        const date = new Date(item._id.year, item._id.month - 1, item._id.day, item._id.hour);
        return date.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit' });
    });
    const hourlyData = stats.hourly.map(item => item.count);
    
    hourlyChart = new Chart(hourlyCtx, {
        type: 'line',
        data: {
            labels: hourlyLabels,
            datasets: [{
                label: '日志数量',
                data: hourlyData,
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: '按小时统计'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

