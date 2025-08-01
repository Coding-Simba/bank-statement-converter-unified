"""Two-factor authentication utilities."""

import pyotp
import qrcode
import io
import base64
import secrets
from typing import List, Tuple, Optional


def generate_secret() -> str:
    """Generate a new TOTP secret."""
    return pyotp.random_base32()


def generate_qr_code(email: str, secret: str, issuer: str = "BankCSV") -> str:
    """Generate a QR code for 2FA setup.
    
    Returns base64 encoded PNG image.
    """
    # Create provisioning URI
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
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
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def verify_token(secret: str, token: str, window: int = 1) -> bool:
    """Verify a TOTP token.
    
    Args:
        secret: The user's TOTP secret
        token: The 6-digit token to verify
        window: Number of time windows to check (for clock drift)
    
    Returns:
        True if token is valid, False otherwise
    """
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=window)
    except Exception:
        return False


def generate_backup_codes(count: int = 10) -> List[str]:
    """Generate backup codes for 2FA.
    
    Args:
        count: Number of backup codes to generate
    
    Returns:
        List of backup codes
    """
    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric codes
        code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
        # Format as XXXX-XXXX for readability
        formatted_code = f"{code[:4]}-{code[4:]}"
        codes.append(formatted_code)
    
    return codes


def hash_backup_code(code: str) -> str:
    """Hash a backup code for storage.
    
    We store hashed versions to prevent exposure if database is compromised.
    """
    import hashlib
    # Remove formatting
    clean_code = code.replace('-', '')
    # Simple hash for backup codes (not as critical as passwords)
    return hashlib.sha256(clean_code.encode()).hexdigest()


def verify_backup_code(code: str, hashed_codes: List[str]) -> Tuple[bool, Optional[str]]:
    """Verify a backup code against a list of hashed codes.
    
    Args:
        code: The backup code to verify
        hashed_codes: List of hashed backup codes
    
    Returns:
        Tuple of (is_valid, matched_hash)
    """
    hashed_input = hash_backup_code(code)
    
    for hashed_code in hashed_codes:
        if hashed_input == hashed_code:
            return True, hashed_code
    
    return False, None


def format_secret_for_display(secret: str) -> str:
    """Format secret for manual entry display.
    
    Breaks the secret into groups of 4 characters for easier reading.
    """
    # Group every 4 characters
    groups = [secret[i:i+4] for i in range(0, len(secret), 4)]
    return ' '.join(groups)