import uuid
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.db.models import SourceCustomer, ProtectedCustomer, BatchRun, ProtectionPolicy, AuditLog
from app.protection.fpe import encrypt_phone_fpe
from app.protection.tokenizer import generate_deterministic_token
from app.protection.vault import store_vault_mapping

def get_or_create_default_policies(db: Session) -> Dict[str, str]:
    """
    Returns mapping of field_name -> protection_type.
    """
    policies = db.query(ProtectionPolicy).filter(ProtectionPolicy.is_active == True).all()
    if not policies:
        default_defs = [
            ("name", "PERSON_NAME", "TOKENIZATION"),
            ("email", "EMAIL_ADDRESS", "TOKENIZATION"),
            ("mobile", "PHONE_NUMBER", "FPE"),
            ("city", "LOCATION", "KEEP_PLAINTEXT"),
            ("segment", "CATEGORICAL", "KEEP_PLAINTEXT"),
        ]
        for fname, etype, ptype in default_defs:
            p = ProtectionPolicy(field_name=fname, entity_type=etype, protection_type=ptype, is_active=True)
            db.add(p)
        db.commit()
        policies = db.query(ProtectionPolicy).filter(ProtectionPolicy.is_active == True).all()
        
    return {p.field_name.lower(): p.protection_type for p in policies}

def run_batch_protection_job(db: Session, source_name: str = "source_customers", batch_size: int = 1000) -> BatchRun:
    """
    Executes a chunked, idempotent batch protection run.
    Transforms raw customer data into protected records and encrypts mappings into the secure vault.
    """
    batch_id = f"BATCH_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:8].upper()}"
    
    batch_run = BatchRun(
        batch_id=batch_id,
        source=source_name,
        status="RUNNING",
        start_time=datetime.utcnow(),
        row_count=0,
        success_count=0,
        error_count=0
    )
    db.add(batch_run)
    db.commit()
    
    policies = get_or_create_default_policies(db)
    
    try:
        # Read source customers in chunks
        offset = 0
        total_processed = 0
        success_count = 0
        error_count = 0
        
        while True:
            chunk = db.query(SourceCustomer).offset(offset).limit(batch_size).all()
            if not chunk:
                break
                
            for customer in chunk:
                total_processed += 1
                try:
                    # 1. Transform Name
                    name_policy = policies.get("name", "TOKENIZATION")
                    if name_policy == "TOKENIZATION":
                        name_token = generate_deterministic_token("NAME", customer.name)
                        store_vault_mapping(db, name_token, "NAME", customer.name)
                    else:
                        name_token = customer.name
                        
                    # 2. Transform Email
                    email_policy = policies.get("email", "TOKENIZATION")
                    if email_policy == "TOKENIZATION":
                        email_token = generate_deterministic_token("EMAIL", customer.email)
                        store_vault_mapping(db, email_token, "EMAIL", customer.email)
                    else:
                        email_token = customer.email
                        
                    # 3. Transform Mobile (FPE)
                    mobile_policy = policies.get("mobile", "FPE")
                    if mobile_policy == "FPE":
                        mobile_fpe = encrypt_phone_fpe(customer.mobile)
                        store_vault_mapping(db, mobile_fpe, "MOBILE", customer.mobile)
                    else:
                        mobile_fpe = customer.mobile
                        
                    # 4. Idempotent Upsert into ProtectedCustomer
                    existing_prot = db.query(ProtectedCustomer).filter(ProtectedCustomer.customer_id == customer.customer_id).first()
                    if existing_prot:
                        existing_prot.name_token = name_token
                        existing_prot.email_token = email_token
                        existing_prot.mobile_fpe = mobile_fpe
                        existing_prot.city = customer.city
                        existing_prot.segment = customer.segment
                        existing_prot.batch_id = batch_id
                        existing_prot.updated_at = datetime.utcnow()
                    else:
                        new_prot = ProtectedCustomer(
                            customer_id=customer.customer_id,
                            name_token=name_token,
                            email_token=email_token,
                            mobile_fpe=mobile_fpe,
                            city=customer.city,
                            segment=customer.segment,
                            batch_id=batch_id
                        )
                        db.add(new_prot)
                    
                    success_count += 1
                except Exception as row_err:
                    error_count += 1
                    # Note: Do not log plaintext values in error logs
                    print(f"[BATCH ERROR] Failed to process customer_id: {customer.customer_id}. Error: {str(row_err)}")
                    
            db.commit()
            offset += batch_size

        batch_run.row_count = total_processed
        batch_run.success_count = success_count
        batch_run.error_count = error_count
        batch_run.status = "COMPLETED"
        batch_run.end_time = datetime.utcnow()
        
        # Log to audit trail
        audit_event = AuditLog(
            actor="batch_pipeline_worker",
            action="BATCH_PROTECTION_JOB",
            subject_id=batch_id,
            field="DATASET",
            purpose="SCHEDULED_BATCH_PROTECTION",
            reference_id=batch_id,
            outcome="ALLOWED",
            details=f"Processed {total_processed} rows (Success: {success_count}, Errors: {error_count})"
        )
        db.add(audit_event)
        db.commit()
        
    except Exception as e:
        db.rollback()
        batch_run.status = "FAILED"
        batch_run.end_time = datetime.utcnow()
        batch_run.error_details = str(e)
        db.commit()
        
    return batch_run
