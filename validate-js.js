// Extract and validate JavaScript from index.html
const fs = require('fs');

const html = fs.readFileSync('index.html', 'utf8');

// Extract JavaScript between <script> tags
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (scriptMatch) {
    const jsCode = scriptMatch[1];
    
    console.log('Extracted JavaScript code length:', jsCode.length);
    
    // Try to parse it to check for syntax errors
    try {
        // Create a function to test the code
        const testFunc = new Function(jsCode);
        console.log('✅ JavaScript syntax is valid!');
        
        // Check if key functions exist
        const hasOpenFileDialog = jsCode.includes('function openFileDialog');
        const hasHandleFileSelect = jsCode.includes('function handleFileSelect');
        const hasProcessFile = jsCode.includes('function processFile');
        
        console.log('✅ openFileDialog function:', hasOpenFileDialog ? 'Found' : 'NOT FOUND');
        console.log('✅ handleFileSelect function:', hasHandleFileSelect ? 'Found' : 'NOT FOUND');
        console.log('✅ processFile function:', hasProcessFile ? 'Found' : 'NOT FOUND');
        
        // Check onclick handlers in HTML
        const hasOnclick = html.includes('onclick="openFileDialog()"');
        const hasOnchange = html.includes('onchange="handleFileSelect(event)"');
        
        console.log('✅ onclick handler:', hasOnclick ? 'Found' : 'NOT FOUND');
        console.log('✅ onchange handler:', hasOnchange ? 'Found' : 'NOT FOUND');
        
    } catch (error) {
        console.error('❌ JavaScript syntax error:', error.message);
    }
} else {
    console.error('❌ No script tag found!');
}