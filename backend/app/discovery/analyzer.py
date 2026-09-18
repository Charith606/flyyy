import re
from typing import List, Dict, Any

# Regex patterns for fast, reliable PII pattern recognition
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
PHONE_REGEX = re.compile(r'^\+?[0-9\s\-\(\)]{7,15}$')
PHONE_10_DIGIT_REGEX = re.compile(r'^[6-9]\d{9}$') # Standard 10-digit mobile
NAME_REGEX = re.compile(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)+$')

presidio_engine = None
# Safe presidio initialization without automatic subprocess pip install
try:
    import spacy
    if spacy.util.is_package("en_core_web_sm"):
        from presidio_analyzer import AnalyzerEngine
        presidio_engine = AnalyzerEngine()
except Exception:
    presidio_engine = None

def discover_field_pii(field_name: str, sample_values: List[Any]) -> Dict[str, Any]:
    """
    Analyzes a column name and sample values to discover PII entity type and confidence.
    """
    name_lower = field_name.lower().strip()
    str_samples = [str(v).strip() for v in sample_values if v is not None and str(v).strip() != ""]
    
    if not str_samples:
        return {
            "field_name": field_name,
            "entity_type": "UNKNOWN",
            "confidence": 0.0,
            "recommended_action": "KEEP_PLAINTEXT",
            "sample_count": 0
        }
    
    total = len(str_samples)
    
    # 1. Email Detection
    email_matches = sum(1 for v in str_samples if EMAIL_REGEX.match(v) or "@" in v)
    if "email" in name_lower or (email_matches / total) > 0.5:
        confidence = 0.99 if "email" in name_lower and (email_matches / total) > 0.5 else 0.85
        return {
            "field_name": field_name,
            "entity_type": "EMAIL_ADDRESS",
            "confidence": confidence,
            "recommended_action": "TOKENIZATION",
            "sample_count": total
        }
    
    # 2. Phone / Mobile Detection
    digits_matches = sum(1 for v in str_samples if len(re.sub(r'\D', '', v)) in [10, 11, 12])
    phone_name_matches = any(k in name_lower for k in ["phone", "mobile", "contact", "cell", "tel"])
    if phone_name_matches or (digits_matches / total) > 0.5:
        confidence = 0.98 if phone_name_matches and (digits_matches / total) > 0.5 else 0.88
        return {
            "field_name": field_name,
            "entity_type": "PHONE_NUMBER",
            "confidence": confidence,
            "recommended_action": "FPE",
            "sample_count": total
        }
        
    # 3. Name Detection
    name_column_matches = any(k in name_lower for k in ["name", "full_name", "first_name", "last_name", "customer_name"])
    name_regex_matches = sum(1 for v in str_samples if len(v.split()) >= 2 and all(part.isalpha() for part in v.split()))
    if name_column_matches or (name_regex_matches / total) > 0.4:
        confidence = 0.95 if name_column_matches else 0.75
        return {
            "field_name": field_name,
            "entity_type": "PERSON_NAME",
            "confidence": confidence,
            "recommended_action": "TOKENIZATION",
            "sample_count": total
        }

    # 4. Identifier / Code
    id_matches = any(k in name_lower for k in ["id", "identifier", "code", "cust_id"])
    if id_matches:
        return {
            "field_name": field_name,
            "entity_type": "CUSTOMER_IDENTIFIER",
            "confidence": 0.90,
            "recommended_action": "KEEP_PLAINTEXT",
            "sample_count": total
        }
        
    # Default non-PII / categorical
    return {
        "field_name": field_name,
        "entity_type": "CATEGORICAL_ATTRIBUTE",
        "confidence": 0.10,
        "recommended_action": "KEEP_PLAINTEXT",
        "sample_count": total
    }

def discover_dataset(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Runs PII discovery over a list of records (dictionary rows).
    """
    if not records:
        return []
    
    fields = list(records[0].keys())
    results = []
    
    for f in fields:
        samples = [r.get(f) for r in records[:50]]
        discovery = discover_field_pii(f, samples)
        results.append(discovery)
        
    return results
