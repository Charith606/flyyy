import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db.models import VaultMapping
from app.protection.tokenizer import generate_deterministic_token
from app.protection.fpe import encrypt_phone_fpe

settings = get_settings()

def _get_aes_gcm_key() -> bytes:
    raw_key = settings.VAULT_AES_KEY
    try:
        # Try hex decode if 64 chars
        if len(raw_key) == 64:
            return bytes.fromhex(raw_key)
        # Try base64
        return base64.b64decode(raw_key)[:32].ljust(32, b'0')
    except Exception:
        # Fallback to UTF-8 padded
        return raw_key.encode('utf-8')[:32].ljust(32, b'0')

def encrypt_vault_payload(plaintext: str) -> str:
    """
    Encrypts a plaintext string using AES-256-GCM.
    Returns standard Base64 string containing: 12-byte Nonce + Ciphertext (with 16-byte Auth Tag).
    """
    if not plaintext:
        return ""
    key = _get_aes_gcm_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    payload = nonce + ciphertext
    return base64.b64encode(payload).decode('utf-8')

def decrypt_vault_payload(encrypted_b64: str) -> str:
    """
    Decrypts an AES-256-GCM payload.
    """
    if not encrypted_b64:
        return ""
    key = _get_aes_gcm_key()
    aesgcm = AESGCM(key)
    raw = base64.b64decode(encrypted_b64.encode('utf-8'))
    nonce = raw[:12]
    ciphertext = raw[12:]
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted_bytes.decode('utf-8')

def store_vault_mapping(db: Session, token_or_cipher: str, field_type: str, plaintext: str) -> VaultMapping:
    """
    Safely stores the encrypted mapping in the vault table.
    """
    existing = db.query(VaultMapping).filter(VaultMapping.token_or_cipher == token_or_cipher).first()
    if existing:
        return existing
    
    encrypted_blob = encrypt_vault_payload(plaintext)
    mapping = VaultMapping(
        token_or_cipher=token_or_cipher,
        field_type=field_type,
        encrypted_plaintext=encrypted_blob,
        key_reference="aes_gcm_v1"
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return mapping

def resolve_vault_mapping(db: Session, token_or_cipher: str) -> str | None:
    """
    Resolves token or FPE cipher to its decrypted plaintext value.
    """
    mapping = db.query(VaultMapping).filter(VaultMapping.token_or_cipher == token_or_cipher).first()
    if not mapping:
        return None
    return decrypt_vault_payload(mapping.encrypted_plaintext)

def reverse_lookup_vault_by_plaintext(db: Session, field_type: str, plaintext: str) -> str | None:
    """
    Finds the protected token or cipher corresponding to a given plaintext value.
    Computes the deterministic token or FPE cipher directly and queries the vault.
    """
    if field_type == "EMAIL":
        token = generate_deterministic_token("EMAIL", plaintext)
        mapping = db.query(VaultMapping).filter(VaultMapping.token_or_cipher == token).first()
        if mapping:
            return token
    elif field_type == "MOBILE":
        cipher = encrypt_phone_fpe(plaintext)
        mapping = db.query(VaultMapping).filter(VaultMapping.token_or_cipher == cipher).first()
        if mapping:
            return cipher
    elif field_type == "NAME":
        token = generate_deterministic_token("NAME", plaintext)
        mapping = db.query(VaultMapping).filter(VaultMapping.token_or_cipher == token).first()
        if mapping:
            return token

    # Fallback linear search if necessary
    mappings = db.query(VaultMapping).filter(VaultMapping.field_type == field_type).all()
    for m in mappings:
        try:
            decrypted = decrypt_vault_payload(m.encrypted_plaintext)
            if decrypted.strip().lower() == plaintext.strip().lower():
                return m.token_or_cipher
        except Exception:
            continue
    return None
