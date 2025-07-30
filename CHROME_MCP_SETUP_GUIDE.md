# Chrome MCP Server Setup Guide for Testing BankCSVConverter.com

## ✅ Installation Complete

### What's Installed:
1. **mcp-chrome-bridge** (npm package) - Installed globally ✅
2. **Chrome Extension** - Downloaded to `/Users/MAC/Downloads/chrome-mcp-extension` ✅

## 🚀 Setup Steps

### 1. Load the Chrome Extension
1. Open Chrome and navigate to: `chrome://extensions/`
2. Enable **Developer mode** (toggle in top right)
3. Click **Load unpacked**
4. Select folder: `/Users/MAC/Downloads/chrome-mcp-extension`
5. You should see "Chrome MCP Server" extension loaded
6. Click the extension icon in toolbar and click **Connect**

### 2. Configure Claude Desktop (or your MCP client)

Add this to your Claude Desktop config file:
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "chrome-mcp-server": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:12306/mcp"
    }
  }
}
```

### 3. Restart Claude Desktop
After adding the config, restart Claude Desktop to load the MCP server.

## 🧪 Testing Your Website

Once connected, you can ask Claude to:

### Basic Tests:
```
- "Take a screenshot of bankcsvconverter.com"
- "Navigate to bankcsvconverter.com and check if it loads"
- "Click on the upload button on bankcsvconverter.com"
```

### File Upload Testing:
```
- "Upload the Westpac PDF at /Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf to bankcsvconverter.com"
- "Monitor the network requests when uploading a file"
- "Check how many transactions were extracted"
```

### Advanced Testing:
```
- "Test uploading multiple PDFs and check extraction accuracy"
- "Monitor console errors during file conversion"
- "Take screenshots of the results page"
- "Check if all transactions are properly displayed"
```

### Network Monitoring:
```
- "Show me all API calls made during file upload"
- "What's the response from the /api/convert endpoint?"
- "Monitor network errors during conversion"
```

## 📋 Available Chrome MCP Tools

- **navigate_to** - Navigate to URLs
- **take_screenshot** - Capture screenshots
- **click_element** - Click on page elements
- **fill_input** - Fill form inputs
- **get_page_content** - Extract page content
- **monitor_network** - Monitor network requests
- **execute_javascript** - Run JS in page context
- **upload_file** - Handle file uploads
- **get_console_logs** - View console messages

## 🔍 Troubleshooting

1. **Extension not connecting?**
   - Make sure the extension shows "Connected" status
   - Check Chrome developer console for errors

2. **Claude not recognizing MCP?**
   - Verify config file is properly formatted JSON
   - Restart Claude Desktop after config changes

3. **Can't upload files?**
   - Ensure file paths are correct
   - Check if website file input is accessible

## 💡 Example Test Workflow

```
1. "Navigate to bankcsvconverter.com"
2. "Take a screenshot of the homepage"
3. "Click on the upload area"
4. "Upload /Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf"
5. "Monitor network requests during upload"
6. "Wait for conversion to complete"
7. "Take screenshot of results"
8. "Get the extracted transaction count from the page"
9. "Download the CSV file"
```

This will help you verify that all 51 transactions are being extracted from the Woodforest PDF!