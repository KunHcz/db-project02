#!/bin/bash
# MongoDB数据库备份脚本
# 使用mongodump进行数据库备份

# MongoDB连接配置
MONGO_HOST="${MONGO_HOST:-localhost}"
MONGO_PORT="${MONGO_PORT:-27017}"
MONGO_USERNAME="${MONGO_USERNAME:-admin}"
MONGO_PASSWORD="${MONGO_PASSWORD:-admin123}"
MONGO_DATABASE="${MONGO_DATABASE:-smart_home}"

# 备份目录（相对于脚本所在目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/backup"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 生成备份文件名（带时间戳）
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="smart_home_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

echo "=========================================="
echo "MongoDB 数据库备份脚本"
echo "=========================================="
echo "数据库: ${MONGO_DATABASE}"
echo "主机: ${MONGO_HOST}:${MONGO_PORT}"
echo "备份路径: ${BACKUP_PATH}"
echo "=========================================="

# 检查是否使用Docker容器
USE_DOCKER=false
if command -v docker &> /dev/null; then
    if docker ps --format '{{.Names}}' | grep -q "^smart_home_mongodb$"; then
        USE_DOCKER=true
        echo "检测到Docker容器，使用容器内的mongodump"
    fi
fi

# 构建mongodump命令
if [ "$USE_DOCKER" = true ]; then
    # 使用Docker容器执行备份
    CONTAINER_BACKUP_PATH="/data/backup/${BACKUP_NAME}"
    MONGODUMP_CMD="docker exec smart_home_mongodb mongodump --host localhost:27017 --db ${MONGO_DATABASE} --username ${MONGO_USERNAME} --password ${MONGO_PASSWORD} --authenticationDatabase admin --out ${CONTAINER_BACKUP_PATH}"
else
    # 检查mongodump是否可用
    if ! command -v mongodump &> /dev/null; then
        echo "错误: 未找到mongodump命令"
        echo "请确保MongoDB工具已安装并在PATH中"
        echo "或者确保Docker容器正在运行: docker ps"
        exit 1
    fi
    
    # 使用本地mongodump
    MONGODUMP_CMD="mongodump --host ${MONGO_HOST}:${MONGO_PORT} --db ${MONGO_DATABASE} --out ${BACKUP_PATH}"
    
    # 如果使用认证，添加用户名和密码
    if [ -n "${MONGO_USERNAME}" ] && [ -n "${MONGO_PASSWORD}" ]; then
        MONGODUMP_CMD="${MONGODUMP_CMD} --username ${MONGO_USERNAME} --password ${MONGO_PASSWORD} --authenticationDatabase admin"
    fi
fi

# 执行备份
echo "开始备份..."
if eval "${MONGODUMP_CMD}"; then
    # 如果使用Docker，需要将备份文件复制到宿主机
    if [ "$USE_DOCKER" = true ]; then
        echo "正在将备份文件从容器复制到宿主机..."
        docker cp "smart_home_mongodb:${CONTAINER_BACKUP_PATH}" "${BACKUP_PATH}"
        if [ $? -eq 0 ]; then
            echo "✅ 备份文件已复制到: ${BACKUP_PATH}"
            # 清理容器内的备份文件
            docker exec smart_home_mongodb rm -rf "${CONTAINER_BACKUP_PATH}"
        else
            echo "⚠️  警告: 无法复制备份文件，备份仍在容器内: ${CONTAINER_BACKUP_PATH}"
        fi
    fi
    echo "✅ 备份成功！"
    echo "备份文件保存在: ${BACKUP_PATH}"
    
    # 计算备份文件大小
    BACKUP_SIZE=$(du -sh "${BACKUP_PATH}" | cut -f1)
    echo "备份总大小: ${BACKUP_SIZE}"
    
    # 压缩备份（可选）
    echo ""
    read -p "是否压缩备份文件？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "正在压缩备份文件..."
        cd "${BACKUP_DIR}"
        tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
        if [ $? -eq 0 ]; then
            echo "✅ 备份已压缩: ${BACKUP_NAME}.tar.gz"
            # 删除未压缩的备份目录
            rm -rf "${BACKUP_NAME}"
            echo "已删除未压缩的备份目录"
        fi
    fi
    
    # 删除7天前的备份
    echo ""
    echo "清理7天前的旧备份..."
    find "${BACKUP_DIR}" -name "smart_home_backup_*" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null
    find "${BACKUP_DIR}" -name "smart_home_backup_*.tar.gz" -mtime +7 -delete 2>/dev/null
    echo "✅ 已清理7天前的旧备份"
    
    exit 0
else
    echo "❌ 备份失败"
    exit 1
fi

