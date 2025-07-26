#!/bin/bash
# Deploy to Railway.app - Super simple deployment

# Install Railway CLI
# npm install -g @railway/cli

# Create railway.json
cat > railway.json << EOF
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn backend.main:app --host 0.0.0.0 --port \$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF

# Create Procfile
cat > Procfile << EOF
web: uvicorn backend.main:app --host 0.0.0.0 --port \$PORT
EOF

# Create nixpacks.toml
cat > nixpacks.toml << EOF
[phases.setup]
nixPkgs = ["python310", "gcc", "tesseract", "poppler-utils"]

[phases.install]
cmds = ["pip install -r backend/requirements-fastapi.txt", "pip install -r requirements-ocr.txt"]

[start]
cmd = "uvicorn backend.main:app --host 0.0.0.0 --port \$PORT"
EOF

echo "Ready to deploy!"
echo "Run: railway login"
echo "Then: railway up"