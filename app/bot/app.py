from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers.custom_request import router as custom_request_router
from app.bot.handlers.group_gating import router as group_gating_router
from app.bot.handlers.private_entry import router as private_entry_router
from app.bot.handlers.supplier_onboarding import router as supplier_onboarding_router


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(custom_request_router)
    dispatcher.include_router(group_gating_router)
    dispatcher.include_router(private_entry_router)
    dispatcher.include_router(supplier_onboarding_router)
    return dispatcher
