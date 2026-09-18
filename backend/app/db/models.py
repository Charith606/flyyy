from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from app.db.session import Base

class SourceCustomer(Base):
    __tablename__ = "source_customers"
    
    customer_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    mobile = Column(String(50), nullable=False)
    city = Column(String(100), nullable=True)
    segment = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProtectedCustomer(Base):
    __tablename__ = "protected_customers"
    
    customer_id = Column(String(50), primary_key=True, index=True)
    name_token = Column(String(100), nullable=False, index=True)
    email_token = Column(String(100), nullable=False, index=True)
    mobile_fpe = Column(String(50), nullable=False, index=True)
    city = Column(String(100), nullable=True)
    segment = Column(String(50), nullable=True)
    batch_id = Column(String(100), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VaultMapping(Base):
    __tablename__ = "vault_mappings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_or_cipher = Column(String(150), unique=True, index=True, nullable=False)
    field_type = Column(String(50), nullable=False) # "EMAIL", "NAME", "MOBILE"
    encrypted_plaintext = Column(Text, nullable=False) # Base64 encoded nonce+ciphertext+tag
    key_reference = Column(String(50), default="default_v1")
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    subject_id = Column(String(100), nullable=True, index=True)
    field = Column(String(50), nullable=True)
    purpose = Column(String(100), nullable=True)
    reference_id = Column(String(100), nullable=True)
    outcome = Column(String(50), nullable=False, index=True) # "ALLOWED", "ACCESS_DENIED"
    ip_address = Column(String(50), default="127.0.0.1")
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class BatchRun(Base):
    __tablename__ = "batch_runs"
    
    batch_id = Column(String(100), primary_key=True, index=True)
    source = Column(String(100), nullable=False)
    status = Column(String(50), default="PENDING") # PENDING, RUNNING, COMPLETED, FAILED
    row_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    error_details = Column(Text, nullable=True)

class ProtectionPolicy(Base):
    __tablename__ = "protection_policies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    field_name = Column(String(100), unique=True, nullable=False)
    entity_type = Column(String(100), nullable=False)
    protection_type = Column(String(50), nullable=False) # "FPE", "TOKENIZATION", "DYNAMIC_MASKING", "KEEP_PLAINTEXT"
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
