/**
 * 日志查询前端JavaScript模块
 * 
 * 本模块实现了日志查询页面的所有前端交互功能，包括：
 * 1. 日志列表的加载和显示（支持分页）
 * 2. 日志的增删操作
 * 3. 日志筛选（设备ID、类型、时间范围）
 * 4. 全文搜索（MongoDB文本索引）
 * 5. 日志统计信息展示（使用Chart.js可视化）
 * 
 * API基础路径：/api/logs
 * 
 * 作者: 数据库系统课程项目小组
 */

// ==================== API配置 ====================
const API_BASE = '/api/logs';

// ==================== 全局变量 ====================
let currentPage = 1;  // 当前页码
let typeChart = null;  // 日志类型统计图表对象（Chart.js）
let hourlyChart = null;  // 按小时统计图表对象（Chart.js）

// ==================== 页面初始化 ====================
// 页面加载完成后自动加载日志列表和统计信息
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

/**
 * 全文搜索日志
 * 
 * 使用MongoDB的文本索引实现全文搜索功能。
 * 这是MongoDB文档数据库的特色功能，可以在日志内容中搜索关键词。
 * 
 * 功能：
 * 1. 获取搜索关键词
 * 2. 调用全文搜索API
 * 3. 显示搜索结果（按相关性排序）
 * 4. 清空分页（全文搜索不支持分页）
 * 
 * MongoDB全文搜索原理：
 * - 使用$text操作符进行全文搜索
 * - 结果按相关性评分（textScore）排序
 * - 需要在MongoDB中创建文本索引
 */
function searchLogs() {
    // 获取搜索关键词
    const keyword = document.getElementById('searchKeyword').value;
    if (!keyword.trim()) {
        alert('请输入搜索关键词');
        return;
    }
    
    // 调用全文搜索API
    // encodeURIComponent: 对关键词进行URL编码，防止特殊字符导致URL错误
    fetch(`${API_BASE}/search?keyword=${encodeURIComponent(keyword)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 显示搜索结果（按相关性排序）
                displayLogs(data.data);
                // 清空分页（全文搜索不支持分页）
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

/**
 * 更新统计图表
 * 
 * 使用Chart.js库将MongoDB聚合查询的结果可视化。
 * 包括两个图表：
 * 1. 按类型统计（饼图/环形图）
 * 2. 按小时统计（折线图，时间序列分析）
 * 
 * @param {Object} stats - 统计信息对象
 * @param {Array} stats.by_type - 按类型统计结果
 * @param {Array} stats.hourly - 按小时统计结果
 */
function updateCharts(stats) {
    // ==================== 按类型统计图表（环形图） ====================
    const typeCtx = document.getElementById('typeChart').getContext('2d');
    // 如果图表已存在，先销毁（避免重复创建）
    if (typeChart) {
        typeChart.destroy();
    }
    
    // 将日志类型代码转换为中文标签
    const typeLabels = stats.by_type.map(item => {
        const typeMap = {
            'info': '信息',
            'warning': '警告',
            'error': '错误',
            'status_change': '状态变更'
        };
        return typeMap[item._id] || item._id;
    });
    // 提取统计数据
    const typeData = stats.by_type.map(item => item.count);
    
    // 创建环形图（doughnut chart）
    typeChart = new Chart(typeCtx, {
        type: 'doughnut',  // 图表类型：环形图
        data: {
            labels: typeLabels,  // 标签（日志类型）
            datasets: [{
                data: typeData,  // 数据（数量）
                backgroundColor: [  // 颜色配置
                    '#28a745',  // 绿色（信息）
                    '#ffc107',  // 黄色（警告）
                    '#dc3545',  // 红色（错误）
                    '#17a2b8'   // 蓝色（状态变更）
                ]
            }]
        },
        options: {
            responsive: true,  // 响应式布局
            maintainAspectRatio: true,  // 保持宽高比
            plugins: {
                title: {
                    display: true,
                    text: '按类型统计'
                }
            }
        }
    });
    
    // ==================== 按小时统计图表（折线图） ====================
    const hourlyCtx = document.getElementById('hourlyChart').getContext('2d');
    // 如果图表已存在，先销毁
    if (hourlyChart) {
        hourlyChart.destroy();
    }
    
    // 格式化时间标签
    // stats.hourly中的_id包含year、month、day、hour字段
    const hourlyLabels = stats.hourly.map(item => {
        const date = new Date(item._id.year, item._id.month - 1, item._id.day, item._id.hour);
        return date.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit' });
    });
    // 提取每小时的数量
    const hourlyData = stats.hourly.map(item => item.count);
    
    // 创建折线图（line chart）
    hourlyChart = new Chart(hourlyCtx, {
        type: 'line',  // 图表类型：折线图
        data: {
            labels: hourlyLabels,  // X轴标签（时间）
            datasets: [{
                label: '日志数量',
                data: hourlyData,  // Y轴数据（数量）
                borderColor: '#007bff',  // 线条颜色
                backgroundColor: 'rgba(0, 123, 255, 0.1)',  // 填充颜色（半透明）
                tension: 0.4  // 曲线平滑度（0-1，0.4表示平滑曲线）
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
                    beginAtZero: true  // Y轴从0开始
                }
            }
        }
    });
}

