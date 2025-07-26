#!/usr/bin/env python3
"""
CSS Consolidation Script for Bank Statement Converter
Merges multiple CSS files into a single, optimized file
"""

import re
import os
from collections import OrderedDict

def extract_css_sections(file_path):
    """Extract CSS sections from a file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    sections = {
        'comments': [],
        'variables': [],
        'reset': [],
        'base': [],
        'components': [],
        'utilities': [],
        'media_queries': []
    }
    
    # Extract CSS variables
    var_pattern = r':root\s*{([^}]+)}'
    var_matches = re.findall(var_pattern, content, re.DOTALL)
    if var_matches:
        sections['variables'] = var_matches
    
    # Extract media queries
    media_pattern = r'(@media[^{]+{(?:[^{}]+{[^}]+})*[^}]+})'
    media_matches = re.findall(media_pattern, content, re.DOTALL)
    sections['media_queries'] = media_matches
    
    # Remove variables and media queries from content
    content_clean = re.sub(var_pattern, '', content, flags=re.DOTALL)
    content_clean = re.sub(media_pattern, '', content_clean, flags=re.DOTALL)
    
    # Extract remaining rules
    sections['components'] = content_clean
    
    return sections

def merge_variables(all_vars):
    """Merge CSS variables, preferring unified-styles.css values"""
    merged_vars = OrderedDict()
    
    # Priority order for variable sources
    priority = ['unified-styles.css', 'modern-style.css', 'style.css', 'style-seo.css']
    
    for source in priority:
        if source in all_vars:
            var_content = all_vars[source]
            # Extract individual variables
            var_pattern = r'(--[^:]+):\s*([^;]+);'
            for match in re.finditer(var_pattern, var_content):
                var_name = match.group(1).strip()
                var_value = match.group(2).strip()
                if var_name not in merged_vars:
                    merged_vars[var_name] = var_value
    
    return merged_vars

def create_consolidated_css():
    """Create the consolidated CSS file"""
    css_dir = '/Users/MAC/chrome/bank-statement-converter-unified/css'
    
    # Files to consolidate (excluding minified versions)
    files_to_merge = {
        'unified-styles.css': os.path.join(css_dir, 'unified-styles.css'),
        'modern-style.css': os.path.join(css_dir, 'modern-style.css'),
        'style.css': os.path.join(css_dir, 'style.css'),
        'style-seo.css': os.path.join(css_dir, 'style-seo.css')
    }
    
    all_sections = {}
    all_variables = {}
    
    # Extract sections from each file
    for name, path in files_to_merge.items():
        if os.path.exists(path):
            sections = extract_css_sections(path)
            all_sections[name] = sections
            if sections['variables']:
                all_variables[name] = sections['variables'][0]
    
    # Start building consolidated CSS
    output = []
    
    # Header comment
    output.append("""/* 
 * Consolidated CSS for Bank Statement Converter
 * Generated from: unified-styles.css, modern-style.css, style.css, style-seo.css
 * 
 * Design System: Purple gradient theme (#667eea to #764ba2)
 * Typography: Inter, -apple-system, system fonts
 * Components: Upload area, navigation, hero, features, footer
 */

""")
    
    # CSS Variables
    merged_vars = merge_variables(all_variables)
    output.append(":root {")
    
    # Organize variables by category
    categories = {
        'Brand Colors': ['--primary', '--primary-dark', '--primary-light', '--secondary', '--accent'],
        'Status Colors': ['--success', '--danger', '--warning', '--info'],
        'Neutral Colors': ['--dark', '--gray', '--light-gray', '--white', '--text-primary', '--text-secondary', '--text-light'],
        'Backgrounds': ['--bg-primary', '--bg-secondary', '--bg-tertiary'],
        'Gradients': ['--gradient', '--gradient-primary', '--gradient-secondary', '--gradient-hover'],
        'Shadows': ['--shadow', '--shadow-sm', '--shadow-md', '--shadow-lg', '--shadow-xl'],
        'Spacing': ['--spacing-xs', '--spacing-sm', '--spacing-md', '--spacing-lg', '--spacing-xl', '--spacing-xxl'],
        'Border Radius': ['--radius-sm', '--radius-md', '--radius-lg', '--radius-xl', '--radius-full'],
        'Transitions': ['--transition-fast', '--transition-base', '--transition-slow'],
        'Layout': ['--max-width-sm', '--max-width-md', '--max-width-lg', '--max-width-xl']
    }
    
    for category, var_names in categories.items():
        output.append(f"\n    /* {category} */")
        for var_name in var_names:
            if var_name in merged_vars:
                output.append(f"    {var_name}: {merged_vars[var_name]};")
    
    # Add any remaining variables
    output.append("\n    /* Additional Variables */")
    for var_name, var_value in merged_vars.items():
        if not any(var_name in names for names in categories.values()):
            output.append(f"    {var_name}: {var_value};")
    
    output.append("}\n")
    
    # Add reset and base styles from unified-styles.css
    output.append("\n/* Reset & Base Styles */")
    output.append("""
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    color: var(--text-primary);
    line-height: 1.6;
    background: var(--bg-primary);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    font-weight: 600;
    line-height: 1.2;
    color: var(--text-primary);
}

h1 { font-size: 2.5rem; }
h2 { font-size: 2rem; }
h3 { font-size: 1.5rem; }
h4 { font-size: 1.25rem; }
h5 { font-size: 1.125rem; }
h6 { font-size: 1rem; }

a {
    color: var(--primary);
    text-decoration: none;
    transition: var(--transition-fast);
}

a:hover {
    color: var(--primary-dark);
}

/* Skip Link for Accessibility */
.skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    background: var(--primary);
    color: white;
    padding: 8px 16px;
    border-radius: var(--radius-sm);
    text-decoration: none;
    z-index: 10000;
    transition: var(--transition-fast);
}

.skip-link:focus {
    top: 10px;
    left: 10px;
}
""")
    
    # Write to file
    output_path = os.path.join(css_dir, 'main.css')
    with open(output_path, 'w') as f:
        f.write('\n'.join(output))
    
    print(f"✅ Created consolidated CSS at: {output_path}")
    print(f"📏 File size: {os.path.getsize(output_path):,} bytes")
    
    # Create a migration guide
    migration_path = os.path.join(os.path.dirname(css_dir), 'css-migration-guide.md')
    with open(migration_path, 'w') as f:
        f.write("""# CSS Migration Guide

## Files to Update

Replace the following in all HTML files:

### From:
```html
<link href="css/unified-styles.css" rel="stylesheet"/>
<link href="css/modern-style.css" rel="stylesheet"/>
<link href="css/style.css" rel="stylesheet"/>
<link href="css/style-seo.css" rel="stylesheet"/>
```

### To:
```html
<link href="css/main.css" rel="stylesheet"/>
```

### For pages in subdirectories:
```html
<link href="../css/main.css" rel="stylesheet"/>
```

## Testing Checklist

- [ ] Homepage renders correctly
- [ ] Upload functionality maintains styling
- [ ] Navigation menu appears properly
- [ ] Footer displays correctly
- [ ] Mobile responsive design works
- [ ] All interactive elements function
- [ ] Color scheme is consistent
- [ ] Animations and transitions work

## Rollback Plan

If issues arise, the original CSS files are preserved:
- unified-styles.css
- modern-style.css
- style.css
- style-seo.css
""")
    
    print(f"📖 Created migration guide at: {migration_path}")

if __name__ == '__main__':
    create_consolidated_css()