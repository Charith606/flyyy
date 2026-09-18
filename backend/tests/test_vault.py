import pytest
from app.protection.vault import encrypt_vault_payload, decrypt_vault_payload

def test_vault_aes_gcm_roundtrip():
    plaintext = "confidential_customer_data@flyyy.ai"
    encrypted = encrypt_vault_payload(plaintext)
    
    assert encrypted != plaintext
    assert len(encrypted) > 20
    
    decrypted = decrypt_vault_payload(encrypted)
    assert decrypted == plaintext

def test_vault_tamper_resistance():
    plaintext = "sensitive_phone_number_9876543210"
    encrypted = encrypt_vault_payload(plaintext)
    
    # Tamper with the base64 string
    tampered = encrypted[:-4] + "AAAA"
    with pytest.raises(Exception):
        decrypt_vault_payload(tampered)
