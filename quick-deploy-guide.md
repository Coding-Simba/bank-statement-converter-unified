# Quick Deploy Guide - Netherlands to US Lightsail

## 🚀 Initial Setup (One Time)

### 1. Create Lightsail Instance
- Region: **US East (Ohio)**
- Blueprint: **Ubuntu 22.04**
- Plan: **$3.50/month**

### 2. First Time Setup
```bash
# SSH into Lightsail (use browser terminal)
curl -O https://raw.githubusercontent.com/YOUR_REPO/main/lightsail-setup.sh
bash lightsail-setup.sh
```

### 3. Configure GitHub Secrets
Add to your GitHub repo → Settings → Secrets:
- `LIGHTSAIL_HOST`: Your instance IP
- `LIGHTSAIL_SSH_KEY`: Your private SSH key

## 📦 Daily Deployment Options

### Option 1: GitHub Push (Automatic)
```bash
git add .
git commit -m "Update feature X"
git push origin main
# GitHub Actions deploys automatically!
```

### Option 2: Manual Deploy Script
```bash
# Set your IP once
export LIGHTSAIL_IP=3.145.XX.XXX

# Deploy
./deploy-helper.sh deploy

# View logs
./deploy-helper.sh logs

# Check status
./deploy-helper.sh status
```

### Option 3: Direct SSH Deploy
```bash
# Quick one-liner from Netherlands
ssh ubuntu@YOUR_IP "cd /path/to/app && git pull && sudo systemctl restart bankconverter"
```

## 🔧 Common Tasks

### View Live Logs
```bash
ssh ubuntu@YOUR_IP "sudo journalctl -u bankconverter -f"
```

### Quick Restart
```bash
ssh ubuntu@YOUR_IP "sudo systemctl restart bankconverter"
```

### Check Failed PDFs
```bash
ssh ubuntu@YOUR_IP "cd bank-statement-converter && python manage_failed_pdfs.py list"
```

## 🚨 Troubleshooting

### Service Won't Start
```bash
# Check error
ssh ubuntu@YOUR_IP "sudo journalctl -u bankconverter -n 50"

# Common fix - reinstall dependencies
ssh ubuntu@YOUR_IP "cd bank-statement-converter && source venv/bin/activate && pip install -r backend/requirements-fastapi.txt"
```

### Can't Connect from Netherlands
- Check Lightsail firewall allows port 22
- Try using IP instead of domain
- Use `-v` flag for verbose SSH: `ssh -v ubuntu@IP`

### Slow SSH Response
Normal latency Netherlands → US: ~100ms
Use VS Code Remote SSH for better experience

## 💡 Pro Tips

1. **Morning Deploys**: Deploy in US morning (3-5 PM Netherlands time) for less traffic
2. **Use GitHub Actions**: Let automation handle deployments while you sleep
3. **Monitor from EU**: Set up UptimeRobot for EU and US monitoring
4. **Static Assets**: Later add CloudFront CDN for faster EU access

## 📊 Monitoring

- Service Status: `http://YOUR_IP/health`
- Failed PDFs: Check `/failed_pdfs/` directory
- Disk Space: `df -h`
- Memory: `free -m`

## 🔐 Security Checklist

- [ ] Change default SSH port (optional)
- [ ] Enable UFW firewall
- [ ] Set up SSL with Let's Encrypt
- [ ] Regular security updates: `sudo apt update && sudo apt upgrade`

## 🆘 Emergency Rollback

If deployment breaks everything:
```bash
ssh ubuntu@YOUR_IP << 'EOF'
  BACKUP=$(ls -td /home/ubuntu/bank-statement-converter.backup.* | head -1)
  sudo systemctl stop bankconverter
  rm -rf /home/ubuntu/bank-statement-converter
  mv $BACKUP /home/ubuntu/bank-statement-converter  
  sudo systemctl start bankconverter
EOF
```