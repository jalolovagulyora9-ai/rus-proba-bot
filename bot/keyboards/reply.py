"""
Reply Keyboards for Russian Proba Bot.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def get_main_menu_keyboard(is_registered: bool = False) -> ReplyKeyboardMarkup:
    """Returns the persistent main menu reply keyboard."""
    if is_registered:
        keyboard = [
            [KeyboardButton(text="🎫 Mening chiptam"), KeyboardButton(text="📍 Imtihon lokatsiyasi")],
            [KeyboardButton(text="ℹ️ Imtihon qoidalari")]
        ]
    else:
        keyboard = [
            [KeyboardButton(text="📝 Ro'yxatdan o'tish")],
            [KeyboardButton(text="📍 Imtihon lokatsiyasi"), KeyboardButton(text="ℹ️ Imtihon haqida")]
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
