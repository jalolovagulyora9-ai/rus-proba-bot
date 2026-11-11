"""
Common commands and menu handlers (/start, /help, /cancel, /my_id, /location).
"""
import os
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from django.conf import settings

from bot.services import (
    get_participant_by_telegram_id,
    get_exam_status,
    format_participant_ticket,
)
from bot.keyboards import (
    get_main_menu_keyboard,
    get_start_registration_inline_keyboard,
    get_location_inline_keyboard,
)

common_router = Router(name="common_router")

PROMO_CAPTION = (
    "🏛 <b>RUS TILI VA ADABIYOTIDAN MILLIY SERTIFIKAT SINOV IMTIHONI!</b>\n\n"
    "<i>O'z bilimingizni sinab ko'ring va haqiqiy imtihon muhitini his eting!</i>\n\n"
    "👨‍🏫 <b>EKSPERT VA TASHKILOTCHI: Jalolov Asrorjon</b>\n"
    "✅ Rus tilidan xalqaro <b>C1</b> daraja sertifikati sohibi.\n"
    "✅ Milliy sertifikat bo'yicha eng yuqori <b>A daraja</b> egasi.\n"
    "✅ Ko'plab o'qituvchilarni attestatsiya va toifa imtihonlariga tayyorlagan tajribali ustoz.\n\n"
    "🏫 <b>O'tkazilish joyi:</b> Mirzo Ulug'bek xususiy maktabi\n"
    "📅 <b>Sana:</b> 15-NOYABR\n"
    "🎟 <b>Qatnashish:</b> MUTLAQO BEPUL!\n\n"
    "⚠️ <i>Joylar soni cheklangan! Ro'yxatdan o'tish uchun quyidagi tugmani bosing:</i>"
)

@common_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Handles /start command.
    Sends promo banner with expert info for new users, or ticket for registered users.
    """
    await state.clear()
    telegram_id = message.from_user.id
    participant = await get_participant_by_telegram_id(telegram_id)
    exam_info = await get_exam_status()

    if participant:
        reply_kb = get_main_menu_keyboard(is_registered=True)
        ticket_text = format_participant_ticket(participant, exam_info)
        await message.answer(
            f"Assalomu alaykum, <b>{participant.first_name}</b>!\n\n"
            f"Siz allaqachon imtihonga ro'yxatdan o'tgansiz!\n\n"
            f"{ticket_text}",
            reply_markup=reply_kb
        )
        return

    # User is not registered yet
    reply_kb = get_main_menu_keyboard(is_registered=False)

    if not exam_info["is_open"]:
        await message.answer(
            f"Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
            f"«{exam_info['title']}»ga ro'yxatdan o'tish hozirda to'xtatilgan yoki yakunlangan.",
            reply_markup=reply_kb
        )
        return

    if exam_info["is_full"]:
        await message.answer(
            f"Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
            f"Afsuski, imtihon uchun ajratilgan barcha <b>{exam_info['max_capacity']}</b> ta o'rin to'ldi.\n"
            f"Ro'yxatdan o'tish yakunlandi.",
            reply_markup=reply_kb
        )
        return

    # Check for banner image
    banner_file = Path(settings.BASE_DIR) / "data" / "banner.jpg"
    inline_kb = get_start_registration_inline_keyboard()

    if banner_file.exists():
        try:
            await message.answer_photo(
                photo=FSInputFile(str(banner_file)),
                caption=PROMO_CAPTION,
                reply_markup=inline_kb
            )
        except Exception:
            await message.answer(
                PROMO_CAPTION,
                reply_markup=inline_kb
            )
    else:
        await message.answer(
            PROMO_CAPTION,
            reply_markup=inline_kb
        )

    # Send persistent menu keyboard
    await message.answer(
        "Quyidagi menyudan ham foydalanishingiz mumkin:",
        reply_markup=reply_kb
    )


@common_router.message(F.text.in_(["📍 Imtihon lokatsiyasi", "📍 Imtihon manzili", "/location"]))
async def cmd_location(message: Message):
    """
    Sends the exact GPS location of Mirzo Ulug'bek private school.
    """
    lat = 40.619075
    lon = 70.982239
    await message.answer_location(
        latitude=lat,
        longitude=lon
    )
    await message.answer(
        "📍 <b>Imtihon o'tkaziladigan joy:</b> Mirzo Ulug'bek xususiy maktabi\n"
        "📅 <b>Imtihon sanasi:</b> 15-noyabr\n\n"
        "Xaritada ko'rish yoki marshrut chizish uchun quyidagi tugmani bosing:",
        reply_markup=get_location_inline_keyboard()
    )


@common_router.message(Command("cancel"))
@common_router.message(F.text == "❌ Bekor qilish")
async def cmd_cancel(message: Message, state: FSMContext):
    """
    Cancels current operation and resets FSM state.
    """
    current_state = await state.get_state()
    await state.clear()

    telegram_id = message.from_user.id
    participant = await get_participant_by_telegram_id(telegram_id)
    reply_kb = get_main_menu_keyboard(is_registered=bool(participant))

    if current_state is None:
        await message.answer(
            "Bosh menyudasiz.",
            reply_markup=reply_kb
        )
    else:
        await message.answer(
            "Jarayon bekor qilindi. Bosh menyudasiz.",
            reply_markup=reply_kb
        )


@common_router.callback_query(F.data == "cancel_reg")
async def cb_cancel_reg(callback: CallbackQuery, state: FSMContext):
    """
    Cancels registration via inline button.
    """
    await state.clear()
    telegram_id = callback.from_user.id
    participant = await get_participant_by_telegram_id(telegram_id)
    reply_kb = get_main_menu_keyboard(is_registered=bool(participant))

    await callback.answer("Ro'yxatdan o'tish bekor qilindi.")
    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "Ro'yxatdan o'tish bekor qilindi. Bosh menyudasiz.",
        reply_markup=reply_kb
    )


@common_router.message(Command("my_id"))
@common_router.message(F.text.in_(["🎫 Mening chiptam", "🎫 Mening ro'yxat raqamim"]))
async def cmd_my_id(message: Message):
    """
    Displays ticket info for already registered participant.
    """
    telegram_id = message.from_user.id
    participant = await get_participant_by_telegram_id(telegram_id)
    exam_info = await get_exam_status()

    if participant:
        ticket = format_participant_ticket(participant, exam_info)
        await message.answer(ticket, reply_markup=get_main_menu_keyboard(is_registered=True))
        await message.answer(
            "📍 Imtihon manzilini xaritada ko'rish uchun:",
            reply_markup=get_location_inline_keyboard()
        )
    else:
        await message.answer(
            "Siz hali ro'yxatdan o'tmagansiz.\n"
            "Imtihonda qatnashish uchun ro'yxatdan o'tishingiz mumkin:",
            reply_markup=get_start_registration_inline_keyboard()
        )


@common_router.message(Command("help"))
@common_router.message(F.text.in_(["ℹ️ Imtihon qoidalari", "ℹ️ Imtihon haqida", "ℹ️ Ma'lumot / Yo'riqnoma"]))
async def cmd_help(message: Message):
    """
    Displays exam details, rules, and contact info.
    """
    telegram_id = message.from_user.id
    participant = await get_participant_by_telegram_id(telegram_id)
    exam_info = await get_exam_status()

    text = (
        f"ℹ️ <b>IMTIHON HAQIDA MA'LUMOT VA TALABLAR</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📚 <b>Tadbir:</b> {exam_info['title']}\n"
        f"👨‍🏫 <b>Ekspert:</b> Jalolov Asrorjon (C1 / A daraja)\n"
        f"📅 <b>Sana:</b> 15-NOYABR\n"
        f"🏢 <b>O'tkazilish joyi:</b> Mirzo Ulug'bek xususiy maktabi\n"
        f"🎟 <b>Ishtirok:</b> Bepul\n\n"
        f"<b>Qoidalar:</b>\n"
        f"1. Imtihonga kelganda shaxsni tasdiqlovchi hujjat (pasport / ID karta / guvohnoma) ko'rsatiladi.\n"
        f"2. Bot tomonidan berilgan <b>RU-XXXX</b> raqami eshikda tekshiriladi.\n"
        f"3. O'zingiz bilan ko'k/qora ruchka olishingiz so'raladi.\n"
        f"4. Imtihon boshlanishidan kamida 30 daqiqa oldin kelish tavsiya etiladi.\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text, reply_markup=get_main_menu_keyboard(is_registered=bool(participant)))
