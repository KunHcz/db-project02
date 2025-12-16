#!/bin/bash

# 智能家居设备日志管理系统启动脚本

echo "=========================================="
echo "智能家居设备日志管理系统"
echo "=========================================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: 未找到Docker，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: 未找到Docker Compose，请先安装Docker Compose"
    exit 1
fi

echo "1. 启动Docker服务..."
docker-compose up -d

echo ""
echo "2. 等待服务启动..."
sleep 5

echo ""
echo "3. 检查服务状态..."
docker-compose ps

echo ""
echo "=========================================="
echo "服务启动完成！"
echo "=========================================="
echo "前端访问地址: http://localhost:5001"
echo "API健康检查: http://localhost:5001/api/health"
echo ""
echo "导入示例数据:"
echo "  docker exec smart_home_backend python /app/scripts/import_data.py --clear"
echo ""
echo "查看日志:"
echo "  docker-compose logs -f"
echo ""
echo "停止服务:"
echo "  docker-compose down"
echo "=========================================="

