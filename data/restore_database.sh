#!/bin/bash
# MongoDB数据库恢复脚本
# 使用mongorestore进行数据库恢复

# MongoDB连接配置
MONGO_HOST="${MONGO_HOST:-localhost}"
MONGO_PORT="${MONGO_PORT:-27017}"
MONGO_USERNAME="${MONGO_USERNAME:-admin}"
MONGO_PASSWORD="${MONGO_PASSWORD:-admin123}"
MONGO_DATABASE="${MONGO_DATABASE:-smart_home}"

# 备份目录（相对于脚本所在目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/backup"

# 检查参数
if [ -z "$1" ]; then
    echo "用法: $0 <备份名称>"
    echo ""
    echo "示例:"
    echo "  $0 smart_home_backup_20240101_120000"
    echo "  $0 smart_home_backup_20240101_120000.tar.gz"
    echo ""
    echo "可用备份列表:"
    echo "=========================================="
    if [ -d "${BACKUP_DIR}" ]; then
        # 列出目录备份
        for backup in "${BACKUP_DIR}"/smart_home_backup_*; do
            if [ -d "$backup" ]; then
                echo "  $(basename "$backup")"
            fi
        done
        # 列出压缩备份
        for backup in "${BACKUP_DIR}"/smart_home_backup_*.tar.gz; do
            if [ -f "$backup" ]; then
                echo "  $(basename "$backup")"
            fi
        done
    else
        echo "  没有找到备份文件"
    fi
    echo "=========================================="
    exit 1
fi

BACKUP_NAME="$1"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
RESTORE_PATH=""

# 检查备份文件是否存在
if [ ! -e "${BACKUP_PATH}" ]; then
    echo "❌ 备份文件不存在: ${BACKUP_PATH}"
    exit 1
fi

# 如果是压缩文件，先解压
if [[ "${BACKUP_NAME}" == *.tar.gz ]]; then
    echo "检测到压缩备份文件，正在解压..."
    TEMP_DIR="${BACKUP_DIR}/temp_restore_$$"
    mkdir -p "${TEMP_DIR}"
    
    if tar -xzf "${BACKUP_PATH}" -C "${TEMP_DIR}"; then
        # 查找解压后的备份目录
        RESTORE_PATH=$(find "${TEMP_DIR}" -type d -name "smart_home_backup_*" | head -n 1)
        if [ -z "${RESTORE_PATH}" ]; then
            echo "❌ 无法找到解压后的备份目录"
            rm -rf "${TEMP_DIR}"
            exit 1
        fi
        echo "✅ 解压完成"
    else
        echo "❌ 解压失败"
        rm -rf "${TEMP_DIR}"
        exit 1
    fi
elif [ -d "${BACKUP_PATH}" ]; then
    RESTORE_PATH="${BACKUP_PATH}"
else
    echo "❌ 无效的备份文件格式"
    exit 1
fi

# 检查mongorestore是否可用
if ! command -v mongorestore &> /dev/null; then
    echo "错误: 未找到mongorestore命令"
    echo "请确保MongoDB工具已安装并在PATH中"
    echo "或者使用Docker容器中的mongorestore:"
    echo "  docker exec smart_home_mongodb mongorestore ..."
    if [ -n "${TEMP_DIR}" ]; then
        rm -rf "${TEMP_DIR}"
    fi
    exit 1
fi

echo "=========================================="
echo "恢复数据库备份"
echo "=========================================="
echo "备份文件: ${BACKUP_NAME}"
echo "备份路径: ${RESTORE_PATH}"
echo "目标数据库: ${MONGO_DATABASE}"
echo "=========================================="

# 确认操作
echo "⚠️  警告: 此操作将覆盖现有数据库！"
read -p "确认恢复？(yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "操作已取消"
    if [ -n "${TEMP_DIR}" ]; then
        rm -rf "${TEMP_DIR}"
    fi
    exit 0
fi

# 构建mongorestore命令
MONGORESTORE_CMD="mongorestore --host ${MONGO_HOST}:${MONGO_PORT} --db ${MONGO_DATABASE} --drop"

# 如果使用认证，添加用户名和密码
if [ -n "${MONGO_USERNAME}" ] && [ -n "${MONGO_PASSWORD}" ]; then
    MONGORESTORE_CMD="${MONGORESTORE_CMD} --username ${MONGO_USERNAME} --password ${MONGO_PASSWORD} --authenticationDatabase admin"
fi

# 添加备份路径
MONGORESTORE_CMD="${MONGORESTORE_CMD} ${RESTORE_PATH}/${MONGO_DATABASE}"

# 执行恢复
echo "开始恢复..."
if eval "${MONGORESTORE_CMD}"; then
    echo "✅ 恢复成功！"
    
    # 清理临时文件
    if [ -n "${TEMP_DIR}" ]; then
        rm -rf "${TEMP_DIR}"
        echo "已清理临时文件"
    fi
    
    exit 0
else
    echo "❌ 恢复失败"
    
    # 清理临时文件
    if [ -n "${TEMP_DIR}" ]; then
        rm -rf "${TEMP_DIR}"
    fi
    
    exit 1
fi

