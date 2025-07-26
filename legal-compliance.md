# Legal Compliance for US Customers from Netherlands

## Data Protection Requirements

### 1. Privacy Policy Required
Since you're processing financial documents, you need:
- Clear privacy policy
- Data retention policy (you already delete after 24h ✓)
- SSL certificate (mandatory for financial data)

### 2. US Compliance
- No PCI DSS required (not processing payments)
- Consider CCPA for California users
- State where data is processed (US servers)

### 3. EU Considerations
As a Netherlands-based business:
- GDPR still applies to you
- Need cookie consent banner
- Right to deletion (already implemented ✓)

## Recommended Setup

1. **Terms of Service** - Add to your site
2. **Privacy Policy** - Clearly state:
   - Data is processed on US servers
   - Auto-deleted after 24 hours
   - No data sharing
   - Netherlands company serving US market

3. **Security**
   - Use HTTPS everywhere (required)
   - Encrypt uploads in transit
   - No storage of sensitive data

## Simple Implementation

Add to your homepage:
```html
<footer>
  <p>
    By using this service, you agree to our 
    <a href="/terms">Terms of Service</a> and 
    <a href="/privacy">Privacy Policy</a>
  </p>
  <p>🇳🇱 Netherlands company | 🇺🇸 US servers | 🔒 Your data deleted after 24h</p>
</footer>
```