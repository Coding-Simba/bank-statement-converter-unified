#!/bin/bash

# Download Chrome MCP Extension

echo "Downloading Chrome MCP Extension..."
echo "==================================="

# Create directory
EXTENSION_DIR="$HOME/Downloads/chrome-mcp-extension"
mkdir -p "$EXTENSION_DIR"
cd "$EXTENSION_DIR"

# Download the extension
echo "Downloading from GitHub release v0.0.6..."
curl -L -o extension.zip "https://github.com/hangwin/mcp-chrome/releases/download/v0.0.6/extension.zip"

if [ -f "extension.zip" ]; then
    echo "✅ Download complete"
    
    echo "Extracting extension..."
    unzip -o extension.zip
    rm extension.zip
    
    echo "✅ Extension extracted to: $EXTENSION_DIR"
    echo ""
    echo "Files in extension directory:"
    ls -la
else
    echo "❌ Download failed. Please download manually from:"
    echo "   https://github.com/hangwin/mcp-chrome/releases"
fi

echo ""
echo "Next: Load the extension in Chrome"
echo "1. Open Chrome and go to: chrome://extensions/"
echo "2. Enable 'Developer mode' (top right)"
echo "3. Click 'Load unpacked'"
echo "4. Select: $EXTENSION_DIR"