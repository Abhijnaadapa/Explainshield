from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
import logging
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from database.mongodb import connect_to_mongo, close_mongo_connection
from routers import claims, onboarding, audit
from utils.auth import create_access_token

# Initialize logging
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup process
    print("--- Starting ExplainShield Backend ---")
    await connect_to_mongo()
    yield
    # Shutdown process
    await close_mongo_connection()
    print("--- Shutdown: ExplainShield Backend ---")

app = FastAPI(
    title="ExplainShield AI Compliance API",
    description="Insurance Fairness & Trust Audit Engine",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware: CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware: Request Logging & Logging Time
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = "{0:.2f}".format(process_time)
    logger.info(f"rid={request.url.path} method={request.method} time={formatted_process_time}ms status={response.status_code}")
    print(f"[{request.method}] {request.url.path} - {response.status_code} ({formatted_process_time}ms)")
    return response

# Root Endpoint
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "ExplainShield AI Auditor",
        "version": "1.0.0"
    }

# Include Routers
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["Onboarding"])
app.include_router(claims.router, prefix="/api/claims", tags=["Audit Pipeline"])
app.include_router(audit.router, prefix="/api/audit", tags=["Compliance Reporting"])

@app.get("/api/token")
async def get_token():
    """Generate a demo token for testing"""
    token = create_access_token({"company_id": "demo_audit_corp", "sub": "auditor@explainshield.ai"})
    return {"token": token}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
