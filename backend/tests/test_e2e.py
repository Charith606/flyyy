import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import init_db, SessionLocal
from app.db.models import SourceCustomer, ProtectedCustomer, VaultMapping, AuditLog, BatchRun
from app.seed import seed_source_database

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    init_db()
    seed_source_database(10)
    yield

def test_full_end_to_end_demonstration():
    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    # 2. PII Discovery
    disc_res = client.post("/discovery/run")
    assert disc_res.status_code == 200
    fields = disc_res.json()["fields"]
    field_names = [f["field_name"] for f in fields]
    assert "email" in field_names
    assert "mobile" in field_names
    assert "name" in field_names
    
    # Check confidence
    for f in fields:
        if f["field_name"] == "email":
            assert f["confidence"] >= 0.8
            assert f["recommended_action"] == "TOKENIZATION"
        elif f["field_name"] == "mobile":
            assert f["confidence"] >= 0.8
            assert f["recommended_action"] == "FPE"

    # 3. Batch Protection Run
    batch_res = client.post("/batch/run", json={"batch_size": 100})
    assert batch_res.status_code == 200
    batch_data = batch_res.json()
    assert batch_data["status"] == "COMPLETED"
    assert batch_data["success_count"] >= 5

    # 4. Verify Protected Customer Data (Zero Plaintext PII)
    cust_res = client.get("/customers")
    assert cust_res.status_code == 200
    cust_data = cust_res.json()
    assert cust_data["total"] >= 5
    first_cust = cust_data["items"][0]
    
    # Assert tokens & FPE formatting
    assert first_cust["name_token"].startswith("NAME_")
    assert first_cust["email_token"].startswith("EMAIL_")
    assert len(first_cust["mobile_fpe"]) == 10
    assert first_cust["mobile_fpe"].isdigit()
    assert "@" not in first_cust["email_token"]

    # 5. Verify CSV Export has only protected data
    csv_res = client.get("/batch/export/csv")
    assert csv_res.status_code == 200
    csv_text = csv_res.text
    assert "john@example.com" not in csv_text
    assert "EMAIL_" in csv_text

    # 6. Blind Marketing Campaign Execution via Privacy Gateway
    email_token = first_cust["email_token"]
    camp_payload = {
        "recipient": email_token,
        "campaign_id": "CMP1001",
        "template_id": "WELCOME",
        "subject": "Special Offer for You",
        "body": "Your welcome voucher is ready!"
    }
    camp_res = client.post("/gateway/send-campaign", json=camp_payload)
    assert camp_res.status_code == 200
    camp_data = camp_res.json()
    assert camp_data["status"] == "SENT"
    assert camp_data["recipient"] == email_token
    # CRITICAL: Plaintext email is NEVER returned in response
    assert "@" not in str(camp_data)

    # 7. Bounce Webhook Processing
    bounce_payload = {
        "email": "john@example.com",
        "event": "BOUNCE",
        "reason": "MAILBOX_NOT_FOUND"
    }
    bounce_res = client.post("/gateway/bounce-webhook", json=bounce_payload)
    assert bounce_res.status_code == 200
    bounce_data = bounce_res.json()
    assert bounce_data["status"] == "PROCESSED"
    assert bounce_data["recipient"].startswith("EMAIL_")

    # 8. Unauthorized Reveal Attempt (Must return 403 ACCESS_DENIED)
    unauth_payload = {
        "subject_id": first_cust["customer_id"],
        "field": "EMAIL",
        "purpose": "GENERIC_BROWSING", # Unauthorized purpose
        "reference": "", # Missing ticket
        "actor": "unauthorized_guest"
    }
    unauth_res = client.post("/gateway/reveal", json=unauth_payload)
    assert unauth_res.status_code == 403

    # 9. Authorized Reveal (Customer Support Ticket)
    auth_payload = {
        "subject_id": first_cust["customer_id"],
        "field": "EMAIL",
        "purpose": "CUSTOMER_SUPPORT",
        "reference": "TICKET-1091",
        "actor": "support_agent_sarah"
    }
    auth_res = client.post("/gateway/reveal", json=auth_payload)
    assert auth_res.status_code == 200
    auth_data = auth_res.json()
    assert auth_data["outcome"] == "ALLOWED"
    assert "@" in auth_data["plaintext_value"]

    # 10. Audit Log Verification
    audit_res = client.get("/audit")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["total"] >= 4
    
    actions = [item["action"] for item in audit_data["items"]]
    assert "SEND_CAMPAIGN_EMAIL" in actions
    assert "PROCESS_BOUNCE_WEBHOOK" in actions
    assert "REVEAL_PII" in actions
