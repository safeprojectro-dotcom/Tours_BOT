from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.mini_app import router as mini_app_router
from app.api.routes.payments import router as payments_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(mini_app_router)
api_router.include_router(payments_router)
