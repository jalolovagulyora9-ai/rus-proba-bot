"""
Handlers router configuration.
"""
from aiogram import Router
from bot.handlers.common import common_router
from bot.handlers.registration import registration_router

def get_handlers_router() -> Router:
    """Combines all modular routers into a single root router."""
    root_router = Router(name="root_router")
    root_router.include_router(common_router)
    root_router.include_router(registration_router)
    return root_router
