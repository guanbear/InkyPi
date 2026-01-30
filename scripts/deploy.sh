#!/bin/bash
# Local deployment script for InkyPi

set -e

SERVER="root@guanzhicheng.com"
PROJECT_DIR="/root/guanzhicheng/InkyPi"

echo "========================================="
echo "InkyPi Deployment Script"
echo "Time: $(date)"
echo "========================================="

# 1. 检查是否有未提交的更改
echo -e "\nStep 1: Checking local git status..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes:"
    git status --short
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 1
    fi
fi

# 2. 推送代码到远程
echo -e "\nStep 2: Pushing code to remote repository..."
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: ${CURRENT_BRANCH}"
git push origin ${CURRENT_BRANCH}
echo "✅ Code pushed successfully"

# 3. SSH到服务器执行重启脚本
echo -e "\nStep 3: Deploying to server..."
echo "Connecting to ${SERVER}..."
ssh ${SERVER} "cd ${PROJECT_DIR} && bash restart.sh" || true
echo "Note: Ignore 'Failed to start' message if process is actually running"

echo -e "\n========================================="
echo "✅ Deployment completed!"
echo "========================================="
echo ""
echo "Useful commands:"
echo "  View logs:  ssh ${SERVER} 'tail -f ${PROJECT_DIR}/inkypi.log'"
echo "  Check status: ssh ${SERVER} 'ps aux | grep inkypi.py'"
echo "  Clear logs: ssh ${SERVER} '> ${PROJECT_DIR}/inkypi.log'"
