# CSS Migration Guide

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
