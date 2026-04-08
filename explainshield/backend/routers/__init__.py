from fastapi import APIRouter
from .onboarding import router as onboarding_router
from .claims import router as claims_router
from .audit import router as audit_router

# All routers are exported as the 'router' for each module
