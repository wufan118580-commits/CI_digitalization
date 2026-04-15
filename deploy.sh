#!/bin/bash
# 本地部署脚本（无需拉取代码）

set -e

PORT=8080

echo "===== 本地部署 org-management ====="

# 检查依赖
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

# 构建镜像
echo ">>> 构建 Docker 镜像..."
docker build -t org-management:local .

# 停止旧容器
echo ">>> 停止旧容器..."
docker stop org-management-local 2>/dev/null || true
docker rm org-management-local 2>/dev/null || true

# 启动容器
echo ">>> 启动服务..."
docker run -d \
    --name org-management-local \
    --restart always \
    -p ${PORT}:8080 \
    -e DB_HOST=$DB_HOST \
    -e DB_PORT=$DB_PORT \
    -e DB_USER=$DB_USER \
    -e DB_PASSWORD=$DB_PASSWORD \
    -e DB_NAME=$DB_NAME \
    -e JWT_SECRET_KEY=$JWT_SECRET_KEY \
    -e WECHAT_APPID=$WECHAT_APPID \
    -e WECHAT_SECRET=$WECHAT_SECRET \
    org-management:local

# 验证
sleep 3
if docker ps | grep -q org-management-local; then
    echo "===== 部署成功 ====="
    echo "访问地址: http://localhost:${PORT}"
    echo "健康检查: http://localhost:${PORT}/health"
else
    echo "===== 部署失败 ====="
    docker logs org-management-local
    exit 1
fi
