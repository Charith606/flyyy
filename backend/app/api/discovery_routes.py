from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import pandas as pd
import io
from app.db.session import get_db
from app.db.models import SourceCustomer
from app.discovery.analyzer import discover_dataset

discovery_router = APIRouter(prefix="/discovery", tags=["PII Discovery"])

@discovery_router.post("/run")
@discovery_router.post("")
def run_discovery(db: Session = Depends(get_db)):
    """
    Scans source_customers table and reports detected PII fields with confidence scores.
    """
    customers = db.query(SourceCustomer).limit(100).all()
    if not customers:
        return {"status": "empty", "message": "No source customer records found. Please seed or upload data.", "fields": []}
    
    records = [
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
    
    discovery_results = discover_dataset(records)
    return {
        "status": "success",
        "sample_size": len(records),
        "fields": discovery_results
    }

@discovery_router.post("/upload-csv")
async def discover_csv_upload(file: UploadFile = File(...)):
    """
    Accepts any uploaded CSV and performs PII detection without saving sensitive data.
    """
    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))
    records = df.head(100).to_dict(orient="records")
    discovery_results = discover_dataset(records)
    return {
        "filename": file.filename,
        "sample_size": len(records),
        "fields": discovery_results
    }
