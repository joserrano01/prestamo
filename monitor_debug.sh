#!/bin/bash

echo "🔍 Starting real-time monitoring for refresh issue debug"
echo "=================================================="
echo "Timestamp: $(date)"
echo "Monitoring nginx and frontend logs..."
echo "Press Ctrl+C to stop"
echo ""

# Create a temporary file for correlation
TEMP_LOG="/tmp/prestamo_debug_$(date +%s).log"
echo "Debug log file: $TEMP_LOG"

# Function to log with precise timestamp
log_with_timestamp() {
    local source=$1
    local message=$2
    local timestamp=$(date '+%H:%M:%S.%3N')
    echo "[$timestamp] [$source] $message" | tee -a "$TEMP_LOG"
}

# Monitor nginx logs
monitor_nginx() {
    docker compose -f docker-compose.dev.yml logs -f nginx 2>/dev/null | while read line; do
        if [[ $line == *"GET"* ]] || [[ $line == *"POST"* ]]; then
            log_with_timestamp "NGINX" "$line"
        fi
    done
}

# Monitor frontend logs  
monitor_frontend() {
    docker compose -f docker-compose.dev.yml logs -f frontend 2>/dev/null | while read line; do
        if [[ $line == *"hmr"* ]] || [[ $line == *"reload"* ]] || [[ $line == *"update"* ]] || [[ $line == *"ready"* ]]; then
            log_with_timestamp "FRONTEND" "$line"
        fi
    done
}

# Monitor backend logs for API calls
monitor_backend() {
    docker compose -f docker-compose.dev.yml logs -f backend 2>/dev/null | while read line; do
        if [[ $line == *"INFO:"* ]] && [[ $line == *"sucursales"* ]]; then
            log_with_timestamp "BACKEND" "$line"
        fi
    done
}

# Function to analyze patterns
analyze_patterns() {
    echo ""
    echo "🔍 Analysis of last 2 minutes:"
    echo "================================"
    
    # Count requests per minute
    echo "Request frequency:"
    grep "NGINX" "$TEMP_LOG" | grep "GET /" | tail -20 | while read line; do
        timestamp=$(echo $line | cut -d']' -f1 | tr -d '[')
        echo "  - $timestamp"
    done
    
    echo ""
    echo "Suspicious tokens:"
    grep "token=" "$TEMP_LOG" | tail -5
    
    echo ""
    echo "HMR activity:"
    grep "hmr\|reload" "$TEMP_LOG" | tail -5
}

# Start monitoring in background
echo "Starting monitors..."
monitor_nginx &
NGINX_PID=$!

monitor_frontend &
FRONTEND_PID=$!

monitor_backend &
BACKEND_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping monitors..."
    kill $NGINX_PID $FRONTEND_PID $BACKEND_PID 2>/dev/null
    
    analyze_patterns
    
    echo ""
    echo "📊 Full debug log saved to: $TEMP_LOG"
    echo "You can review it with: cat $TEMP_LOG"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Show live stats every 10 seconds
while true; do
    sleep 10
    echo ""
    echo "📊 Live Stats ($(date '+%H:%M:%S')):"
    echo "  Recent requests (last 30 seconds):"
    grep "NGINX" "$TEMP_LOG" | tail -5 | while read line; do
        echo "    $(echo $line | cut -d']' -f3-)"
    done
done