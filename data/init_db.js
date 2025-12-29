// MongoDB初始化脚本
// 创建数据库和集合，设置索引

// 切换到smart_home数据库
db = db.getSiblingDB('smart_home');

// 创建用户（如果使用认证）
db.createUser({
  user: 'smart_home_user',
  pwd: 'smart_home_pass',
  roles: [
    {
      role: 'readWrite',
      db: 'smart_home'
    }
  ]
});

// 创建设备集合
db.createCollection('devices');

// 创建日志集合
db.createCollection('device_logs');

// 为devices集合创建索引
// 1. 地理位置索引（2dsphere）- 用于地理位置查询
db.devices.createIndex(
  { location: '2dsphere' },
  { name: 'location_2dsphere_idx' }
);

// 2. 设备类型索引
db.devices.createIndex(
  { type: 1 },
  { name: 'type_idx' }
);

// 3. 设备状态索引
db.devices.createIndex(
  { status: 1 },
  { name: 'status_idx' }
);

// 4. 设备ID唯一索引
db.devices.createIndex(
  { device_id: 1 },
  { unique: true, name: 'device_id_unique_idx' }
);

// 为device_logs集合创建索引
// 1. TTL索引 - 自动删除90天前的日志
db.device_logs.createIndex(
  { timestamp: 1 },
  { 
    expireAfterSeconds: 7776000, // 90天 = 90 * 24 * 60 * 60秒
    name: 'timestamp_ttl_idx' 
  }
);

// 2. 复合索引 - 设备ID + 时间戳（优化查询性能）
db.device_logs.createIndex(
  { device_id: 1, timestamp: -1 },
  { name: 'device_timestamp_idx' }
);

// 3. 日志类型索引
db.device_logs.createIndex(
  { log_type: 1 },
  { name: 'log_type_idx' }
);

// 4. 全文搜索索引（在日志内容上）
db.device_logs.createIndex(
  { 'content.message': 'text', 'content.details': 'text' },
  { name: 'log_content_text_idx' }
);

print('数据库初始化完成！');
print('已创建集合: devices, device_logs');
print('已创建索引: 地理位置索引、TTL索引、复合索引、全文搜索索引');


