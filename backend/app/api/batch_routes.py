from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import io
import csv
from app.db.session import get_db
from app.db.models import BatchRun, ProtectedCustomer
from app.batch.pipeline import run_batch_protection_job

batch_router = APIRouter(prefix="/batch", tags=["Batch Processing"])

class BatchTriggerRequest(BaseModel):
    source_name: Optional[str] = "source_customers"
    batch_size: Optional[int] = 1000

@batch_router.post("/run")
def trigger_batch_run(req: BatchTriggerRequest = BatchTriggerRequest(), db: Session = Depends(get_db)):
    """
    Triggers a chunked, idempotent batch protection run.
    """
    batch_run = run_batch_protection_job(db, source_name=req.source_name, batch_size=req.batch_size)
    return {
        "batch_id": batch_run.batch_id,
        "status": batch_run.status,
        "row_count": batch_run.row_count,
        "success_count": batch_run.success_count,
        "error_count": batch_run.error_count,
        "start_time": batch_run.start_time,
        "end_time": batch_run.end_time
    }

@batch_router.get("/list")
def list_batches(limit: int = 20, db: Session = Depends(get_db)):
    runs = db.query(BatchRun).order_by(BatchRun.start_time.desc()).limit(limit).all()
    return runs

@batch_router.get("/{batch_id}")
def get_batch_status(batch_id: str, db: Session = Depends(get_db)):
    run = db.query(BatchRun).filter(BatchRun.batch_id == batch_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Batch ID not found")
    return run

@batch_router.get("/export/csv")
def export_protected_csv(db: Session = Depends(get_db)):
    """
    Exports protected_customers as a CSV file to prove zero plaintext PII exists in exports.
    """
    records = db.query(ProtectedCustomer).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["customer_id", "name_token", "email_token", "mobile_fpe", "city", "segment", "batch_id"])
    
    for r in records:
        writer.writerow([r.customer_id, r.name_token, r.email_token, r.mobile_fpe, r.city, r.segment, r.batch_id])
        
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=protected_customers_export.csv"}
    )
