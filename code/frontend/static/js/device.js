const API_BASE = '/api/devices';

// 页面加载时获取设备列表
document.addEventListener('DOMContentLoaded', function() {
    loadDevices();
});

// 加载设备列表
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

// 显示设备列表
function displayDevices(devices) {
    const tbody = document.getElementById('deviceTableBody');
    
    if (devices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无设备数据</td></tr>';
        return;
    }
    
    tbody.innerHTML = devices.map(device => {
        const statusClass = device.status === 'online' ? 'status-online' : 
                           device.status === 'offline' ? 'status-offline' : 'status-maintenance';
        const statusText = device.status === 'online' ? '在线' : 
                          device.status === 'offline' ? '离线' : '维护中';
        const location = device.location?.coordinates ? 
            `${device.location.coordinates[1].toFixed(6)}, ${device.location.coordinates[0].toFixed(6)}` : 
            '未知';
        const createdAt = device.created_at ? new Date(device.created_at).toLocaleString('zh-CN') : '-';
        
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
    }).join('');
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

// 查询附近设备
function searchNearbyDevices() {
    const longitude = parseFloat(document.getElementById('longitude').value);
    const latitude = parseFloat(document.getElementById('latitude').value);
    const maxDistance = parseFloat(document.getElementById('maxDistance').value) || 1000;
    
    if (isNaN(longitude) || isNaN(latitude)) {
        alert('请输入有效的经纬度');
        return;
    }
    
    const url = `${API_BASE}/nearby?longitude=${longitude}&latitude=${latitude}&max_distance=${maxDistance}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`找到 ${data.count} 个附近设备`);
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

// 加载设备统计信息
function loadDeviceStats() {
    fetch(`${API_BASE}/stats`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const stats = data.data;
                let html = `<h6>总设备数: ${stats.total}</h6>`;
                html += '<h6 class="mt-3">按类型统计:</h6><ul>';
                stats.by_type.forEach(item => {
                    html += `<li>${item._id}: ${item.count} 个</li>`;
                });
                html += '</ul>';
                html += '<h6 class="mt-3">按状态统计:</h6><ul>';
                stats.by_status.forEach(item => {
                    html += `<li>${item._id}: ${item.count} 个</li>`;
                });
                html += '</ul>';
                
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

