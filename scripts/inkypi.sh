#!/bin/bash
# InkyPi utility commands

SERVER="root@guanzhicheng.com"
PROJECT_DIR="/root/guanzhicheng/InkyPi"

function show_usage() {
    echo "InkyPi Utility Commands"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  logs        - View real-time logs (tail -f)"
    echo "  logs-last   - View last 100 lines of logs"
    echo "  status      - Check if InkyPi is running"
    echo "  clear-logs  - Clear the log file"
    echo "  restart     - Restart InkyPi service"
    echo "  shell       - Open SSH shell on server"
    echo ""
}

case "$1" in
    logs)
        echo "📋 Viewing InkyPi logs (Ctrl+C to exit)..."
        ssh ${SERVER} "tail -f ${PROJECT_DIR}/inkypi.log"
        ;;
    logs-last)
        echo "📋 Last 100 lines of InkyPi logs..."
        ssh ${SERVER} "tail -100 ${PROJECT_DIR}/inkypi.log"
        ;;
    status)
        echo "🔍 Checking InkyPi status..."
        ssh ${SERVER} "ps aux | grep '[p]ython3 src/inkypi.py' && echo -e '\n✅ InkyPi is running' || echo -e '\n❌ InkyPi is not running'"
        ;;
    clear-logs)
        echo "🗑️  Clearing log file..."
        ssh ${SERVER} "> ${PROJECT_DIR}/inkypi.log && echo 'Logs cleared'"
        ;;
    restart)
        echo "🔄 Restarting InkyPi..."
        ssh ${SERVER} "cd ${PROJECT_DIR} && bash restart.sh"
        ;;
    shell)
        echo "🖥️  Opening SSH shell..."
        ssh ${SERVER} "cd ${PROJECT_DIR} && exec bash"
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
