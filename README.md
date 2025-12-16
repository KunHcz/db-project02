# 智能家居设备日志管理系统

基于MongoDB的智能家居设备日志管理系统，展示文档数据库在物联网场景下的优势。

## 项目概述

本项目是一个智能家居设备日志管理系统，使用MongoDB作为文档数据库，实现了设备管理、日志记录、地理位置查询、时间序列分析等核心功能。系统采用B/S架构，前端使用HTML+JavaScript+Bootstrap，后端使用Python Flask框架。

## 技术栈

- **数据库**: MongoDB 6.0+ (Docker部署)
- **后端**: Python 3.10 + Flask 3.0
- **前端**: HTML5 + JavaScript + Bootstrap 5.3
- **部署**: Docker Compose
- **数据可视化**: Chart.js

## 项目结构

```
db-project02/
├── data/
│   ├── init_db.js          # MongoDB初始化脚本（创建集合和索引）
│   ├── backup/             # 数据库备份目录
│   └── .gitkeep
├── code/
│   ├── backend/
│   │   ├── app.py          # Flask主应用
│   │   ├── models.py       # 数据模型定义
│   │   ├── utils.py        # 工具函数
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── device_routes.py  # 设备管理路由
│   │   │   └── log_routes.py     # 日志管理路由
│   │   └── requirements.txt
│   ├── frontend/
│   │   ├── index.html      # 设备管理页面
│   │   ├── logs.html       # 日志查询页面
│   │   └── static/
│   │       ├── css/
│   │       │   └── style.css
│   │       └── js/
│   │           ├── device.js
│   │           └── logs.js
│   └── scripts/
│       ├── import_data.py  # 数据导入脚本
│       └── backup_db.py    # 数据库备份脚本
├── docker-compose.yml      # Docker编排配置
├── Dockerfile              # 后端服务Dockerfile
└── README.md               # 项目说明文档
```

## 核心功能

### 1. 设备管理
- 设备的增删改查（CRUD操作）
- 设备类型筛选和状态筛选
- 设备地理位置查询（2dsphere索引）
- 附近设备查询（基于地理位置）
- 设备统计信息

### 2. 日志管理
- 日志的增删改查
- 日志类型筛选（info/warning/error/status_change）
- 时间范围查询
- 全文搜索（文本索引）
- 日志统计分析（聚合查询）
- 分页显示

### 3. MongoDB特色功能展示

#### 标志性实践1: 文档插入与内嵌文档
- 设备信息使用内嵌文档存储配置信息
- 日志记录使用内嵌文档存储详细信息

#### 标志性实践2: 地理位置索引与查询
- 创建2dsphere索引支持地理位置查询
- 实现$near查询查找附近设备
- 支持$geoWithin查询指定区域内的设备

#### 标志性实践3: 时间序列索引与TTL
- 创建TTL索引自动清理90天前的日志
- 时间范围查询优化

#### 标志性实践4: 聚合管道查询
- 按设备类型统计日志数量
- 按时间段聚合日志数据（按小时）
- 计算设备平均状态变化频率

#### 标志性实践5: 全文搜索
- 在日志内容上创建文本索引
- 实现日志内容全文搜索功能

## 快速开始

### 前置要求

- Docker 和 Docker Compose
- Python 3.10+ (如果本地运行)

### 使用Docker部署（推荐）

1. **启动服务**

```bash
docker-compose up -d
```

这将启动MongoDB和Flask后端服务。

2. **导入示例数据**

```bash
# 进入后端容器
docker exec -it smart_home_backend bash

# 运行数据导入脚本
cd /app
python ../scripts/import_data.py
```

或者从宿主机运行（需要安装pymongo）：

```bash
cd code/scripts
python import_data.py
```

3. **访问系统**

- 前端页面: http://localhost:5001
- API健康检查: http://localhost:5001/api/health

### 本地开发部署

1. **启动MongoDB**

```bash
docker-compose up -d mongodb
```

2. **安装Python依赖**

```bash
cd code/backend
pip install -r requirements.txt
```

3. **设置环境变量**

```bash
export MONGO_HOST=localhost
export MONGO_PORT=27017
export MONGO_USERNAME=admin
export MONGO_PASSWORD=admin123
export MONGO_DATABASE=smart_home
```

4. **启动后端服务**

```bash
python app.py
```

5. **导入数据**

```bash
cd ../../code/scripts
python import_data.py
```

## 数据库备份与恢复

### 创建备份

```bash
cd code/scripts
python backup_db.py backup
```

### 列出所有备份

```bash
python backup_db.py list
```

### 恢复备份

```bash
python backup_db.py restore smart_home_backup_20240101_120000
```

## API接口文档

### 设备管理接口

- `GET /api/devices` - 获取所有设备
  - 查询参数: `type`, `status`
- `GET /api/devices/:device_id` - 获取单个设备
- `POST /api/devices` - 创建设备
- `PUT /api/devices/:device_id` - 更新设备
- `DELETE /api/devices/:device_id` - 删除设备
- `GET /api/devices/nearby` - 查询附近设备
  - 查询参数: `longitude`, `latitude`, `max_distance`, `limit`
- `GET /api/devices/stats` - 获取设备统计信息

### 日志管理接口

- `GET /api/logs` - 查询日志
  - 查询参数: `device_id`, `log_type`, `start_time`, `end_time`, `page`, `per_page`
- `POST /api/logs` - 创建日志
- `DELETE /api/logs/:log_id` - 删除日志
- `GET /api/logs/stats` - 获取日志统计信息（聚合查询）
- `GET /api/logs/search` - 全文搜索日志
  - 查询参数: `keyword`, `page`, `per_page`

## 数据模型

### 设备集合 (devices)

```javascript
{
  device_id: String,        // 设备唯一标识
  name: String,            // 设备名称
  type: String,            // 设备类型
  location: {              // 地理位置（GeoJSON格式）
    type: "Point",
    coordinates: [longitude, latitude]
  },
  status: String,          // 设备状态（online/offline/maintenance）
  config: Object,          // 设备配置（内嵌文档）
  created_at: Date,
  updated_at: Date
}
```

### 日志集合 (device_logs)

```javascript
{
  device_id: String,       // 设备ID
  log_type: String,        // 日志类型（info/warning/error/status_change）
  timestamp: Date,         // 时间戳（TTL索引）
  content: {               // 日志内容（内嵌文档）
    message: String,
    details: Object
  }
}
```

## 索引设计

### devices集合索引

- `location: 2dsphere` - 地理位置索引
- `type: 1` - 设备类型索引
- `status: 1` - 设备状态索引
- `device_id: 1` - 设备ID唯一索引

### device_logs集合索引

- `timestamp: 1` - TTL索引（90天自动过期）
- `device_id: 1, timestamp: -1` - 复合索引
- `log_type: 1` - 日志类型索引
- `content.message: text, content.details: text` - 全文搜索索引

## 示例数据

系统包含以下示例数据：

- **设备数量**: 80个设备
- **设备类型**: 7种（智能灯、温湿度传感器、摄像头、智能门锁、烟雾报警器、智能插座、运动传感器）
- **日志记录**: 约12,000条日志
- **时间跨度**: 最近30天的数据
- **地理位置**: 广州市范围内随机分布

## 使用场景说明

### 为什么选择MongoDB？

1. **灵活的文档结构**: 不同设备类型有不同的配置项，MongoDB的内嵌文档可以灵活存储这些差异化的配置信息，无需为每种设备类型创建单独的表。

2. **地理位置查询**: MongoDB的2dsphere索引原生支持地理位置查询，非常适合物联网场景中查找附近设备的需求。

3. **时间序列数据**: 日志数据具有明显的时间序列特征，MongoDB的TTL索引可以自动清理过期数据，减少存储压力。

4. **高性能聚合**: MongoDB的聚合管道功能强大，可以高效地进行复杂的数据分析和统计。

5. **水平扩展**: MongoDB支持分片，可以轻松应对大规模物联网设备的数据存储需求。

## 开发团队分工（5人2周）

- **人员1**: Docker环境搭建 + MongoDB配置 + 数据准备
- **人员2**: 后端API开发（设备管理部分）
- **人员3**: 后端API开发（日志管理 + 聚合查询）
- **人员4**: 前端页面开发（设备管理页面）
- **人员5**: 前端页面开发（日志查询页面）+ 测试

## 注意事项

1. **数据库认证**: 默认用户名/密码为 admin/admin123，生产环境请修改
2. **数据持久化**: MongoDB数据存储在Docker卷中，删除容器不会丢失数据
3. **端口占用**: 确保27017和5001端口未被占用（如果5001被占用，可修改docker-compose.yml中的端口映射）
4. **备份**: 定期使用备份脚本备份数据库

## 常见问题

### Q: MongoDB连接失败？

A: 检查MongoDB容器是否正常运行：`docker ps`，查看日志：`docker logs smart_home_mongodb`

### Q: 前端页面无法访问？

A: 检查后端服务是否正常运行：访问 http://localhost:5000/api/health

### Q: 地理位置查询不工作？

A: 确保设备数据中的location字段格式正确，且已创建2dsphere索引

### Q: TTL索引不生效？

A: TTL索引需要MongoDB后台任务运行，通常每分钟检查一次，可能需要等待几分钟

## 许可证

本项目仅用于课程学习目的。

## 作者

数据库系统课程项目小组

