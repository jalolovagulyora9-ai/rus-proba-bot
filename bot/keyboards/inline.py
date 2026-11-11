"""
Inline Keyboards for Russian Proba Bot.
"""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.regions import get_region_list, get_districts_by_region

def get_start_registration_inline_keyboard() -> InlineKeyboardMarkup:
    """Inline button to start registration from /start message."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Ro'yxatdan o'tish", callback_data="start_reg")
    )
    return builder.as_markup()

def get_regions_inline_keyboard() -> InlineKeyboardMarkup:
    """Builds 2-column inline keyboard for all regions of Uzbekistan."""
    builder = InlineKeyboardBuilder()
    regions = get_region_list()
    for idx, reg_name in enumerate(regions):
        builder.button(text=reg_name, callback_data=f"reg:{idx}")
    builder.adjust(2)
    # Cancel row at bottom
    builder.row(
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_reg")
    )
    return builder.as_markup()

def get_districts_inline_keyboard(region_name: str) -> InlineKeyboardMarkup:
    """Builds 2-column inline keyboard for districts of selected region."""
    builder = InlineKeyboardBuilder()
    districts = get_districts_by_region(region_name)
    for idx, dist_name in enumerate(districts):
        builder.button(text=dist_name, callback_data=f"dist:{idx}")
    builder.adjust(2)
    # Navigation rows
    builder.row(
        InlineKeyboardButton(text="⬅️ Viloyatni qayta tanlash", callback_data="back_to_regions")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_reg")
    )
    return builder.as_markup()

def get_confirmation_inline_keyboard() -> InlineKeyboardMarkup:
    """Builds inline keyboard to confirm or restart registration."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Ma'lumotlarni tasdiqlash", callback_data="confirm_reg")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Qayta kiritish", callback_data="restart_reg"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_reg")
    )
    return builder.as_markup()
