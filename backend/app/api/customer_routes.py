from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models import ProtectedCustomer, SourceCustomer
from app.protection.masking import mask_email, mask_phone, mask_name

customer_router = APIRouter(tags=["Customers"])

@customer_router.get("/customers")
def get_protected_customers(
    limit: int = 50,
    offset: int = 0,
    apply_ui_masking: bool = False,
    db: Session = Depends(get_db)
):
    """
    Returns customer records strictly from the protected database.
    Optionally applies dynamic UI masking for display.
    """
    customers = db.query(ProtectedCustomer).offset(offset).limit(limit).all()
    total = db.query(ProtectedCustomer).count()
    
    results = []
    for c in customers:
        mobile_display = mask_phone(c.mobile_fpe) if apply_ui_masking else c.mobile_fpe
        results.append({
            "customer_id": c.customer_id,
            "name_token": c.name_token,
            "email_token": c.email_token,
            "mobile_fpe": mobile_display,
            "city": c.city,
            "segment": c.segment,
            "batch_id": c.batch_id
        })
        
    return {
        "total": total,
        "items": results
    }

@customer_router.get("/customers/{customer_id}")
def get_single_protected_customer(customer_id: str, db: Session = Depends(get_db)):
    c = db.query(ProtectedCustomer).filter(ProtectedCustomer.customer_id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found in protected database")
    return {
        "customer_id": c.customer_id,
        "name_token": c.name_token,
        "email_token": c.email_token,
        "mobile_fpe": c.mobile_fpe,
        "city": c.city,
        "segment": c.segment,
        "batch_id": c.batch_id
    }

@customer_router.get("/source-customers")
def get_source_customers(limit: int = 20, db: Session = Depends(get_db)):
    """
    Used only in admin/discovery view to illustrate the original raw dataset before protection.
    """
    customers = db.query(SourceCustomer).limit(limit).all()
    total = db.query(SourceCustomer).count()
    return {
        "total": total,
        "items": [
            {
                "customer_id": c.customer_id,
                "name": c.name,
                "email": c.email,
                "mobile": c.mobile,
                "city": c.city,
                "segment": c.segment
            }
            for c in customers
        ]
    }
