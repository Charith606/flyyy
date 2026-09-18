import pytest
from app.protection.fpe import encrypt_phone_fpe, decrypt_phone_fpe, encrypt_alphanumeric_fpe, decrypt_alphanumeric_fpe
from app.protection.tokenizer import generate_deterministic_token

def test_phone_fpe_preserves_length_and_charset():
    original_phone = "9876543210"
    encrypted_phone = encrypt_phone_fpe(original_phone)
    
    # 1. Output must be string of digits
    assert encrypted_phone.isdigit()
    # 2. Output must have identical 10-digit length
    assert len(encrypted_phone) == 10
    # 3. Output must not match plaintext
    assert encrypted_phone != original_phone
    # 4. Decryption must recover original phone
    decrypted_phone = decrypt_phone_fpe(encrypted_phone)
    assert decrypted_phone == original_phone

def test_fpe_determinism():
    phone = "9123456780"
    enc1 = encrypt_phone_fpe(phone)
    enc2 = encrypt_phone_fpe(phone)
    assert enc1 == enc2, "FPE encryption must be deterministic for join stability"

def test_alphanumeric_fpe():
    code = "AB12CD34"
    enc = encrypt_alphanumeric_fpe(code, length=8)
    assert len(enc) == 8
    assert enc.isalnum()
    assert enc != code
    dec = decrypt_alphanumeric_fpe(enc, length=8)
    assert dec == code

def test_deterministic_tokenization():
    email = "john@example.com"
    token1 = generate_deterministic_token("EMAIL", email)
    token2 = generate_deterministic_token("EMAIL", email)
    assert token1 == token2
    assert token1.startswith("EMAIL_")
