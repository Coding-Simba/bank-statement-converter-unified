const fs = require('fs');
const { JSDOM } = require('jsdom');

// Read the HTML file
const html = fs.readFileSync('index.html', 'utf8');

// Extract all JavaScript from the HTML
const scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
let match;
let scriptNumber = 0;
let allScripts = '';

console.log('=== Checking JavaScript in index.html ===\n');

while ((match = scriptRegex.exec(html)) !== null) {
    scriptNumber++;
    const scriptContent = match[1].trim();
    
    if (scriptContent && !scriptContent.includes('src=')) {
        console.log(`Script #${scriptNumber} (starts at position ${match.index}):`);
        console.log('First 100 chars:', scriptContent.substring(0, 100) + '...\n');
        
        // Try to parse the script
        try {
            // Add to all scripts to check for global conflicts
            allScripts += scriptContent + '\n\n';
            
            // Basic syntax check
            new Function(scriptContent);
            console.log('✅ No syntax errors detected\n');
        } catch (error) {
            console.log('❌ Syntax Error:', error.message);
            console.log('Near:', scriptContent.substring(0, 200), '\n');
        }
    }
}

// Check for duplicate declarations
console.log('\n=== Checking for duplicate declarations ===\n');
const declarations = ['menuToggle', 'navMenu', 'uploadBtn', 'fileInput'];
declarations.forEach(varName => {
    const regex = new RegExp(`(const|let|var)\\s+${varName}\\b`, 'g');
    const matches = allScripts.match(regex);
    if (matches && matches.length > 1) {
        console.log(`❌ Warning: '${varName}' is declared ${matches.length} times`);
    } else {
        console.log(`✅ '${varName}' is declared correctly`);
    }
});

// Check HTML structure
console.log('\n=== Checking HTML structure ===\n');
const requiredElements = [
    { id: 'uploadBtn', type: 'button' },
    { id: 'fileInput', type: 'input' },
    { id: 'uploadBox', type: 'div' },
    { id: 'progressContainer', type: 'div' },
    { id: 'resultContainer', type: 'div' },
    { id: 'progressFill', type: 'div' },
    { id: 'progressText', type: 'element' },
    { id: 'downloadBtn', type: 'button' },
    { id: 'convertAnotherBtn', type: 'button' }
];

requiredElements.forEach(elem => {
    const regex = new RegExp(`id=["']${elem.id}["']`, 'i');
    if (html.match(regex)) {
        console.log(`✅ Found element with id="${elem.id}"`);
    } else {
        console.log(`❌ Missing element with id="${elem.id}"`);
    }
});

console.log('\n=== Summary ===');
console.log('Check complete. If all items show ✅, the page should work correctly.');