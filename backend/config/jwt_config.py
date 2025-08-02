"""JWT Configuration - Single source of truth for JWT settings"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# JWT Configuration - single source of truth
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-here-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 90

# Log the configuration once
print(f"JWT Config loaded with SECRET_KEY: {JWT_SECRET_KEY[:20]}... (first 20 chars)")