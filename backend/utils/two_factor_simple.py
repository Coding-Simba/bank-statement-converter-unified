"""Simplified two-factor authentication utilities without external dependencies."""

import secrets
import hashlib
import json
import time
import base64
from typing import Tuple, List, Optional


def generate_secret() -> str:
    """Generate a new 2FA secret (simplified)."""
    # Generate a random 16-byte secret
    return base64.b32encode(secrets.token_bytes(16)).decode('utf-8').rstrip('=')


def generate_qr_placeholder(email: str, secret: str, issuer: str = "BankCSV") -> str:
    """Generate a placeholder for QR code (without actual QR generation)."""
    # Return a data URL with instructions
    instructions = f"""
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
        <rect width="200" height="200" fill="white" stroke="black" stroke-width="2"/>
        <text x="100" y="90" text-anchor="middle" font-family="Arial" font-size="14">
            Scan with your
        </text>
        <text x="100" y="110" text-anchor="middle" font-family="Arial" font-size="14">
            authenticator app
        </text>
        <text x="100" y="140" text-anchor="middle" font-family="Arial" font-size="10" fill="#666">
            {issuer}
        </text>
        <text x="100" y="155" text-anchor="middle" font-family="Arial" font-size="10" fill="#666">
            {email[:20]}...
        </text>
    </svg>
    """
    
    # Convert to base64
    svg_base64 = base64.b64encode(instructions.encode()).decode()
    return f"data:image/svg+xml;base64,{svg_base64}"


def simple_totp(secret: str, time_step: int = 30) -> str:
    """Generate a simplified TOTP token (6 digits)."""
    if not secret:
        return "000000"
    
    # Get current time counter
    counter = int(time.time() // time_step)
    
    # Create a simple hash
    data = f"{secret}{counter}"
    hash_result = hashlib.sha256(data.encode()).hexdigest()
    
    # Extract 6 digits
    # Take first 8 hex chars and convert to int, then mod by 1000000
    num = int(hash_result[:8], 16) % 1000000
    
    # Pad with zeros if needed
    return str(num).zfill(6)


def verify_token(secret: str, token: str, window: int = 1) -> bool:
    """Verify a 2FA token (simplified)."""
    if not secret or not token:
        return False
    
    try:
        # Clean token
        token = token.replace(" ", "").strip()
        
        # Check current and adjacent time windows
        current_time = int(time.time())
        time_step = 30
        
        for i in range(-window, window + 1):
            test_time = current_time + (i * time_step)
            counter = int(test_time // time_step)
            
            # Generate token for this time window
            data = f"{secret}{counter}"
            hash_result = hashlib.sha256(data.encode()).hexdigest()
            num = int(hash_result[:8], 16) % 1000000
            expected_token = str(num).zfill(6)
            
            if token == expected_token:
                return True
        
        return False
    except Exception:
        return False


def generate_backup_codes(count: int = 8) -> List[str]:
    """Generate backup codes for 2FA recovery."""
    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric code
        code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
        # Format as XXXX-XXXX
        formatted_code = f"{code[:4]}-{code[4:]}"
        codes.append(formatted_code)
    return codes


def hash_backup_code(code: str) -> str:
    """Hash a backup code for storage."""
    # Remove formatting
    clean_code = code.replace("-", "").upper()
    # Use SHA256 for hashing
    return hashlib.sha256(clean_code.encode()).hexdigest()


def verify_backup_code(input_code: str, hashed_codes: List[str]) -> Tuple[bool, Optional[str]]:
    """Verify a backup code against hashed codes."""
    # Clean input
    clean_code = input_code.replace("-", "").replace(" ", "").upper()
    
    # Hash the input
    input_hash = hashlib.sha256(clean_code.encode()).hexdigest()
    
    # Check against stored hashes
    for stored_hash in hashed_codes:
        if input_hash == stored_hash:
            return True, stored_hash
    
    return False, None


def format_secret_for_display(secret: str) -> str:
    """Format secret for manual entry (spaces every 4 characters)."""
    # Add spaces every 4 characters for readability
    return ' '.join([secret[i:i+4] for i in range(0, len(secret), 4)])


def get_current_token(secret: str) -> str:
    """Get the current TOTP token (for testing)."""
    return simple_totp(secret)


def get_remaining_seconds() -> int:
    """Get remaining seconds for current TOTP period."""
    return 30 - int(time.time() % 30)


def generate_provisioning_uri(email: str, secret: str, issuer: str = "BankCSV") -> str:
    """Generate otpauth:// URI for manual entry."""
    # Format: otpauth://totp/ISSUER:EMAIL?secret=SECRET&issuer=ISSUER
    return f"otpauth://totp/{issuer}:{email}?secret={secret}&issuer={issuer}"