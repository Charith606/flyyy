import re

def mask_email(email_str: str) -> str:
    """Mask email for display: e.g. john.smith@example.com -> j***h@example.com"""
    if not email_str or "@" not in email_str:
        return email_str
    
    parts = email_str.split("@")
    user = parts[0]
    domain = parts[1]
    
    if len(user) <= 2:
        masked_user = user[0] + "*"
    else:
        masked_user = user[0] + "*" * (len(user) - 2) + user[-1]
        
    return f"{masked_user}@{domain}"

def mask_phone(phone_str: str) -> str:
    """Mask phone for display: e.g. 9876543210 -> 987****210"""
    digits = re.sub(r'\D', '', str(phone_str))
    if len(digits) <= 4:
        return digits
    return digits[:3] + "*" * (len(digits) - 5) + digits[-2:]

def mask_name(name_str: str) -> str:
    """Mask name for display: e.g. John Smith -> J*** S***"""
    if not name_str:
        return name_str
    words = name_str.split()
    masked_words = []
    for w in words:
        if len(w) <= 1:
            masked_words.append(w)
        else:
            masked_words.append(w[0] + "*" * (len(w) - 1))
    return " ".join(masked_words)
