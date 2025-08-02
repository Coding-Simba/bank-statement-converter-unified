# GitHub Actions - Fixed ✅

## Changes Made

### 1. Fixed Service Names
- Changed all instances of `bankconverter` to `bankcsv-backend` in both workflows
- This matches the actual systemd service name on the server

### 2. Fixed File Copying
- Split the single `cp -r *.html css js` command into separate commands
- This prevents failures when some directories don't exist
- Each copy operation now has `2>/dev/null || true` to handle missing files gracefully

### 3. Fixed Virtual Environment Paths
- Changed from `cd ${{ env.DEPLOY_PATH }}` to `cd ${{ env.DEPLOY_PATH }}/backend`
- Added fallback logic to check both `venv/bin/activate` and `../venv/bin/activate`
- This handles different venv locations on the server

### 4. Fixed Requirements Installation
- Changed from specific `requirements-fastapi.txt` to checking for multiple files
- Now checks for both `requirements.txt` and `requirements-fastapi.txt`
- Uses `--quiet` flag to reduce output

### 5. Fixed Health Check Endpoints
- Changed from `/api/health` to `/health` to match the actual endpoint
- This is consistent with the main.py implementation

### 6. Improved Error Handling
- Added `sudo systemctl status bankcsv-backend` when service fails to start
- This provides better debugging information in the workflow logs

## Files Modified
1. `.github/workflows/deploy-to-lightsail.yml`
2. `.github/workflows/deploy-with-rollback.yml`

## Next Steps

1. **Configure GitHub Secrets** (if not already done):
   - Go to Settings → Secrets and variables → Actions
   - Add `LIGHTSAIL_SSH_KEY` with your private key contents
   - Add `LIGHTSAIL_HOST` with value `3.235.19.83`

2. **Test the Deployment**:
   - The next push to main will trigger the workflows
   - Monitor the Actions tab for any issues

3. **Manual Deployment** (if needed):
   ```bash
   # SSH to server
   ssh -i ~/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83
   
   # Check service status
   sudo systemctl status bankcsv-backend
   
   # Check logs
   sudo journalctl -u bankcsv-backend -f
   ```

## Status
All identified issues have been fixed. The workflows should now deploy successfully once the GitHub secrets are configured.