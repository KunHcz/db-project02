# 数据库脚本说明

本目录包含数据库创建脚本和备份恢复脚本。

## 文件说明

### 1. `init_db.js` - 数据库初始化脚本

MongoDB数据库初始化脚本，用于：
- 创建 `smart_home` 数据库
- 创建数据库用户
- 创建集合（devices、device_logs）
- 创建所有必要的索引：
  - 地理位置索引（2dsphere）
  - TTL索引（90天自动过期）
  - 复合索引
  - 全文搜索索引
  - 唯一索引

**使用方式：**

该脚本会在MongoDB容器首次启动时自动执行（通过docker-compose.yml配置）。

也可以手动执行：
```bash
docker exec -i smart_home_mongodb mongo admin -u admin -p admin123 < init_db.js
```

### 2. `backup_database.sh` - 数据库备份脚本

使用 `mongodump` 创建数据库备份。

**功能：**
- 创建带时间戳的备份
- 支持压缩备份（可选）
- 自动清理7天前的旧备份
- 显示备份大小和位置

**使用方式：**
```bash
cd data
./backup_database.sh
```

**环境变量（可选）：**
```bash
export MONGO_HOST=localhost
export MONGO_PORT=27017
export MONGO_USERNAME=admin
export MONGO_PASSWORD=admin123
export MONGO_DATABASE=smart_home
```

### 3. `restore_database.sh` - 数据库恢复脚本

使用 `mongorestore` 恢复数据库备份。

**功能：**
- 支持目录备份和压缩备份
- 自动解压压缩备份
- 安全确认机制（防止误操作）
- 列出可用备份

**使用方式：**
```bash
cd data
# 列出所有备份
./list_backups.sh

# 恢复备份（目录备份）
./restore_database.sh smart_home_backup_20240101_120000

# 恢复备份（压缩备份）
./restore_database.sh smart_home_backup_20240101_120000.tar.gz
```

**⚠️ 警告：** 恢复操作会覆盖现有数据库，请谨慎操作！

### 4. `list_backups.sh` - 列出所有备份

列出 `backup` 目录中的所有备份文件。

**使用方式：**
```bash
cd data
./list_backups.sh
```

## 备份目录

备份文件存储在 `backup/` 目录中：
- 目录备份：`smart_home_backup_YYYYMMDD_HHMMSS/`
- 压缩备份：`smart_home_backup_YYYYMMDD_HHMMSS.tar.gz`

## 使用Docker容器执行备份

如果本地没有安装MongoDB工具，可以使用Docker容器执行：

### 备份
```bash
docker exec smart_home_mongodb mongodump \
  --host localhost:27017 \
  --db smart_home \
  --username admin \
  --password admin123 \
  --authenticationDatabase admin \
  --out /data/backup/smart_home_backup_$(date +%Y%m%d_%H%M%S)
```

### 恢复
```bash
docker exec -i smart_home_mongodb mongorestore \
  --host localhost:27017 \
  --db smart_home \
  --username admin \
  --password admin123 \
  --authenticationDatabase admin \
  --drop \
  /data/backup/smart_home_backup_YYYYMMDD_HHMMSS/smart_home
```

## 注意事项

1. **权限问题**：确保脚本有执行权限（`chmod +x *.sh`）
2. **MongoDB工具**：本地执行需要安装MongoDB Database Tools
3. **数据安全**：定期备份数据库，建议每天备份一次
4. **备份清理**：备份脚本会自动清理7天前的旧备份
5. **恢复操作**：恢复操作会删除现有数据，请先备份！

## 相关文件

- Python备份脚本：`../code/scripts/backup_db.py`
- 数据导入脚本：`../code/scripts/import_data.py`

