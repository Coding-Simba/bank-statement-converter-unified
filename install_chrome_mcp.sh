#!/bin/bash

# Chrome MCP Server Installation Script

echo "Chrome MCP Server Installation"
echo "=============================="
echo ""

# Check prerequisites
echo "1. Checking prerequisites..."

# Check Node.js version
NODE_VERSION=$(node -v 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "❌ Node.js not found. Please install Node.js >= 18.19.0"
    echo "   Visit: https://nodejs.org/"
    exit 1
else
    echo "✅ Node.js found: $NODE_VERSION"
fi

# Check if pnpm is installed
if command -v pnpm &> /dev/null; then
    echo "✅ pnpm is installed"
    PACKAGE_MANAGER="pnpm"
else
    echo "⚠️  pnpm not found, using npm instead"
    PACKAGE_MANAGER="npm"
fi

echo ""
echo "2. Installing mcp-chrome-bridge globally..."

if [ "$PACKAGE_MANAGER" = "pnpm" ]; then
    # Enable scripts for pnpm
    echo "   Configuring pnpm..."
    pnpm config set enable-pre-post-scripts true
    
    # Install the bridge
    echo "   Installing with pnpm..."
    pnpm install -g mcp-chrome-bridge
    
    # Check if installation succeeded
    if [ $? -ne 0 ]; then
        echo "   Installation failed, trying manual registration..."
        pnpm install -g mcp-chrome-bridge
        mcp-chrome-bridge register
    fi
else
    # Install with npm
    echo "   Installing with npm..."
    npm install -g mcp-chrome-bridge
fi

echo ""
echo "3. Checking installation..."

# Find installation path
if [ "$PACKAGE_MANAGER" = "pnpm" ]; then
    INSTALL_PATH=$(pnpm list -g mcp-chrome-bridge 2>/dev/null | grep -A 1 "mcp-chrome-bridge" | tail -1 | awk '{print $1}')
else
    INSTALL_PATH=$(npm list -g mcp-chrome-bridge 2>/dev/null | grep "mcp-chrome-bridge" | head -1)
fi

if [ -n "$INSTALL_PATH" ]; then
    echo "✅ mcp-chrome-bridge installed successfully"
    echo "   Location: $INSTALL_PATH"
else
    echo "❌ Installation verification failed"
    exit 1
fi

echo ""
echo "4. Downloading Chrome Extension..."

# Create directory for extension
EXTENSION_DIR="$HOME/Downloads/chrome-mcp-extension"
mkdir -p "$EXTENSION_DIR"

# Download latest release
echo "   Downloading from GitHub..."
cd "$EXTENSION_DIR"

# Get latest release URL
LATEST_RELEASE_URL="https://api.github.com/repos/hangwin/mcp-chrome/releases/latest"
DOWNLOAD_URL=$(curl -s "$LATEST_RELEASE_URL" | grep "browser_download_url.*extension.zip" | cut -d '"' -f 4)

if [ -z "$DOWNLOAD_URL" ]; then
    echo "   Could not find download URL automatically."
    echo "   Please download manually from: https://github.com/hangwin/mcp-chrome/releases"
    echo "   Download the extension.zip file"
else
    curl -L -o extension.zip "$DOWNLOAD_URL"
    unzip -o extension.zip
    rm extension.zip
    echo "✅ Extension downloaded to: $EXTENSION_DIR"
fi

echo ""
echo "5. Next Steps:"
echo "=============="
echo ""
echo "A. Load the Chrome Extension:"
echo "   1. Open Chrome and go to: chrome://extensions/"
echo "   2. Enable 'Developer mode' (top right)"
echo "   3. Click 'Load unpacked'"
echo "   4. Select folder: $EXTENSION_DIR"
echo "   5. Click the extension icon and click 'Connect'"
echo ""
echo "B. Configure your MCP client (e.g., Claude Desktop):"
echo ""
echo "   Add to your MCP client config:"
echo ""
echo "   For Streamable HTTP (Recommended):"
echo "   {"
echo "     \"mcpServers\": {"
echo "       \"chrome-mcp-server\": {"
echo "         \"type\": \"streamableHttp\","
echo "         \"url\": \"http://127.0.0.1:12306/mcp\""
echo "       }"
echo "     }"
echo "   }"
echo ""
echo "C. Test your website:"
echo "   Once connected, you can ask Claude to:"
echo "   - Take screenshots of bankcsvconverter.com"
echo "   - Test file upload functionality"
echo "   - Analyze transaction extraction results"
echo "   - Monitor network requests during conversion"
echo ""
echo "Installation script complete! 🎉"