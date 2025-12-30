#!/bin/bash
# 列出所有数据库备份

# 备份目录（相对于脚本所在目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/backup"

echo "=========================================="
echo "数据库备份列表"
echo "=========================================="

if [ ! -d "${BACKUP_DIR}" ]; then
    echo "备份目录不存在: ${BACKUP_DIR}"
    exit 0
fi

# 检查是否有备份文件
BACKUP_COUNT=0

# 列出目录备份
for backup in "${BACKUP_DIR}"/smart_home_backup_*; do
    if [ -d "$backup" ]; then
        BACKUP_COUNT=$((BACKUP_COUNT + 1))
        BACKUP_NAME=$(basename "$backup")
        BACKUP_SIZE=$(du -sh "$backup" | cut -f1)
        BACKUP_TIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$backup" 2>/dev/null || stat -c "%y" "$backup" | cut -d'.' -f1)
        
        echo ""
        echo "备份名称: ${BACKUP_NAME}"
        echo "  类型: 目录备份"
        echo "  大小: ${BACKUP_SIZE}"
        echo "  时间: ${BACKUP_TIME}"
    fi
done

# 列出压缩备份
for backup in "${BACKUP_DIR}"/smart_home_backup_*.tar.gz; do
    if [ -f "$backup" ]; then
        BACKUP_COUNT=$((BACKUP_COUNT + 1))
        BACKUP_NAME=$(basename "$backup")
        BACKUP_SIZE=$(du -sh "$backup" | cut -f1)
        BACKUP_TIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$backup" 2>/dev/null || stat -c "%y" "$backup" | cut -d'.' -f1)
        
        echo ""
        echo "备份名称: ${BACKUP_NAME}"
        echo "  类型: 压缩备份"
        echo "  大小: ${BACKUP_SIZE}"
        echo "  时间: ${BACKUP_TIME}"
    fi
done

if [ $BACKUP_COUNT -eq 0 ]; then
    echo ""
    echo "没有找到备份文件"
    echo ""
    echo "创建备份:"
    echo "  ./backup_database.sh"
fi

echo ""
echo "=========================================="
echo "总计: ${BACKUP_COUNT} 个备份"
echo "=========================================="


