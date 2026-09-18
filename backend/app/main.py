from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.db.session import init_db
from app.api.discovery_routes import discovery_router
from app.api.batch_routes import batch_router
from app.api.customer_routes import customer_router
from app.api.audit_routes import audit_router
from app.api.policy_routes import policy_router
from app.gateway.router import gateway_router
from app.seed import seed_source_database

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Privacy-Preserving Customer Data Platform (Flyyy CDP)",
    lifespan=lifespan
)

# Health check
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@app.post("/seed", tags=["Admin"])
def trigger_seed(count: int = 50):
    seed_source_database(count)
    return {"status": "success", "message": f"Successfully seeded {count} source customers"}

# Register Routers
app.include_router(discovery_router)
app.include_router(batch_router)
app.include_router(customer_router)
app.include_router(audit_router)
app.include_router(policy_router)
app.include_router(gateway_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
