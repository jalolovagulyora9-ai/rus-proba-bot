"""
Reply Keyboards for Russian Proba Bot.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def get_main_menu_keyboard(is_registered: bool = False) -> ReplyKeyboardMarkup:
    """Returns the persistent main menu reply keyboard."""
    if is_registered:
        keyboard = [
            [KeyboardButton(text="🎫 Mening ro'yxat raqamim")],
            [KeyboardButton(text="ℹ️ Ma'lumot / Yo'riqnoma")]
        ]
    else:
        keyboard = [
            [KeyboardButton(text="📝 Ro'yxatdan o'tish")],
            [KeyboardButton(text="ℹ️ Ma'lumot / Yo'riqnoma")]
        ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Returns keyboard with 'Share Contact' and 'Cancel' buttons."""
    keyboard = [
        [KeyboardButton(text="📱 Kontaktni ulashish", request_contact=True)],
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Returns keyboard with a single 'Cancel' button."""
    keyboard = [
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

remove_keyboard = ReplyKeyboardRemove()
