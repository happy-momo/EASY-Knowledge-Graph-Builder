#!/bin/bash

# KG AI Builder 一键启动脚本

echo "================================"
echo "  KG AI Builder - 启动脚本"
echo "================================"
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    echo "   安装指南: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装"
    echo "   安装指南: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker环境检测完成"
echo ""

# 启动服务
echo "🚀 正在启动服务..."
docker-compose up -d

# 等待服务启动
echo ""
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "📊 服务状态:"
docker-compose ps

echo ""
echo "================================"
echo "  ✅ 启动完成!"
echo "================================"
echo ""
echo "访问地址:"
echo "  📱 KG Builder:    http://localhost:8501"
echo "  🗄️ Neo4j Browser: http://localhost:7474"
echo ""
echo "默认配置:"
echo "  Neo4j 用户名: neo4j"
echo "  Neo4j 密码:   password123"
echo ""
echo "其他命令:"
echo "  停止服务: docker-compose down"
echo "  查看日志: docker-compose logs -f"
echo "  重启服务: docker-compose restart"
echo ""