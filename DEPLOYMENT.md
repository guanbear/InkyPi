# InkyPi 部署脚本使用指南

## 📁 脚本说明

本项目包含以下自动化脚本，位于 `scripts/` 目录：

### 1. `deploy.sh` - 一键部署脚本 🚀

**功能**：从本地推送代码到服务器并自动重启服务

**使用方法**：
```bash
./scripts/deploy.sh
```

**执行步骤**：
1. 检查本地是否有未提交的更改
2. 推送代码到 GitHub
3. SSH 到服务器执行重启脚本
4. 显示部署结果

### 2. `inkypi.sh` - 实用工具脚本 🛠️

**功能**：提供各种便捷的管理命令

**使用方法**：
```bash
./scripts/inkypi.sh <command>
```

**可用命令**：
- `logs` - 实时查看日志（tail -f）
- `logs-last` - 查看最后100行日志
- `status` - 检查服务是否运行
- `clear-logs` - 清空日志文件
- `restart` - 重启服务（仅在服务器上执行重启）
- `shell` - 打开服务器 SSH 终端

**示例**：
```bash
# 查看实时日志
./scripts/inkypi.sh logs

# 检查服务状态
./scripts/inkypi.sh status

# 清空日志文件（日志太大时使用）
./scripts/inkypi.sh clear-logs
```

### 3. 服务器端 `restart.sh`

**位置**：`/root/guanzhicheng/InkyPi/restart.sh`

**功能**：服务器上的重启脚本，由 deploy.sh 自动调用

**手动执行**（在服务器上）：
```bash
cd /root/guanzhicheng/InkyPi
bash restart.sh
```

**执行步骤**：
1. 停止现有的 InkyPi 进程
2. 从 git 拉取最新代码
3. 激活虚拟环境
4. 检查并更新依赖（如果需要）
5. 启动服务并保存 PID

## 🔐 SSH 密钥配置

已配置 SSH 密钥认证，无需输入密码即可登录服务器。

**测试连接**：
```bash
ssh root@guanzhicheng.com "echo 'Connection successful!'"
```

## 📊 服务管理

### 启动命令
```bash
nohup python3 src/inkypi.py --dev --host 127.0.0.1 >> inkypi.log 2>&1 &
```

### 日志文件
- **位置**：`/root/guanzhicheng/InkyPi/inkypi.log`
- **模式**：追加模式（不会覆盖旧日志）
- **清理**：定期使用 `./scripts/inkypi.sh clear-logs` 清空

### PID 文件
- **位置**：`/root/guanzhicheng/InkyPi/inkypi.pid`
- **用途**：存储当前运行进程的 PID

## 🎯 常用工作流

### 部署新版本
```bash
# 1. 本地开发完成后提交代码
git add .
git commit -m "Your commit message"

# 2. 一键部署到服务器
./scripts/deploy.sh
```

### 查看日志
```bash
# 实时查看
./scripts/inkypi.sh logs

# 查看最近的日志
./scripts/inkypi.sh logs-last
```

### 日志太大时清理
```bash
# 清空日志文件
./scripts/inkypi.sh clear-logs

# 或者在服务器上手动清空
ssh root@guanzhicheng.com "> /root/guanzhicheng/InkyPi/inkypi.log"
```

### 仅重启服务（不更新代码）
```bash
./scripts/inkypi.sh restart
```

## 🐛 故障排查

### 服务启动失败
```bash
# 1. 查看日志
./scripts/inkypi.sh logs-last

# 2. 检查进程
./scripts/inkypi.sh status

# 3. 手动重启
./scripts/inkypi.sh restart
```

### 日志文件过大
```bash
# 查看日志文件大小
ssh root@guanzhicheng.com "ls -lh /root/guanzhicheng/InkyPi/inkypi.log"

# 清空日志
./scripts/inkypi.sh clear-logs
```

### SSH 连接问题
```bash
# 测试连接
ssh root@guanzhicheng.com "date"

# 如果失败，检查 SSH 密钥
ls -la ~/.ssh/id_rsa*
```

## 📝 服务器信息

- **服务器**：root@guanzhicheng.com
- **项目目录**：/root/guanzhicheng/InkyPi
- **虚拟环境**：/root/guanzhicheng/InkyPi/myenv
- **日志文件**：/root/guanzhicheng/InkyPi/inkypi.log
- **PID 文件**：/root/guanzhicheng/InkyPi/inkypi.pid

## 🎉 优势

相比手动操作，自动化脚本的优势：

- ✅ **一键部署**：`./scripts/deploy.sh` 替代 5 步手动操作
- ✅ **智能重启**：自动检测并杀掉旧进程，确保干净重启
- ✅ **日志管理**：统一的日志文件，支持追加和清理
- ✅ **依赖检测**：自动检测 requirements.txt 变化并更新
- ✅ **状态检查**：启动后自动验证进程是否成功运行
- ✅ **无密码登录**：SSH 密钥认证，安全便捷
