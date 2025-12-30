/**
 * 设备管理前端JavaScript模块
 * 
 * 本模块实现了设备管理页面的所有前端交互功能，包括：
 * 1. 设备列表的加载和显示
 * 2. 设备的增删改查操作
 * 3. 设备筛选和搜索
 * 4. 地理位置查询（附近设备）
 * 5. 设备统计信息展示
 * 
 * API基础路径：/api/devices
 * 
 * 作者: 数据库系统课程项目小组
 */

// ==================== API配置 ====================
// 设备管理API的基础路径
const API_BASE = '/api/devices';

// ==================== 页面初始化 ====================
// 页面加载完成后自动加载设备列表
document.addEventListener('DOMContentLoaded', function() {
    loadDevices();
});

// ==================== 设备列表加载 ====================
/**
 * 加载设备列表
 * 
 * 从服务器获取设备列表，支持以下筛选条件：
 * - type: 设备类型筛选
 * - status: 设备状态筛选
 * - search: 搜索关键词（设备ID或名称）
 * 
 * 功能：
 * 1. 获取筛选条件
 * 2. 构建API请求URL
 * 3. 发送GET请求获取设备列表
 * 4. 调用displayDevices()显示设备列表
 */
function loadDevices() {
    const type = document.getElementById('filterType').value;
    const status = document.getElementById('filterStatus').value;
    const searchKeyword = document.getElementById('searchInput')?.value?.trim() || '';
    
    let url = API_BASE;
    const params = [];
    if (type) params.push(`type=${encodeURIComponent(type)}`);
    if (status) params.push(`status=${encodeURIComponent(status)}`);
    if (searchKeyword) params.push(`search=${encodeURIComponent(searchKeyword)}`);
    if (params.length > 0) {
        url += '?' + params.join('&');
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayDevices(data.data);
            } else {
                alert('加载设备失败: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('deviceTableBody').innerHTML = 
                '<tr><td colspan="7" class="text-center text-danger">加载失败，请检查服务器连接</td></tr>';
        });
}

/**
 * 显示设备列表
 * 
 * 将设备数据渲染到HTML表格中，包括：
 * - 设备ID、名称、类型、状态
 * - 地理位置（经纬度）
 * - 创建时间
 * - 操作按钮（编辑、删除）
 * 
 * @param {Array} devices - 设备对象数组
 */
function displayDevices(devices) {
    const tbody = document.getElementById('deviceTableBody');
    
    // 如果没有设备数据，显示提示信息
    if (devices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无设备数据</td></tr>';
        return;
    }
    
    // 将设备数据转换为HTML表格行
    tbody.innerHTML = devices.map(device => {
        // 根据设备状态设置CSS类和显示文本
        const statusClass = device.status === 'online' ? 'status-online' : 
                           device.status === 'offline' ? 'status-offline' : 'status-maintenance';
        const statusText = device.status === 'online' ? '在线' : 
                          device.status === 'offline' ? '离线' : '维护中';
        
        // 格式化地理位置显示
        // location.coordinates格式：[经度, 纬度]
        // 显示格式：纬度, 经度（更符合常见的地图显示习惯）
        const location = device.location?.coordinates ? 
            `${device.location.coordinates[1].toFixed(6)}, ${device.location.coordinates[0].toFixed(6)}` : 
            '未知';
        
        // 格式化创建时间
        const createdAt = device.created_at ? new Date(device.created_at).toLocaleString('zh-CN') : '-';
        
        // 返回表格行HTML
        return `
            <tr>
                <td>${device.device_id}</td>
                <td>${device.name}</td>
                <td><span class="badge bg-secondary">${device.type}</span></td>
                <td><span class="badge ${statusClass}">${statusText}</span></td>
                <td><small>${location}</small></td>
                <td><small>${createdAt}</small></td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="editDevice('${device.device_id}')">
                        <i class="bi bi-pencil"></i> 编辑
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteDevice('${device.device_id}')">
                        <i class="bi bi-trash"></i> 删除
                    </button>
                </td>
            </tr>
        `;
    }).join('');  // 将数组转换为字符串
}

// 打开添加设备模态框
function openAddModal() {
    document.getElementById('modalTitle').textContent = '添加设备';
    document.getElementById('deviceForm').reset();
    document.getElementById('editDeviceId').value = '';
    document.getElementById('deviceId').disabled = false;
}

// 编辑设备
function editDevice(deviceId) {
    fetch(`${API_BASE}/${deviceId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const device = data.data;
                document.getElementById('modalTitle').textContent = '编辑设备';
                document.getElementById('editDeviceId').value = device.device_id;
                document.getElementById('deviceId').value = device.device_id;
                document.getElementById('deviceId').disabled = true;
                document.getElementById('deviceName').value = device.name;
                document.getElementById('deviceType').value = device.type;
                document.getElementById('deviceStatus').value = device.status;
                
                if (device.location?.coordinates) {
                    document.getElementById('deviceLongitude').value = device.location.coordinates[0];
                    document.getElementById('deviceLatitude').value = device.location.coordinates[1];
                }
                
                document.getElementById('deviceConfig').value = JSON.stringify(device.config || {}, null, 2);
                
                const modal = new bootstrap.Modal(document.getElementById('deviceModal'));
                modal.show();
            } else {
                alert('获取设备信息失败: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('获取设备信息失败');
        });
}

// 保存设备
function saveDevice() {
    const editId = document.getElementById('editDeviceId').value;
    const deviceId = document.getElementById('deviceId').value;
    const name = document.getElementById('deviceName').value;
    const type = document.getElementById('deviceType').value;
    const status = document.getElementById('deviceStatus').value;
    const longitude = parseFloat(document.getElementById('deviceLongitude').value);
    const latitude = parseFloat(document.getElementById('deviceLatitude').value);
    const configText = document.getElementById('deviceConfig').value;
    
    let config = {};
    if (configText.trim()) {
        try {
            config = JSON.parse(configText);
        } catch (e) {
            alert('配置JSON格式错误');
            return;
        }
    }
    
    const deviceData = {
        device_id: deviceId,
        name: name,
        type: type,
        status: status,
        location: {
            longitude: longitude,
            latitude: latitude
        },
        config: config
    };
    
    const method = editId ? 'PUT' : 'POST';
    const url = editId ? `${API_BASE}/${deviceId}` : API_BASE;
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(deviceData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message || '操作成功');
            bootstrap.Modal.getInstance(document.getElementById('deviceModal')).hide();
            loadDevices();
        } else {
            alert('操作失败: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('操作失败');
    });
}

// 删除设备
function deleteDevice(deviceId) {
    if (!confirm(`确定要删除设备 ${deviceId} 吗？`)) {
        return;
    }
    
    fetch(`${API_BASE}/${deviceId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('设备删除成功');
            loadDevices();
        } else {
            alert('删除失败: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('删除失败');
    });
}

/**
 * 查询附近设备（地理位置查询）
 * 
 * 使用MongoDB的$near操作符查询指定位置附近的设备。
 * 这是MongoDB文档数据库的特色功能，利用2dsphere索引实现高效的地理位置查询。
 * 
 * 功能：
 * 1. 获取用户输入的经纬度和最大距离
 * 2. 验证输入的有效性
 * 3. 调用API查询附近设备
 * 4. 显示查询结果
 * 
 * 注意：
 * - 经纬度必须是有效的数值
 * - 最大距离单位：米
 * - 查询结果按距离从近到远排序
 */
function searchNearbyDevices() {
    // 获取用户输入的经纬度和最大距离
    const longitude = parseFloat(document.getElementById('longitude').value);
    const latitude = parseFloat(document.getElementById('latitude').value);
    const maxDistance = parseFloat(document.getElementById('maxDistance').value) || 1000;  // 默认1000米
    
    // 验证输入有效性
    if (isNaN(longitude) || isNaN(latitude)) {
        alert('请输入有效的经纬度');
        return;
    }
    
    // 构建API请求URL
    // 使用MongoDB的$near查询，需要提供中心点坐标和最大距离
    const url = `${API_BASE}/nearby?longitude=${longitude}&latitude=${latitude}&max_distance=${maxDistance}`;
    
    // 发送GET请求
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 显示查询结果数量
                alert(`找到 ${data.count} 个附近设备`);
                // 显示设备列表（按距离排序）
                displayDevices(data.data);
            } else {
                alert('查询失败: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('查询失败');
        });
}

/**
 * 加载设备统计信息
 * 
 * 调用API获取设备统计信息，使用MongoDB聚合查询实现。
 * 统计信息包括：
 * 1. 总设备数
 * 2. 按类型统计（使用$group聚合）
 * 3. 按状态统计（使用$group聚合）
 * 
 * 功能：
 * 1. 调用统计API
 * 2. 格式化统计结果
 * 3. 在模态框中显示统计信息
 */
function loadDeviceStats() {
    // 调用统计API
    fetch(`${API_BASE}/stats`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stats = data.data;
                
                // 构建统计信息HTML
                let html = `<h6>总设备数: ${stats.total}</h6>`;
                
                // 按类型统计
                html += '<h6 class="mt-3">按类型统计:</h6><ul>';
                stats.by_type.forEach(item => {
                    html += `<li>${item._id}: ${item.count} 个</li>`;
                });
                html += '</ul>';
                
                // 按状态统计
                html += '<h6 class="mt-3">按状态统计:</h6><ul>';
                stats.by_status.forEach(item => {
                    html += `<li>${item._id}: ${item.count} 个</li>`;
                });
                html += '</ul>';
                
                // 显示统计信息模态框
                document.getElementById('statsContent').innerHTML = html;
                const modal = new bootstrap.Modal(document.getElementById('statsModal'));
                modal.show();
            } else {
                alert('加载统计信息失败: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('加载统计信息失败');
        });
}

