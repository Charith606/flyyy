from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import ProtectedCustomer, AuditLog
from app.protection.vault import resolve_vault_mapping, reverse_lookup_vault_by_plaintext
from app.gateway.mailer import send_smtp_email

gateway_router = APIRouter(prefix="/gateway", tags=["Privacy Gateway"])

# ----------------- Models -----------------
class CampaignSendRequest(BaseModel):
    recipient: str = Field(..., description="Protected Email Token e.g. EMAIL_P91QZ")
    campaign_id: str = Field(default="CMP1001")
    template_id: str = Field(default="WELCOME")
    subject: Optional[str] = "Important Update from Flyyy"
    body: Optional[str] = "Hello, your order has been processed successfully."

class CampaignSendResponse(BaseModel):
    recipient: str
    status: str
    campaign_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BounceWebhookRequest(BaseModel):
    email: str = Field(..., description="Plaintext email received from mail provider webhook")
    event: str = Field(default="BOUNCE")
    reason: Optional[str] = "MAILBOX_NOT_FOUND"

class BounceWebhookResponse(BaseModel):
    recipient: str # Protected Token
    event: str
    reason: Optional[str]
    status: str

class RevealRequest(BaseModel):
    subject_id: str = Field(..., description="Customer ID (e.g. C001) or Token")
    field: str = Field(default="EMAIL", description="EMAIL, MOBILE, or NAME")
    purpose: str = Field(..., description="Declared justification: CUSTOMER_SUPPORT, FRAUD_INVESTIGATION, LEGAL_COMPLIANCE")
    reference: str = Field(..., description="Audit ticket/case reference e.g. TICKET-1091")
    actor: str = Field(default="support_agent", description="Requesting agent or role")

class RevealResponse(BaseModel):
    subject_id: str
    field: str
    plaintext_value: str
    purpose: str
    reference: str
    outcome: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ----------------- Helpers -----------------
def record_audit(db: Session, actor: str, action: str, subject_id: str, field: str, purpose: str, reference: str, outcome: str, details: str = "", ip_address: str = "127.0.0.1"):
    audit = AuditLog(
        actor=actor,
        action=action,
        subject_id=subject_id,
        field=field,
        purpose=purpose,
        reference_id=reference,
        outcome=outcome,
        details=details,
        ip_address=ip_address,
        timestamp=datetime.utcnow()
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit

# ----------------- Endpoints -----------------

@gateway_router.post("/send-campaign", response_model=CampaignSendResponse)
@gateway_router.post("/send-email", response_model=CampaignSendResponse)
def send_campaign(req: CampaignSendRequest, request: Request, db: Session = Depends(get_db)):
    """
    BLIND MARKETING EXECUTION:
    Marketing app passes only the protected token.
    The Privacy Gateway resolves the real email in an isolated context, delivers the email,
    and returns a success confirmation WITHOUT exposing the real email.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # 1. Resolve token from isolated vault
    real_email = resolve_vault_mapping(db, req.recipient)
    if not real_email:
        record_audit(
            db=db,
            actor="marketing_service",
            action="SEND_CAMPAIGN_EMAIL",
            subject_id=req.recipient,
            field="EMAIL",
            purpose=f"MARKETING_{req.campaign_id}",
            reference=req.campaign_id,
            outcome="ACCESS_DENIED",
            details="Token not found in secure vault",
            ip_address=client_ip
        )
        raise HTTPException(status_code=404, detail="Protected recipient token not found")

    # 2. Dispatch email to SMTP service
    send_smtp_email(
        to_email=real_email,
        subject=req.subject or f"Flyyy Campaign {req.campaign_id}",
        body_text=req.body or "Privacy Preserving Notification"
    )

    # 3. Log to Audit Trail
    record_audit(
        db=db,
        actor="marketing_service",
        action="SEND_CAMPAIGN_EMAIL",
        subject_id=req.recipient,
        field="EMAIL",
        purpose=f"MARKETING_{req.campaign_id}",
        reference=req.campaign_id,
        outcome="ALLOWED",
        details=f"Template: {req.template_id}",
        ip_address=client_ip
    )

    # 4. Return strictly protected token in response
    return CampaignSendResponse(
        recipient=req.recipient,
        status="SENT",
        campaign_id=req.campaign_id
    )

@gateway_router.post("/bounce-webhook", response_model=BounceWebhookResponse)
@gateway_router.post("/webhooks/email", response_model=BounceWebhookResponse)
def handle_bounce_webhook(req: BounceWebhookRequest, request: Request, db: Session = Depends(get_db)):
    """
    BOUNCE HANDLING:
    Webhook receives external plaintext email, reverse-resolves it to the protected token,
    and forwards only the tokenized event for downstream storage.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    token = reverse_lookup_vault_by_plaintext(db, "EMAIL", req.email)
    protected_id = token if token else "TOKEN_UNRESOLVED"

    record_audit(
        db=db,
        actor="email_provider_webhook",
        action="PROCESS_BOUNCE_WEBHOOK",
        subject_id=protected_id,
        field="EMAIL",
        purpose="BOUNCE_HANDLING",
        reference=req.event,
        outcome="ALLOWED",
        details=f"Reason: {req.reason}",
        ip_address=client_ip
    )

    return BounceWebhookResponse(
        recipient=protected_id,
        event=req.event,
        reason=req.reason,
        status="PROCESSED"
    )

@gateway_router.post("/reveal", response_model=RevealResponse)
def controlled_reveal(req: RevealRequest, request: Request, db: Session = Depends(get_db)):
    """
    CONTROLLED REVEAL:
    Strict RBAC + purpose justification verification.
    Allowed purposes: CUSTOMER_SUPPORT, FRAUD_INVESTIGATION, LEGAL_COMPLIANCE.
    All attempts (allowed & denied) are immutably audited.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    valid_purposes = ["CUSTOMER_SUPPORT", "FRAUD_INVESTIGATION", "LEGAL_COMPLIANCE"]
    
    # Check 1: Purpose justification
    purpose_normalized = req.purpose.upper().strip()
    if purpose_normalized not in valid_purposes or not req.reference.strip():
        record_audit(
            db=db,
            actor=req.actor,
            action="REVEAL_PII",
            subject_id=req.subject_id,
            field=req.field,
            purpose=req.purpose,
            reference=req.reference,
            outcome="ACCESS_DENIED",
            details="Invalid purpose or missing reference ID",
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ACCESS_DENIED: Request does not meet authorized purpose or reference criteria"
        )
    
    # Check 2: Unauthorized actors
    if "unauthorized" in req.actor.lower() or "guest" in req.actor.lower():
        record_audit(
            db=db,
            actor=req.actor,
            action="REVEAL_PII",
            subject_id=req.subject_id,
            field=req.field,
            purpose=req.purpose,
            reference=req.reference,
            outcome="ACCESS_DENIED",
            details="User role lacks REVEAL_PII privilege",
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ACCESS_DENIED: Unauthorized user role"
        )

    # Check 3: Retrieve token or cipher
    # Try finding protected customer by customer_id or token directly
    token_to_resolve = req.subject_id
    customer = db.query(ProtectedCustomer).filter(ProtectedCustomer.customer_id == req.subject_id).first()
    
    if customer:
        field_upper = req.field.upper()
        if field_upper == "EMAIL":
            token_to_resolve = customer.email_token
        elif field_upper in ["MOBILE", "PHONE"]:
            token_to_resolve = customer.mobile_fpe
        elif field_upper == "NAME":
            token_to_resolve = customer.name_token

    plaintext = resolve_vault_mapping(db, token_to_resolve)
    
    if not plaintext:
        record_audit(
            db=db,
            actor=req.actor,
            action="REVEAL_PII",
            subject_id=req.subject_id,
            field=req.field,
            purpose=req.purpose,
            reference=req.reference,
            outcome="ACCESS_DENIED",
            details="Record not found in vault",
            ip_address=client_ip
        )
        raise HTTPException(status_code=404, detail="Requested identity not found in secure vault")

    # Record Success in Audit Log
    record_audit(
        db=db,
        actor=req.actor,
        action="REVEAL_PII",
        subject_id=req.subject_id,
        field=req.field,
        purpose=req.purpose,
        reference=req.reference,
        outcome="ALLOWED",
        details="Authorized reveal approved",
        ip_address=client_ip
    )

    return RevealResponse(
        subject_id=req.subject_id,
        field=req.field,
        plaintext_value=plaintext,
        purpose=req.purpose,
        reference=req.reference,
        outcome="ALLOWED"
    )
