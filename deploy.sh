#!/bin/bash
# 服务器部署脚本

set -e

PROJECT_DIR="/opt/org-management"
SERVICE_NAME="org-management"
PORT=8000

echo "===== 开始部署 $SERVICE_NAME ====="

# 进入项目目录
cd $PROJECT_DIR

# 拉取最新代码
echo ">>> 拉取代码..."
git pull origin main

# 安装依赖
echo ">>> 安装依赖..."
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 停止旧服务
echo ">>> 停止旧服务..."
pkill -f "uvicorn main:app" || true
sleep 2

# 启动新服务
echo ">>> 启动服务..."
nohup uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2 > app.log 2>&1 &

# 等待服务启动
sleep 3

# 检查服务状态
if curl -sf http://127.0.0.1:$PORT/health > /dev/null; then
    echo "===== 部署成功 ====="
    echo "服务地址: http://127.0.0.1:$PORT"
else
    echo "===== 部署失败，服务未正常启动 ====="
    echo "查看日志: tail -f $PROJECT_DIR/app.log"
    exit 1
fi
