# CSS Duplicate Selectors Report

Found 94 duplicate selectors across CSS files


## Selector: `to`
Found in 6 files:

### unified-styles.css
```css
opacity: 1;
        transform: translateY(0);
```

### unified-styles.css
```css
opacity: 1;
```

### unified-styles.css
```css
transform: scale(1); opacity: 1;
```

### modern-style.css
```css
opacity: 1;
        transform: translateY(0);
```

### modern-style.css
```css
opacity: 1;
```

### modern-style.css
```css
transform: scale(1);
```

## Selector: `h2`
Found in 5 files:

### unified-styles.css
```css
font-size: 2rem;
```

### unified-styles.css
```css
font-size: 1.5rem;
```

### modern-style.css
```css
font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 1.5rem;
    text-align: center;
    color: var(--dark);
```

### modern-style.css
```css
font-size: 2rem;
```

### style-seo.css
```css
font-size: 2rem;
    margin-bottom: 1rem;
    text-align: center;
```

## Selector: `.hero h1`
Found in 5 files:

### unified-styles.css
```css
font-size: 3rem;
    margin-bottom: var(--spacing-md);
    color: white;
    animation: fadeInUp 0.8s ease-out;
```

### unified-styles.css
```css
font-size: 2.5rem;
```

### modern-style.css
```css
font-size: 3.5rem;
    font-weight: 700;
    margin-bottom: 1.5rem;
    color: white;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    animation: fadeInUp 0.8s ease-out;
```

### style.css
```css
font-size: 2.5rem;
    margin-bottom: 20px;
    color: #2c3e50;
```

### style.css
```css
font-size: 2rem;
```

## Selector: `.upload-area`
Found in 5 files:

### unified-styles.css
```css
background: white;
    border-radius: var(--radius-xl);
    padding: var(--spacing-xl);
    max-width: var(--max-width-sm);
    margin: var(--spacing-lg) auto;
    box-shadow: var(--shadow-xl);
    tr...
```

### unified-styles.css
```css
padding: var(--spacing-lg);
```

### modern-style.css
```css
padding: 2rem;
        margin: 2rem 1rem;
```

### style-seo.css
```css
background: white;
    border-radius: 20px;
    padding: 3rem;
    box-shadow: var(--shadow-lg);
    margin: 2rem auto;
    max-width: 600px;
```

### style-seo.css
```css
padding: 2rem;
```

## Selector: `body`
Found in 4 files:

### unified-styles.css
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    font-size: 16px;
    line-height: 1.6;
    color: var(--text-primary);
    background-color: var(--bg-primary);
 ...
```

### modern-style.css
```css
font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', 'Segoe UI', sans-serif;
    color: var(--dark);
    line-height: 1.6;
    background: #fafafa;
    overflow-x: hidden;
```

### style.css
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f8f9fa;
```

### style-seo.css
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--dark);
    line-height: 1.6;
    background: var(--white);
```

## Selector: `h3`
Found in 4 files:

### unified-styles.css
```css
font-size: 1.5rem;
```

### unified-styles.css
```css
font-size: 1.25rem;
```

### modern-style.css
```css
font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: var(--dark);
```

### style-seo.css
```css
font-size: 1.3rem;
    margin-bottom: 0.5rem;
```

## Selector: `.container`
Found in 4 files:

### unified-styles.css
```css
width: 100%;
    max-width: var(--max-width-xl);
    margin: 0 auto;
    padding: 0 var(--spacing-md);
```

### modern-style.css
```css
max-width: 1200px;
    margin: 0 auto;
```

### style.css
```css
max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
```

### style-seo.css
```css
max-width: 1200px;
    margin: 0 auto;
```

## Selector: `header`
Found in 4 files:

### unified-styles.css
```css
background: var(--bg-primary);
    box-shadow: var(--shadow-sm);
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    height: 60px;
```

### modern-style.css
```css
background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    position: sticky;
    top: 0;
    z-...
```

### style.css
```css
background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    position: sticky;
    top: 0;
    z-index: 1000;
```

### style-seo.css
```css
background: white;
    box-shadow: var(--shadow);
    position: sticky;
    top: 0;
    z-index: 100;
```

## Selector: `.nav-menu`
Found in 4 files:

### unified-styles.css
```css
display: flex;
    gap: var(--spacing-lg);
    list-style: none;
```

### unified-styles.css
```css
display: none;
        position: absolute;
        top: 60px;
        left: 0;
        right: 0;
        background: white;
        flex-direction: column;
        padding: var(--spacing-md);
        ...
```

### modern-style.css
```css
display: flex;
    gap: 30px;
    list-style: none;
```

### style.css
```css
display: flex;
    list-style: none;
    align-items: center;
    gap: 30px;
```

## Selector: `.menu-toggle`
Found in 4 files:

### unified-styles.css
```css
display: none;
    background: none;
    border: none;
    cursor: pointer;
    padding: 5px;
```

### unified-styles.css
```css
display: block;
```

### modern-style.css
```css
display: none;
    background: none;
    border: none;
    cursor: pointer;
    padding: 5px;
```

### modern-style.css
```css
display: block;
```

## Selector: `.hero`
Found in 4 files:

### unified-styles.css
```css
background: var(--gradient-primary);
    color: white;
    padding: var(--spacing-xxl) 0;
    text-align: center;
    position: relative;
    overflow: hidden;
```

### modern-style.css
```css
background: var(--gradient);
    padding: 6rem 2rem 4rem;
    text-align: center;
    position: relative;
    overflow: hidden;
```

### style.css
```css
padding: 60px 0;
    background: #f8f9fa;
    text-align: center;
```

### style-seo.css
```css
background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 4rem 2rem;
    text-align: center;
```

## Selector: `footer`
Found in 4 files:

### unified-styles.css
```css
background: var(--bg-tertiary);
    padding: var(--spacing-xl) 0 var(--spacing-lg);
    border-top: 1px solid var(--border-color);
```

### modern-style.css
```css
background: var(--dark);
    color: white;
    padding: 4rem 2rem 2rem;
```

### style.css
```css
background: #2c3e50;
    color: white;
    padding: 30px 0;
    text-align: center;
```

### style-seo.css
```css
background: var(--dark);
    color: white;
    padding: 3rem 2rem 1rem;
```

## Selector: `.footer-content`
Found in 4 files:

### unified-styles.css
```css
display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: var(--spacing-xl);
    margin-bottom: var(--spacing-lg);
```

### unified-styles.css
```css
grid-template-columns: 1fr;
        gap: var(--spacing-lg);
```

### modern-style.css
```css
display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 3rem;
    max-width: 1200px;
    margin: 0 auto;
```

### style-seo.css
```css
display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 2rem;
    max-width: 1200px;
    margin: 0 auto;
```

## Selector: `.nav-links`
Found in 4 files:

### modern-style.css
```css
display: flex;
    gap: 2.5rem;
    list-style: none;
    align-items: center;
```

### modern-style.css
```css
display: none;
```

### style-seo.css
```css
display: flex;
    gap: 2rem;
    list-style: none;
```

### style-seo.css
```css
display: none;
```

## Selector: `:root`
Found in 3 files:

### unified-styles.css
```css
--primary: #667eea;
    --primary-dark: #5a67d8;
    --primary-light: #7c8ff0;
    --secondary: #764ba2;
    --accent: #22c55e;
    --danger: #ef4444;
    --warning: #f59e0b;
    
    
    --text-prim...
```

### modern-style.css
```css
--primary: #007AFF;
    --primary-dark: #0051D5;
    --secondary: #5856D6;
    --success: #34C759;
    --danger: #FF3B30;
    --warning: #FF9500;
    --dark: #1D1D1F;
    --gray: #86868B;
    --light-...
```

### style-seo.css
```css
--primary: #007AFF;
    --primary-dark: #0051D5;
    --secondary: #5856D6;
    --success: #34C759;
    --dark: #1D1D1F;
    --gray: #86868B;
    --light-gray: #F2F2F7;
    --white: #FFFFFF;
    --grad...
```

## Selector: `.nav-menu a`
Found in 3 files:

### unified-styles.css
```css
color: var(--text-secondary);
    text-decoration: none;
    font-weight: 500;
    font-size: 0.95rem;
    transition: var(--transition-fast);
```

### modern-style.css
```css
color: #666;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.95rem;
    transition: color 0.3s ease;
```

### style.css
```css
text-decoration: none;
    color: #333;
    font-weight: 500;
    transition: color 0.3s;
```

## Selector: `.nav-menu a:hover`
Found in 3 files:

### unified-styles.css
```css
color: var(--primary);
```

### modern-style.css
```css
color: #667eea;
```

### style.css
```css
color: #2c5aa0;
```

## Selector: `.upload-btn`
Found in 3 files:

### unified-styles.css
```css
background: var(--gradient-primary);
    color: white;
    border: none;
    padding: 16px 40px;
    font-size: 1.1rem;
    font-weight: 600;
    border-radius: 50px;
    cursor: pointer;
    transiti...
```

### modern-style.css
```css
background: var(--gradient);
    color: white;
    border: none;
    padding: 1.2rem 3rem;
    font-size: 1.1rem;
    font-weight: 600;
    border-radius: 100px;
    cursor: pointer;
    transition: a...
```

### style-seo.css
```css
background: var(--gradient);
    color: white;
    border: none;
    padding: 1rem 3rem;
    font-size: 1.2rem;
    font-weight: 600;
    border-radius: 50px;
    cursor: pointer;
    transition: tran...
```

## Selector: `.upload-btn:hover`
Found in 3 files:

### unified-styles.css
```css
background: var(--gradient-hover);
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
```

### modern-style.css
```css
transform: translateY(-2px);
    box-shadow: 0 15px 30px rgba(102, 126, 234, 0.4);
```

### style-seo.css
```css
transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
```

## Selector: `.content-section`
Found in 3 files:

### unified-styles.css
```css
padding: var(--spacing-xxl) 0;
    background: var(--bg-primary);
```

### modern-style.css
```css
padding: 5rem 2rem;
```

### style-seo.css
```css
padding: 4rem 2rem;
```

## Selector: `.content-section:nth-child(even)`
Found in 3 files:

### unified-styles.css
```css
background: var(--bg-secondary);
```

### modern-style.css
```css
background: var(--light-gray);
```

### style-seo.css
```css
background: var(--light-gray);
```

## Selector: `.feature-icon`
Found in 3 files:

### unified-styles.css
```css
font-size: 2.5rem;
    margin-bottom: var(--spacing-sm);
    display: block;
```

### modern-style.css
```css
font-size: 3rem;
    margin-bottom: 1rem;
```

### style.css
```css
width: 80px;
    height: 80px;
    margin: 0 auto 20px;
    background: #f0f7ff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
```

## Selector: `.faq-item`
Found in 3 files:

### unified-styles.css
```css
background: white;
    border-radius: var(--radius-md);
    padding: var(--spacing-lg);
    margin-bottom: var(--spacing-md);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-color...
```

### modern-style.css
```css
background: white;
    margin-bottom: 1rem;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: var(--shadow);
    transition: all 0.3s ease;
```

### style-seo.css
```css
margin-bottom: 2rem;
    padding: 1.5rem;
    background: white;
    border-radius: 10px;
    box-shadow: var(--shadow);
```

## Selector: `.cta-section`
Found in 3 files:

### unified-styles.css
```css
background: var(--gradient-primary);
    color: white;
    padding: var(--spacing-xxl) 0;
    text-align: center;
```

### modern-style.css
```css
background: var(--gradient);
    color: white;
    text-align: center;
    padding: 5rem 2rem;
    position: relative;
    overflow: hidden;
```

### style-seo.css
```css
background: var(--gradient);
    color: white;
    text-align: center;
    padding: 4rem 2rem;
```

## Selector: `.cta-section h2`
Found in 3 files:

### unified-styles.css
```css
color: white;
    margin-bottom: var(--spacing-md);
```

### modern-style.css
```css
font-size: 2rem;
```

### style-seo.css
```css
color: white;
```

## Selector: `.cta-button`
Found in 3 files:

### unified-styles.css
```css
background: white;
    color: var(--primary);
    padding: 16px 40px;
    font-size: 1.1rem;
    font-weight: 600;
    border-radius: 50px;
    display: inline-block;
    transition: var(--transition-...
```

### modern-style.css
```css
display: inline-block;
    background: white;
    color: var(--primary);
    padding: 1.2rem 3rem;
    border-radius: 100px;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s e...
```

### style-seo.css
```css
display: inline-block;
    background: white;
    color: var(--primary);
    padding: 1rem 3rem;
    border-radius: 50px;
    text-decoration: none;
    font-weight: 600;
    margin-top: 1rem;
    tra...
```

## Selector: `.cta-button:hover`
Found in 3 files:

### unified-styles.css
```css
transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    color: var(--primary-dark);
```

### modern-style.css
```css
transform: translateY(-3px);
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.2);
```

### style-seo.css
```css
transform: translateY(-2px);
```

## Selector: `.footer-section h4`
Found in 3 files:

### unified-styles.css
```css
color: var(--text-primary);
    margin-bottom: var(--spacing-sm);
```

### modern-style.css
```css
margin-bottom: 1.5rem;
    font-size: 1.1rem;
    color: white;
```

### style-seo.css
```css
margin-bottom: 1rem;
```

## Selector: `.footer-section ul`
Found in 3 files:

### unified-styles.css
```css
list-style: none;
```

### modern-style.css
```css
list-style: none;
```

### style-seo.css
```css
list-style: none;
```

## Selector: `.footer-section a`
Found in 3 files:

### unified-styles.css
```css
color: var(--text-secondary);
    font-size: 0.95rem;
```

### modern-style.css
```css
color: rgba(255, 255, 255, 0.7);
    text-decoration: none;
    display: block;
    padding: 0.5rem 0;
    transition: all 0.3s ease;
```

### style-seo.css
```css
color: #ccc;
    text-decoration: none;
    display: block;
    padding: 0.25rem 0;
```
