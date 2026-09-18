import hmac
import hashlib
import base64
from app.config import get_settings

settings = get_settings()

def generate_deterministic_token(field_prefix: str, value: str, token_length: int = 6) -> str:
    """
    Generates a deterministic token using HMAC-SHA256:
    Example: field_prefix='EMAIL', value='john@example.com' -> 'EMAIL_P91QZ8'
    The same input value always produces the exact same token under the configured secret salt.
    """
    if not value:
        return ""
        
    normalized_val = str(value).strip().lower()
    secret = settings.TOKEN_SECRET_SALT.encode('utf-8')
    digest = hmac.new(secret, normalized_val.encode('utf-8'), hashlib.sha256).digest()
    
    # Encode with base32 (uppercase letters and digits 2-7) to get clean readable tokens like P91QZ8
    b32 = base64.b32encode(digest).decode('utf-8').replace('=', '')
    token_suffix = b32[:token_length]
    
    prefix = field_prefix.upper().strip('_')
    return f"{prefix}_{token_suffix}"
