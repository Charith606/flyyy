from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime
from app.db.session import get_db
from app.db.models import ProtectionPolicy

policy_router = APIRouter(prefix="/policies", tags=["Protection Policies"])

class PolicyUpdateSchema(BaseModel):
    field_name: str
    protection_type: str # "FPE", "TOKENIZATION", "DYNAMIC_MASKING", "KEEP_PLAINTEXT"
    is_active: bool = True

@policy_router.get("")
def get_policies(db: Session = Depends(get_db)):
    from app.batch.pipeline import get_or_create_default_policies
    get_or_create_default_policies(db)
    policies = db.query(ProtectionPolicy).all()
    return policies

@policy_router.post("")
def update_policy(payload: PolicyUpdateSchema, db: Session = Depends(get_db)):
    policy = db.query(ProtectionPolicy).filter(ProtectionPolicy.field_name == payload.field_name).first()
    if not policy:
        policy = ProtectionPolicy(
            field_name=payload.field_name,
            entity_type="CUSTOM",
            protection_type=payload.protection_type,
            is_active=payload.is_active
        )
        db.add(policy)
    else:
        policy.protection_type = payload.protection_type
        policy.is_active = payload.is_active
        policy.updated_at = datetime.utcnow()
        
    db.commit()
    db.refresh(policy)
    return policy
