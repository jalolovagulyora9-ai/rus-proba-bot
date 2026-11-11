"""
Registration FSM Handlers.
Updated flow:
1. Full Name (Ism va Familiya birgalikda)
2. Phone Number (Telefon raqami)
3. Region (Viloyat tanlash)
4. District (Tuman tanlash)
5. School Number (Maktab / Ta'lim muassasasi)
6. Confirmation (Tasdiqlash va unikal chipta berish)
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.states import RegistrationStates
from bot.services import (
    get_participant_by_telegram_id,
    get_exam_status,
    register_participant_async,
    format_participant_ticket,
)
from bot.utils.regions import (
    get_region_by_index,
    get_district_by_index,
)
from bot.keyboards import (
    get_main_menu_keyboard,
    get_phone_keyboard,
    get_cancel_keyboard,
    get_regions_inline_keyboard,
    get_districts_inline_keyboard,
    get_confirmation_inline_keyboard,
)
from core.services.validator import (
    validate_full_name,
    validate_school_number,
    normalize_uzbek_phone,
    ValidationError,
)
from core.services.registration import (
    AlreadyRegisteredError,
    CapacityExceededError,
    RegistrationClosedError,
    RegistrationError,
)

registration_router = Router(name="registration_router")


async def start_registration_flow(user_id: int, user_full_name: str, target_message: Message, state: FSMContext):
    """Initiates registration flow after sanity checks."""
    participant = await get_participant_by_telegram_id(user_id)
    exam_info = await get_exam_status()

    if participant:
        ticket = format_participant_ticket(participant, exam_info)
        await target_message.answer(
            f"Siz allaqachon ro'yxatdan o'tgansiz!\n\n{ticket}",
            reply_markup=get_main_menu_keyboard(is_registered=True)
        )
        return

    if not exam_info["is_open"]:
        await target_message.answer(
            f"Kechirasiz, «{exam_info['title']}»ga ro'yxatdan o'tish hozirda to'xtatilgan.",
            reply_markup=get_main_menu_keyboard(is_registered=False)
        )
        return

    if exam_info["is_full"]:
        await target_message.answer(
            f"Kechirasiz, barcha ajratilgan {exam_info['max_capacity']} ta o'rin to'ldi. Ro'yxatdan o'tish yakunlandi.",
            reply_markup=get_main_menu_keyboard(is_registered=False)
        )
        return

    await state.clear()
    await state.set_state(RegistrationStates.full_name)
    await target_message.answer(
        "📝 <b>Ro'yxatdan o'tish jarayoni boshlandi.</b>\n\n"
        "<b>1-bosqich:</b> Iltimos, ism va familiyangizni kiriting (masalan: <i>Jasur Rustamov</i> yoki <i>Rustamov Jasur</i>):",
        reply_markup=get_cancel_keyboard()
    )


@registration_router.message(Command("register"))
@registration_router.message(F.text == "📝 Ro'yxatdan o'tish")
async def start_registration_msg(message: Message, state: FSMContext):
    """Starts registration via message or menu button."""
    await start_registration_flow(
        user_id=message.from_user.id,
        user_full_name=message.from_user.full_name,
        target_message=message,
        state=state
    )


@registration_router.callback_query(F.data == "start_reg")
async def start_registration_cb(callback: CallbackQuery, state: FSMContext):
    """Starts registration via inline button."""
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await start_registration_flow(
        user_id=callback.from_user.id,
        user_full_name=callback.from_user.full_name,
        target_message=callback.message,
        state=state
    )


# --- Step 1: Full Name (Ism va Familiya birgalikda) ---
@registration_router.message(RegistrationStates.full_name)
async def process_full_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("⚠️ Iltimos, ism va familiyangizni matn ko'rinishida yuboring:")
        return

    try:
        cleaned_first, cleaned_last = validate_full_name(message.text)
    except ValidationError as err:
        await message.answer(f"⚠️ {err}\n\nIltimos, qaytadan kiriting (masalan: <i>Jasur Rustamov</i>):")
        return

    display_name = f"{cleaned_first} {cleaned_last}"
    await state.update_data(
        first_name=cleaned_first,
        last_name=cleaned_last,
        full_name=display_name
    )
    await state.set_state(RegistrationStates.phone_number)
    await message.answer(
        f"Rahmat, <b>{display_name}</b>!\n\n"
        "<b>2-bosqich:</b> Telefon raqamingizni yuboring.\n\n"
        "Quyidagi <b>«📱 Kontaktni ulashish»</b> tugmasini bosing yoki "
        "raqamingizni qo'lda yozing (masalan: <code>+998901234567</code>):",
        reply_markup=get_phone_keyboard()
    )


# --- Step 2: Phone Number ---
@registration_router.message(RegistrationStates.phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    raw_phone = None
    if message.contact and message.contact.phone_number:
        raw_phone = message.contact.phone_number
    elif message.text:
        raw_phone = message.text

    if not raw_phone:
        await message.answer(
            "⚠️ Iltimos, pastdagi «📱 Kontaktni ulashish» tugmasini bosing yoki telefon raqamingizni yozib yuboring:",
            reply_markup=get_phone_keyboard()
        )
        return

    try:
        cleaned_phone = normalize_uzbek_phone(raw_phone)
    except ValidationError as err:
        await message.answer(
            f"⚠️ {err}\n\nIltimos, O'zbekiston telefon raqamini to'g'ri formatda kiriting (masalan: <code>+998901234567</code>):",
            reply_markup=get_phone_keyboard()
        )
        return

    await state.update_data(phone_number=cleaned_phone)
    await state.set_state(RegistrationStates.region)

    await message.answer(
        "<b>3-bosqich:</b> Qaysi viloyat / hududdansiz?\n\n"
        "Quyidagi ro'yxatdan viloyatingiz yoki shahringizni tanlang:",
        reply_markup=get_regions_inline_keyboard()
    )


# --- Step 3: Region Selection (Inline) ---
@registration_router.callback_query(RegistrationStates.region, F.data.startswith("reg:"))
async def process_region_selection(callback: CallbackQuery, state: FSMContext):
    idx_str = callback.data.split(":")[1]
    try:
        reg_idx = int(idx_str)
        region_name = get_region_by_index(reg_idx)
    except (ValueError, IndexError):
        await callback.answer("Viloyat topilmadi, qaytadan tanlang.", show_alert=True)
        return

    if not region_name:
        await callback.answer("Noto'g'ri viloyat tanlandi.", show_alert=True)
        return

    await state.update_data(region=region_name)
    await state.set_state(RegistrationStates.district)
    await callback.answer(f"Tanlandi: {region_name}")

    await callback.message.edit_text(
        f"📍 Tanlangan viloyat: <b>{region_name}</b>\n\n"
        "<b>4-bosqich:</b> Tuman yoki shahringizni tanlang:",
        reply_markup=get_districts_inline_keyboard(region_name)
    )


# --- Back to Region Selection from District ---
@registration_router.callback_query(RegistrationStates.district, F.data == "back_to_regions")
async def back_to_regions(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RegistrationStates.region)
    await callback.answer("Viloyatlar ro'yxatiga qaytildi.")
    await callback.message.edit_text(
        "<b>3-bosqich:</b> Qaysi viloyat / hududdansiz?\n\n"
        "Quyidagi ro'yxatdan viloyatingiz yoki shahringizni tanlang:",
        reply_markup=get_regions_inline_keyboard()
    )


# --- Step 4: District Selection -> School Prompt ---
@registration_router.callback_query(RegistrationStates.district, F.data.startswith("dist:"))
async def process_district_selection(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    region_name = data.get("region")
    if not region_name:
        await callback.answer("Avval viloyatni tanlang.", show_alert=True)
        await state.set_state(RegistrationStates.region)
        return

    idx_str = callback.data.split(":")[1]
    try:
        dist_idx = int(idx_str)
        district_name = get_district_by_index(region_name, dist_idx)
    except (ValueError, IndexError):
        await callback.answer("Tuman topilmadi, qaytadan tanlang.", show_alert=True)
        return

    if not district_name:
        await callback.answer("Noto'g'ri tuman tanlandi.", show_alert=True)
        return

    await state.update_data(district=district_name)
    await state.set_state(RegistrationStates.school_number)
    await callback.answer(f"Tanlandi: {district_name}")

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        f"📍 Tanlangan hudud: <b>{region_name}, {district_name}</b>\n\n"
        "<b>5-bosqich:</b> Ta'lim muassasangiz haqida ma'lumot kiriting.\n\n"
        "O'qiyotgan maktabingiz, litsey yoki o'quv markazingiz nomi/nomerini yozing "
        "(masalan: <i>14-maktab</i>, <i>Prezident maktabi</i> yoki <i>2-son IDUM</i>):",
        reply_markup=get_cancel_keyboard()
    )


# --- Step 5: School / Institution -> Confirmation Summary ---
@registration_router.message(RegistrationStates.school_number)
async def process_school_number(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("⚠️ Iltimos, maktab yoki ta'lim muassasasi nomini matn shaklida yozing:")
        return

    try:
        cleaned_school = validate_school_number(message.text)
    except ValidationError as err:
        await message.answer(f"⚠️ {err}\n\nIltimos, qaytadan kiriting:")
        return

    await state.update_data(school_number=cleaned_school)
    await state.set_state(RegistrationStates.confirm)

    data = await state.get_data()
    full_name = data.get("full_name") or f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()

    summary_text = (
        "📋 <b>KIRITILGAN MA'LUMOTLARNI TEKSHIRING:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>F.I.Sh:</b> {full_name}\n"
        f"📱 <b>Telefon:</b> {data.get('phone_number')}\n"
        f"📍 <b>Hudud:</b> {data.get('region')}, {data.get('district')}\n"
        f"🏫 <b>Ta'lim muassasasi:</b> {cleaned_school}\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Barcha ma'lumotlar to'g'ri bo'lsa, <b>«✅ Ma'lumotlarni tasdiqlash»</b> tugmasini bosing."
    )

    await message.answer(
        summary_text,
        reply_markup=get_confirmation_inline_keyboard()
    )


# --- Step 6: Restart Registration from Confirmation ---
@registration_router.callback_query(RegistrationStates.confirm, F.data == "restart_reg")
async def restart_registration(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(RegistrationStates.full_name)
    await callback.answer("Qaytadan kiritish boshlandi.")

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "✏️ Qaytadan kiritish:\n\n"
        "<b>1-bosqich:</b> Iltimos, ism va familiyangizni kiriting (masalan: <i>Jasur Rustamov</i>):",
        reply_markup=get_cancel_keyboard()
    )


# --- Step 7: Confirm and Execute Atomic DB Registration ---
@registration_router.callback_query(RegistrationStates.confirm, F.data == "confirm_reg")
async def execute_registration(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    telegram_id = callback.from_user.id
    username = callback.from_user.username

    await callback.answer("Ro'yxatga olinmoqda...")

    try:
        participant = await register_participant_async(
            telegram_id=telegram_id,
            phone_number=data.get('phone_number'),
            region=data.get('region'),
            district=data.get('district'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            school_number=data.get('school_number'),
            username=username
        )
    except AlreadyRegisteredError as err:
        await state.clear()
        exam_info = await get_exam_status()
        existing = await get_participant_by_telegram_id(telegram_id)
        ticket = format_participant_ticket(existing, exam_info) if existing else ""
        await callback.message.edit_text(
            f"⚠️ {err}\n\n{ticket}"
        )
        await callback.message.answer(
            "Bosh menyu:",
            reply_markup=get_main_menu_keyboard(is_registered=True)
        )
        return
    except CapacityExceededError as err:
        await state.clear()
        await callback.message.edit_text(f"❌ {err}")
        await callback.message.answer(
            "Bosh menyu:",
            reply_markup=get_main_menu_keyboard(is_registered=False)
        )
        return
    except RegistrationClosedError as err:
        await state.clear()
        await callback.message.edit_text(f"❌ {err}")
        await callback.message.answer(
            "Bosh menyu:",
            reply_markup=get_main_menu_keyboard(is_registered=False)
        )
        return
    except (ValidationError, RegistrationError) as err:
        await callback.message.answer(f"⚠️ Xatolik yuz berdi: {err}\nQaytadan urinib ko'ring.")
        return
    except Exception as err:
        await callback.message.answer(
            f"⚠️ Kutilmagan tizim xatoligi yuz berdi. Iltimos, keyinroq qayta urinib ko'ring."
        )
        return

    # Registration successful!
    await state.clear()
    exam_info = await get_exam_status()
    ticket_card = format_participant_ticket(participant, exam_info)

    try:
        await callback.message.delete()
    except Exception:
        pass

    success_message = (
        f"🎉 <b>TABRIKLAYMIZ! RO'YXATDAN O'TISH MUVAFFAQIYATLI YAKUNLANDI!</b>\n\n"
        f"{ticket_card}"
    )
    await callback.message.answer(
        success_message,
        reply_markup=get_main_menu_keyboard(is_registered=True)
    )
