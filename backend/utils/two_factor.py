"""Two-factor authentication utilities."""

import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
from typing import Tuple, List, Optional


def generate_secret() -> str:
    """Generate a new 2FA secret."""
    return pyotp.random_base32()


def generate_qr_code(email: str, secret: str, issuer: str = "BankCSV") -> str:
    """Generate QR code for 2FA setup."""
    # Create provisioning URI
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=issuer
    )
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"


def verify_token(secret: str, token: str, window: int = 1) -> bool:
    """Verify a 2FA token."""
    if not secret or not token:
        return False
    
    try:
        # Clean token (remove spaces)
        token = token.replace(" ", "").strip()
        
        # Create TOTP instance
        totp = pyotp.TOTP(secret)
        
        # Verify with time window
        return totp.verify(token, valid_window=window)
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
    if not secret:
        return ""
    
    totp = pyotp.TOTP(secret)
    return totp.now()


def get_remaining_seconds() -> int:
    """Get remaining seconds for current TOTP period."""
    import time
    return 30 - int(time.time() % 30)