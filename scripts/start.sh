#!/bin/bash
set -e

# KG AI Builder 一键启动脚本

echo "================================"
echo "  KG AI Builder - 启动脚本"
echo "================================"
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    echo "   安装指南: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 Docker Compose（优先 v2 `docker compose`，回退 v1 `docker-compose`）
COMPOSE_CMD=""
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose 未安装，请先安装"
    echo "   安装指南: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker 环境检测完成（使用 ${COMPOSE_CMD}）"
echo ""

# 启动服务
echo "🚀 正在启动服务..."
${COMPOSE_CMD} up -d

# 等待 Neo4j 健康检查通过（docker compose 自身会等待 depends_on condition: service_healthy）
echo ""
echo "⏳ 等待服务就绪..."

# 检查服务状态
echo ""
echo "📊 服务状态:"
${COMPOSE_CMD} ps

echo ""
echo "================================"
echo "  ✅ 启动完成!"
echo "================================"
echo ""
echo "访问地址:"
echo "  📱 KG Builder:    http://localhost:8501"
echo "  🗄️ Neo4j Browser: http://localhost:7474"
echo ""
echo "默认配置（首次启动后请尽快修改）:"
echo "  Neo4j 用户名: neo4j"
echo "  Neo4j 密码:   password123"
echo ""
echo "其他命令:"
echo "  停止服务: ${COMPOSE_CMD} down"
echo "  查看日志: ${COMPOSE_CMD} logs -f"
echo "  重启服务: ${COMPOSE_CMD} restart"
