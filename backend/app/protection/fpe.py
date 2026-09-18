import re
import pyffx
from app.config import get_settings

settings = get_settings()

def get_fpe_key_bytes() -> bytes:
    # Key should be at least 16 bytes.
    raw_key = settings.FPE_KEY.encode('utf-8')
    if len(raw_key) < 16:
        raw_key = raw_key.ljust(16, b'0')
    return raw_key[:32]

def encrypt_phone_fpe(phone_str: str) -> str:
    """
    Encrypts a 10-digit phone number into another 10-digit number preserving exact length and numeric charset.
    If phone has special formatting or standard length, sanitizes to digits.
    """
    digits_only = re.sub(r'\D', '', str(phone_str))
    if len(digits_only) < 4:
        # FPE requires minimum length for security (typically >= 4 characters)
        return digits_only
    
    length = len(digits_only)
    cipher = pyffx.String(get_fpe_key_bytes(), alphabet='0123456789', length=length)
    encrypted_digits = cipher.encrypt(digits_only)
    return encrypted_digits

def decrypt_phone_fpe(encrypted_phone: str) -> str:
    """
    Decrypts an FPE-encrypted phone number back to original numeric digits.
    """
    digits_only = re.sub(r'\D', '', str(encrypted_phone))
    if len(digits_only) < 4:
        return digits_only
    
    length = len(digits_only)
    cipher = pyffx.String(get_fpe_key_bytes(), alphabet='0123456789', length=length)
    decrypted_digits = cipher.decrypt(digits_only)
    return decrypted_digits

def encrypt_alphanumeric_fpe(code_str: str, length: int = 8) -> str:
    """
    Encrypts fixed-length uppercase alphanumeric code (e.g. AB12CD34).
    """
    cleaned = re.sub(r'[^A-Z0-9]', '', str(code_str).upper())
    if len(cleaned) != length:
        cleaned = cleaned[:length].ljust(length, '0')
    
    cipher = pyffx.String(
        get_fpe_key_bytes(),
        alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        length=length
    )
    return cipher.encrypt(cleaned)

def decrypt_alphanumeric_fpe(encrypted_code: str, length: int = 8) -> str:
    cleaned = re.sub(r'[^A-Z0-9]', '', str(encrypted_code).upper())
    if len(cleaned) != length:
        cleaned = cleaned[:length].ljust(length, '0')
        
    cipher = pyffx.String(
        get_fpe_key_bytes(),
        alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        length=length
    )
    return cipher.decrypt(cleaned)
