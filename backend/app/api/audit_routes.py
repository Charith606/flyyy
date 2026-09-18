from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.db.models import AuditLog

audit_router = APIRouter(prefix="/audit", tags=["Audit & Compliance"])

@audit_router.get("")
def get_audit_logs(
    limit: int = 50,
    offset: int = 0,
    outcome: Optional[str] = Query(None, description="Filter by ALLOWED or ACCESS_DENIED"),
    actor: Optional[str] = Query(None, description="Filter by actor name"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    db: Session = Depends(get_db)
):
    """
    Returns immutable audit logs tracking all sensitive actions, reveals, and batch operations.
    """
    query = db.query(AuditLog)
    
    if outcome:
        query = query.filter(AuditLog.outcome == outcome.upper())
    if actor:
        query = query.filter(AuditLog.actor.ilike(f"%{actor}%"))
    if action:
        query = query.filter(AuditLog.action == action.upper())
        
    total = query.count()
    logs = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "items": [
            {
                "id": l.id,
                "actor": l.actor,
                "action": l.action,
                "subject_id": l.subject_id,
                "field": l.field,
                "purpose": l.purpose,
                "reference_id": l.reference_id,
                "outcome": l.outcome,
                "ip_address": l.ip_address,
                "details": l.details,
                "timestamp": l.timestamp
            }
            for l in logs
        ]
    }
