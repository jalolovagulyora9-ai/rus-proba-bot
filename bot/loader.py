"""
aiogram 3 Bot and Dispatcher setup.
"""
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from django.conf import settings

from bot.handlers import get_handlers_router

def get_bot(token: str | None = None) -> Bot:
    """
    Returns an aiogram Bot instance configured with HTML parse mode.
    Falls back to a placeholder token if none is configured, to allow imports and tests without crashing.
    """
    actual_token = token or getattr(settings, 'BOT_TOKEN', '') or "123456789:AAG_dummy_placeholder_token_for_init"
    return Bot(
        token=actual_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

bot = get_bot()
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(get_handlers_router())
