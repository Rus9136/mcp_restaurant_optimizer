#!/bin/bash

# Production Deployment Script for MCP Restaurant Optimizer SSE
# This script deploys the SSE endpoint to production server https://mcp.madlen.space

set -e  # Exit on any error

echo "🚀 Starting MCP Restaurant Optimizer SSE Production Deployment"
echo "=============================================================="

# Configuration
PROJECT_DIR="/root/projects/mcp_restaurant_optimizer"
NGINX_CONFIG_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
SERVICE_NAME="mcp-restaurant"
BACKUP_DIR="/tmp/mcp_backup_$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Pre-deployment checks
log_info "Performing pre-deployment checks..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

# Check required commands
for cmd in nginx systemctl git python3 pip; do
    if ! command_exists $cmd; then
        log_error "Required command '$cmd' not found"
        exit 1
    fi
done

# Check if project directory exists
if [[ ! -d "$PROJECT_DIR" ]]; then
    log_error "Project directory $PROJECT_DIR not found"
    exit 1
fi

# Create backup directory
log_info "Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Step 1: Backup current configuration
log_info "Step 1: Backing up current configuration..."

# Backup nginx config if exists
if [[ -f "$NGINX_CONFIG_DIR/mcp.madlen.space" ]]; then
    cp "$NGINX_CONFIG_DIR/mcp.madlen.space" "$BACKUP_DIR/nginx_mcp_backup.conf"
    log_success "Nginx config backed up"
fi

# Backup service file if exists
if systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
    systemctl show "$SERVICE_NAME" > "$BACKUP_DIR/service_backup.txt"
    log_success "Service configuration backed up"
fi

# Step 2: Update application code
log_info "Step 2: Updating application code..."

cd "$PROJECT_DIR"
git stash push -m "Pre-deployment backup $(date)"
git pull origin main
log_success "Code updated from repository"

# Step 3: Install/update dependencies
log_info "Step 3: Installing dependencies..."

# Install asyncpg for PostgreSQL support
pip install asyncpg sqlalchemy[asyncio] psycopg2-binary
log_success "Database dependencies installed"

# Install requirements
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
    log_success "Python dependencies installed"
fi

# Step 4: Configure environment
log_info "Step 4: Configuring environment..."

# Check if .env exists, if not copy from template
if [[ ! -f ".env" ]]; then
    if [[ -f ".env.production" ]]; then
        cp ".env.production" ".env"
        log_warning "Environment file created from template. Please update with your values!"
        log_warning "Edit: $PROJECT_DIR/.env"
    else
        log_error "No environment configuration found. Please create .env file"
        exit 1
    fi
else
    log_success "Environment file already exists"
fi

# Step 5: Configure nginx
log_info "Step 5: Configuring nginx for SSE..."

# Copy nginx configuration
if [[ -f "nginx_production_sse.conf" ]]; then
    cp "nginx_production_sse.conf" "$NGINX_CONFIG_DIR/mcp.madlen.space"
    
    # Enable site
    if [[ ! -L "$NGINX_ENABLED_DIR/mcp.madlen.space" ]]; then
        ln -sf "$NGINX_CONFIG_DIR/mcp.madlen.space" "$NGINX_ENABLED_DIR/mcp.madlen.space"
    fi
    
    # Test nginx configuration
    nginx -t
    if [[ $? -eq 0 ]]; then
        log_success "Nginx configuration valid"
    else
        log_error "Nginx configuration test failed"
        exit 1
    fi
else
    log_warning "Nginx configuration file not found, using existing"
fi

# Step 6: Create/update systemd service
log_info "Step 6: Configuring systemd service..."

# Create service file if it doesn't exist
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
if [[ ! -f "$SERVICE_FILE" ]]; then
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=MCP Restaurant Optimizer with SSE
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    log_success "Systemd service created"
fi

# Step 7: Database setup check
log_info "Step 7: Checking database connectivity..."

# Test database connection
python3 -c "
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine

async def test_db():
    try:
        # Read DATABASE_URL from .env file
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('DATABASE_URL='):
                    db_url = line.split('=', 1)[1].strip()
                    break
        else:
            print('DATABASE_URL not found in .env')
            return False
        
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            await conn.execute('SELECT 1')
        await engine.dispose()
        print('Database connection successful')
        return True
    except Exception as e:
        print(f'Database connection failed: {e}')
        return False

if not asyncio.run(test_db()):
    exit(1)
" 2>/dev/null

if [[ $? -eq 0 ]]; then
    log_success "Database connection verified"
else
    log_warning "Database connection failed. Please check DATABASE_URL in .env"
fi

# Step 8: Restart services
log_info "Step 8: Restarting services..."

# Stop service gracefully
if systemctl is-active --quiet "$SERVICE_NAME"; then
    systemctl stop "$SERVICE_NAME"
    sleep 2
fi

# Start service
systemctl start "$SERVICE_NAME"
sleep 3

# Check service status
if systemctl is-active --quiet "$SERVICE_NAME"; then
    log_success "MCP service started successfully"
else
    log_error "Failed to start MCP service"
    systemctl status "$SERVICE_NAME"
    exit 1
fi

# Reload nginx
nginx -s reload
if [[ $? -eq 0 ]]; then
    log_success "Nginx reloaded successfully"
else
    log_error "Failed to reload nginx"
    exit 1
fi

# Step 9: Health checks
log_info "Step 9: Performing health checks..."

# Wait a bit for service to fully start
sleep 5

# Check main API
log_info "Testing main API endpoint..."
if curl -f -s "http://localhost:8000/health" > /dev/null; then
    log_success "Main API is responding"
else
    log_error "Main API health check failed"
fi

# Check SSE status endpoint
log_info "Testing SSE status endpoint..."
if curl -f -s "http://localhost:8000/api/v1/mcp/sse/status" > /dev/null; then
    log_success "SSE status endpoint is responding"
else
    log_error "SSE status endpoint failed"
fi

# Test external access (if possible)
log_info "Testing external HTTPS access..."
if curl -f -s -k "https://mcp.madlen.space/api/v1/mcp/sse/status" > /dev/null; then
    log_success "External HTTPS access working"
else
    log_warning "External HTTPS access test failed (check SSL/DNS)"
fi

# Step 10: Display deployment summary
echo ""
echo "🎉 Deployment completed!"
echo "======================"
log_success "MCP Restaurant Optimizer SSE is now deployed"
echo ""
echo "📊 Service Status:"
systemctl status "$SERVICE_NAME" --no-pager -l

echo ""
echo "🌐 Endpoints:"
echo "  • Main API:    https://mcp.madlen.space/"
echo "  • SSE Stream:  https://mcp.madlen.space/api/v1/mcp/sse"
echo "  • SSE Status:  https://mcp.madlen.space/api/v1/mcp/sse/status"
echo ""

echo "🔍 Testing Commands:"
echo "  • curl https://mcp.madlen.space/api/v1/mcp/sse/status"
echo "  • curl -H 'Accept: text/event-stream' https://mcp.madlen.space/api/v1/mcp/sse"
echo ""

echo "📋 Management Commands:"
echo "  • Service logs:    journalctl -u $SERVICE_NAME -f"
echo "  • Service status:  systemctl status $SERVICE_NAME"
echo "  • Nginx logs:      tail -f /var/log/nginx/mcp_*.log"
echo "  • SSE logs:        tail -f /var/log/nginx/sse_access.log"
echo ""

echo "⚠️  Important Notes:"
log_warning "1. Update .env with your actual database and API credentials"
log_warning "2. Ensure SSL certificates are valid for mcp.madlen.space"
log_warning "3. Monitor SSE connections and server resources"
log_warning "4. Backup created in: $BACKUP_DIR"

echo ""
log_info "Deployment completed successfully! 🚀"