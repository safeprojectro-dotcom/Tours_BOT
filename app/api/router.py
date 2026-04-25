from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.admin_supplier_execution import router as admin_supplier_execution_router
from app.api.routes.admin_ops_ui import router as admin_ops_ui_router
from app.api.routes.health import router as health_router
from app.api.routes.mini_app import router as mini_app_router
from app.api.routes.ops_queue import router as ops_queue_router
from app.api.routes.payments import router as payments_router
from app.api.routes.supplier_admin import router as supplier_admin_router
from app.api.routes.telegram_webhook import router as telegram_webhook_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(admin_ops_ui_router)
api_router.include_router(admin_router)
api_router.include_router(admin_supplier_execution_router)
api_router.include_router(supplier_admin_router)
api_router.include_router(telegram_webhook_router)
api_router.include_router(mini_app_router)
api_router.include_router(payments_router)
api_router.include_router(ops_queue_router)
