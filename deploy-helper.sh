#!/bin/bash
# Helper script for easy deployment from Netherlands to US Lightsail

# Configuration
LIGHTSAIL_IP="${LIGHTSAIL_IP:-YOUR_IP_HERE}"
DEPLOY_PATH="/home/ubuntu/bank-statement-converter"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Bank Statement Converter - Deployment Script${NC}"
echo -e "${BLUE}Deploying from Netherlands → US Lightsail${NC}\n"

# Check if IP is set
if [ "$LIGHTSAIL_IP" = "YOUR_IP_HERE" ]; then
    echo -e "${RED}❌ Error: Please set LIGHTSAIL_IP environment variable${NC}"
    echo "Export it: export LIGHTSAIL_IP=your.instance.ip"
    exit 1
fi

# Function to check connection
check_connection() {
    echo -e "${BLUE}Checking connection to $LIGHTSAIL_IP...${NC}"
    if ssh -o ConnectTimeout=5 ubuntu@$LIGHTSAIL_IP "echo 'Connected'" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Connection successful${NC}"
        return 0
    else
        echo -e "${RED}❌ Connection failed${NC}"
        return 1
    fi
}

# Function to deploy
deploy() {
    echo -e "\n${BLUE}📦 Creating deployment package...${NC}"
    
    # Create a temporary directory for clean deployment
    TEMP_DIR=$(mktemp -d)
    
    # Copy files to temp directory
    cp -r backend $TEMP_DIR/
    cp -r *.html css js $TEMP_DIR/ 2>/dev/null || true
    
    # Remove unnecessary files
    find $TEMP_DIR -name "*.pyc" -delete
    find $TEMP_DIR -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Create tarball
    tar -czf deploy.tar.gz -C $TEMP_DIR .
    
    echo -e "${BLUE}📤 Uploading to Lightsail...${NC}"
    scp deploy.tar.gz ubuntu@$LIGHTSAIL_IP:/tmp/
    
    echo -e "${BLUE}🔧 Deploying on server...${NC}"
    ssh ubuntu@$LIGHTSAIL_IP << 'DEPLOY_SCRIPT'
    set -e
    
    # Colors for remote output
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    NC='\033[0m'
    
    echo -e "${BLUE}Extracting files...${NC}"
    cd /tmp
    tar -xzf deploy.tar.gz
    
    # Backup current version
    if [ -d "/home/ubuntu/bank-statement-converter/backend" ]; then
        echo -e "${BLUE}Backing up current version...${NC}"
        sudo cp -r /home/ubuntu/bank-statement-converter /home/ubuntu/bank-statement-converter.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Ensure directories exist
    mkdir -p /home/ubuntu/bank-statement-converter/{backend,frontend/{js,css},uploads,failed_pdfs,data}
    
    # Copy files
    echo -e "${BLUE}Copying backend files...${NC}"
    cp -r backend/* /home/ubuntu/bank-statement-converter/backend/
    
    echo -e "${BLUE}Copying frontend files...${NC}"
    cp -r *.html /home/ubuntu/bank-statement-converter/frontend/ 2>/dev/null || true
    cp -r css/* /home/ubuntu/bank-statement-converter/frontend/css/ 2>/dev/null || true
    cp -r js/* /home/ubuntu/bank-statement-converter/frontend/js/ 2>/dev/null || true
    
    # Update permissions
    chmod -R 755 /home/ubuntu/bank-statement-converter
    
    # Install/update dependencies
    cd /home/ubuntu/bank-statement-converter
    if [ -f "venv/bin/activate" ]; then
        echo -e "${BLUE}Updating Python dependencies...${NC}"
        source venv/bin/activate
        pip install -r backend/requirements-fastapi.txt --upgrade
    fi
    
    # Restart service
    echo -e "${BLUE}Restarting service...${NC}"
    sudo systemctl restart bankconverter
    
    # Wait for service to start
    sleep 3
    
    # Check status
    if sudo systemctl is-active --quiet bankconverter; then
        echo -e "${GREEN}✅ Service started successfully${NC}"
    else
        echo -e "${RED}❌ Service failed to start${NC}"
        sudo journalctl -u bankconverter -n 20
        exit 1
    fi
    
    # Cleanup
    rm -f /tmp/deploy.tar.gz
    rm -rf /tmp/backend /tmp/*.html /tmp/css /tmp/js 2>/dev/null || true
    
    echo -e "${GREEN}✅ Deployment completed!${NC}"
DEPLOY_SCRIPT
    
    # Cleanup local files
    rm -f deploy.tar.gz
    rm -rf $TEMP_DIR
    
    echo -e "\n${GREEN}✅ Deployment successful!${NC}"
    echo -e "${BLUE}🌐 Your app is available at: http://$LIGHTSAIL_IP${NC}"
}

# Function to view logs
view_logs() {
    echo -e "${BLUE}📋 Viewing service logs...${NC}"
    ssh ubuntu@$LIGHTSAIL_IP "sudo journalctl -u bankconverter -f"
}

# Function to restart service
restart_service() {
    echo -e "${BLUE}🔄 Restarting service...${NC}"
    ssh ubuntu@$LIGHTSAIL_IP "sudo systemctl restart bankconverter && echo '✅ Service restarted'"
}

# Function to check status
check_status() {
    echo -e "${BLUE}📊 Checking service status...${NC}"
    ssh ubuntu@$LIGHTSAIL_IP "sudo systemctl status bankconverter"
}

# Main menu
case "${1:-deploy}" in
    "deploy")
        check_connection && deploy
        ;;
    "logs")
        check_connection && view_logs
        ;;
    "restart")
        check_connection && restart_service
        ;;
    "status")
        check_connection && check_status
        ;;
    "test")
        check_connection
        ;;
    *)
        echo "Usage: $0 {deploy|logs|restart|status|test}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Deploy latest code to Lightsail (default)"
        echo "  logs    - View live service logs"
        echo "  restart - Restart the service"
        echo "  status  - Check service status"
        echo "  test    - Test connection to Lightsail"
        exit 1
        ;;
esac