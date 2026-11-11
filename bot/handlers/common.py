"""
Common commands and menu handlers (/start, /help, /cancel, /my_id).
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from bot.services import (
    get_participant_by_telegram_id,
    get_exam_status,
    format_participant_ticket,
)
from bot.keyboards import (
    get_main_menu_keyboard,
    get_start_registration_inline_keyboard,
)

common_router = Router(name="common_router")

@common_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Handles /start command.
    Checks existing registration and displays customized welcome.
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
            f"Siz allaqachon «{exam_info['title']}»ga muvaffaqiyatli ro'yxatdan o'tgansiz!\n\n"
            f"{ticket_text}",
            reply_markup=reply_kb
        )
        return

    # User is not registered yet
    reply_kb = get_main_menu_keyboard(is_registered=False)

    if not exam_info["is_open"]:
        await message.answer(
            f"Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
            f"«{exam_info['title']}»ga ro'yxatdan o'tish hozirda to'xtatilgan yoki yakunlangan.\n\n"
            f"Yangiliklardan xabardor bo'lish uchun rasmiy kanalimizni kuzatib boring.",
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

    # Registration is open
    text = (
        f"Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
        f"📚 <b>«{exam_info['title']}»</b> bepul offline mock imtihoniga ro'yxatdan o'tish botiga xush kelibsiz!\n\n"
        f"<b>Imtihon afzalliklari:</b>\n"
        f"• Milliy sertifikat standarti bo'yicha haqiqiy offline sinov;\n"
        f"• O'z bilim darajangizni aniq baholash imkoniyati;\n"
        f"• Mutlaqo bepul ishtirok.\n\n"
        f"Ro'yxatdan o'tish uchun quyidagi tugmani bosing:"
    )
    await message.answer(
        text,
        reply_markup=get_start_registration_inline_keyboard()
    )
    # Also ensure persistent main menu keyboard is set
    await message.answer(
        "Menyudan foydalanishingiz mumkin:",
        reply_markup=reply_kb
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
@common_router.message(F.text == "🎫 Mening ro'yxat raqamim")
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
    else:
        await message.answer(
            "Siz hali ro'yxatdan o'tmagansiz.\n"
            "Imtihonda qatnashish uchun ro'yxatdan o'tishingiz mumkin:",
            reply_markup=get_start_registration_inline_keyboard()
        )


@common_router.message(Command("help"))
@common_router.message(F.text == "ℹ️ Ma'lumot / Yo'riqnoma")
async def cmd_help(message: Message):
    """
    Displays exam details, rules, and contact info.
    """
    telegram_id = message.from_user.id
    participant = await get_participant_by_telegram_id(telegram_id)
    exam_info = await get_exam_status()

    exam_date = exam_info["exam_date"].strftime("%d.%m.%Y %H:%M") if exam_info["exam_date"] else "Tez orada e'lon qilinadi"
    exam_loc = exam_info["exam_location"] or "Toshkent shahri (aniq manzil e'lon qilinadi)"
    custom_info = exam_info["info_text"] or "Imtihon qoidalari haqida qo'shimcha ma'lumotlar e'lon qilinadi."

    text = (
        f"ℹ️ <b>IMTIHON HAQIDA MA'LUMOT VA YO'RIQNOMA</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📚 <b>Tadbir:</b> {exam_info['title']}\n"
        f"📅 <b>Imtihon kuni va vaqti:</b> {exam_date}\n"
        f"🏢 <b>O'tkazilish manzili:</b> {exam_loc}\n\n"
        f"<b>Qoidalar va talablar:</b>\n"
        f"1. Imtihonga kelganda shaxsni tasdiqlovchi hujjat (pasport / ID karta / guvohnoma) bo'lishi shart.\n"
        f"2. Bot tomonidan berilgan <b>RU-XXXX</b> shaklidagi ro'yxat raqami tekshiriladi.\n"
        f"3. Imtihon boshlanishidan kamida 30 daqiqa oldin kelishingiz so'raladi.\n"
        f"4. Bitta ishtirokchi faqat bir marotaba ro'yxatdan o'tishi mumkin.\n\n"
        f"<b>Qo'shimcha eslatma:</b>\n"
        f"{custom_info}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Savollar bo'yicha tashkilotchilarga murojaat qilishingiz mumkin."
    )
    await message.answer(text, reply_markup=get_main_menu_keyboard(is_registered=bool(participant)))
