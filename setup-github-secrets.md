# Setting Up GitHub Secrets for Deployment

## Required GitHub Secrets

You need to add these secrets to your GitHub repository:

### 1. LIGHTSAIL_HOST
Your Lightsail instance's IP address (e.g., `3.145.67.89`)

### 2. LIGHTSAIL_SSH_KEY
Your private SSH key to access Lightsail

## Step-by-Step Setup

### 1. Get Your Lightsail IP
- Go to AWS Lightsail console
- Click on your instance
- Copy the Public IP

### 2. Get Your SSH Key

#### Option A: Download from Lightsail
1. In Lightsail console, go to Account → SSH keys
2. Download your default key (usually `LightsailDefaultKey-us-east-2.pem`)

#### Option B: Create a new key pair
```bash
# On your local machine
ssh-keygen -t rsa -b 4096 -f lightsail_deploy_key -N ""

# Copy public key to Lightsail instance
cat lightsail_deploy_key.pub | ssh ubuntu@YOUR_IP "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### 3. Add Secrets to GitHub

1. Go to your GitHub repository
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"

Add these secrets:

**LIGHTSAIL_HOST**
```
3.145.67.89  # Your actual IP
```

**LIGHTSAIL_SSH_KEY**
```
-----BEGIN RSA PRIVATE KEY-----
[Your entire private key content including BEGIN and END lines]
-----END RSA PRIVATE KEY-----
```

## Testing Your Setup

### Manual Test
```bash
# Test connection from your local machine
ssh -i path/to/your/key ubuntu@YOUR_IP "echo 'Connection successful!'"
```

### GitHub Actions Test
1. Make a small change to README.md
2. Commit and push to main branch
3. Go to Actions tab in GitHub
4. Watch the deployment run

## Security Best Practices

1. **Never commit SSH keys to your repository**
2. **Use deployment-specific keys** (not your personal SSH key)
3. **Restrict key permissions** on Lightsail:
   ```bash
   chmod 600 ~/.ssh/authorized_keys
   ```

4. **IP Whitelisting** (optional but recommended):
   - Get GitHub Actions IP ranges: https://api.github.com/meta
   - Configure Lightsail firewall to only allow SSH from GitHub

## Troubleshooting

### Permission denied (publickey)
- Check if key is properly formatted in GitHub secret
- Ensure no extra spaces or newlines

### Host key verification failed  
- The workflow automatically adds host to known_hosts
- If still failing, check if IP is correct

### Service fails to start
- Check logs: `ssh ubuntu@IP "sudo journalctl -u bankconverter -n 50"`
- Ensure all Python dependencies are installed

## Alternative: GitHub Lightsail Action

For even easier setup, you can use the official AWS action:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-2

- name: Deploy using AWS CLI
  run: |
    # Use AWS CLI to manage Lightsail
    aws lightsail put-instance-public-ports --instance-name bank-statement-converter ...
```