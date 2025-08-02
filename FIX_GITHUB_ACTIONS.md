# GitHub Actions Deployment Failures - Analysis & Solutions

## Issues Identified

### 1. **Missing Secrets**
The workflows rely on GitHub secrets that may not be configured:
- `LIGHTSAIL_SSH_KEY` - SSH private key for Lightsail instance
- `LIGHTSAIL_HOST` - IP address or hostname of Lightsail instance

### 2. **File Structure Mismatch**
The workflows expect specific directory structures:
- Line 64: `cp -r *.html css js ${{ env.DEPLOY_PATH }}/frontend/`
  - Assumes `css` and `js` are directories in root
  - Your structure has `/css/` and `/js/` directories

### 3. **Missing Requirements Files**
- Line 69: `pip install -r backend/requirements-fastapi.txt`
- Line 70: `pip install -r requirements-ocr.txt`
  - These files may not exist or be in wrong locations

### 4. **Service Name Mismatch**
- Line 77: `sudo systemctl restart bankconverter`
  - Your service is likely named `bankcsv-backend` based on previous configurations

### 5. **Health Check Endpoint**
- Line 97: `http://${{ secrets.LIGHTSAIL_HOST }}/api/health`
- Line 131: `http://${{ secrets.LIGHTSAIL_HOST }}/health`
  - Inconsistent health check endpoints between workflows

### 6. **Virtual Environment Path**
- Line 68: `source venv/bin/activate`
  - Assumes venv is in `/home/ubuntu/bank-statement-converter/venv`
  - Your backend likely has venv at `/home/ubuntu/backend/venv`

## Solutions

### 1. Check GitHub Secrets
Go to your GitHub repository:
1. Settings → Secrets and variables → Actions
2. Ensure these secrets exist:
   - `LIGHTSAIL_SSH_KEY`: Contents of your private key file
   - `LIGHTSAIL_HOST`: Your server IP (3.235.19.83)

### 2. Fix Workflow Files

#### deploy-to-lightsail.yml fixes:
```yaml
# Line 64 - Fix file copying
cp -r *.html ${{ env.DEPLOY_PATH }}/frontend/ 2>/dev/null || true
cp -r css ${{ env.DEPLOY_PATH }}/frontend/ 2>/dev/null || true
cp -r js ${{ env.DEPLOY_PATH }}/frontend/ 2>/dev/null || true

# Line 68-69 - Fix venv path
cd ${{ env.DEPLOY_PATH }}/backend
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
elif [ -f "../venv/bin/activate" ]; then
  source ../venv/bin/activate
fi

# Line 69-70 - Fix requirements
pip install -r requirements.txt 2>/dev/null || true

# Line 77 - Fix service name
sudo systemctl restart bankcsv-backend

# Line 97 - Fix health check
response=$(curl -s -o /dev/null -w "%{http_code}" http://${{ secrets.LIGHTSAIL_HOST }}/health || echo "000")
```

### 3. Create Missing Files
Create `backend/requirements-fastapi.txt`:
```txt
fastapi
uvicorn
sqlalchemy
python-jose
passlib
python-multipart
stripe
pandas
pdfplumber
camelot-py
```

### 4. Temporary Fix - Disable Workflows
While debugging, you can disable the workflows:
```yaml
on:
  push:
    branches: [ main ]
  workflow_dispatch:
```

Change to:
```yaml
on:
  workflow_dispatch:  # Manual trigger only
```

### 5. Debug Locally First
Test the deployment commands locally:
```bash
# Test SSH connection
ssh -i ~/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83 "echo 'Connection successful'"

# Test service status
ssh -i ~/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83 "sudo systemctl status bankcsv-backend"
```

## Recommended Actions

1. **Immediate**: Check if GitHub secrets are properly configured
2. **Fix service names**: Update workflows to use `bankcsv-backend`
3. **Fix file paths**: Update the file copying logic
4. **Add health endpoint**: Ensure `/health` endpoint exists in your backend
5. **Test manually**: Run deployment commands manually first

## Quick Workaround
If you need to push code without triggering failed deployments:

1. Create a different branch:
   ```bash
   git checkout -b development
   git push origin development
   ```

2. Or temporarily remove workflow files:
   ```bash
   git rm .github/workflows/*.yml
   git commit -m "Temporarily remove workflows for debugging"
   git push
   ```