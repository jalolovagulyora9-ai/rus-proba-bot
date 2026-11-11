"""
Async bridge services between aiogram handlers and Django ORM models.
Leverages Django 5.1 native async ORM methods (afirst, acount, acreate).
"""
from asgiref.sync import sync_to_async
from django.utils import timezone
from core.models import ExamConfig, Participant
from core.services.registration import (
    register_participant_sync,
    RegistrationError,
    RegistrationClosedError,
    CapacityExceededError,
    AlreadyRegisteredError,
)
from core.services.validator import ValidationError

async def get_participant_by_telegram_id(telegram_id: int) -> Participant | None:
    """Retrieves participant by telegram_id, or None if not found."""
    return await Participant.objects.filter(telegram_id=telegram_id).afirst()

async def get_exam_status() -> dict:
    """
    Returns current exam configuration and registration status.
    Uses Django 5.1 native async methods.
    """
    config = await ExamConfig.objects.afirst()
    if not config:
        config = await ExamConfig.objects.acreate()

    current_count = await Participant.objects.acount()
    now = timezone.now()

    is_open = config.is_registration_open
    if config.start_date and now < config.start_date:
        is_open = False
    if config.end_date and now > config.end_date:
        is_open = False

    is_full = current_count >= config.max_capacity

    return {
        "title": config.title,
        "is_open": is_open,
        "is_full": is_full,
        "max_capacity": config.max_capacity,
        "current_count": current_count,
        "start_date": config.start_date,
        "end_date": config.end_date,
        "exam_date": config.exam_date,
        "exam_location": config.exam_location,
        "info_text": config.info_text,
    }

# Sync-to-async wrapper for atomic registration transaction
_register_async_worker = sync_to_async(register_participant_sync, thread_sensitive=False)

async def register_participant_async(
    telegram_id: int,
    phone_number: str,
    region: str,
    district: str,
    first_name: str,
    last_name: str,
    school_number: str,
    username: str | None = None
) -> Participant:
    """
    Asynchronous wrapper around atomic register_participant_sync.
    """
    return await _register_async_worker(
        telegram_id=telegram_id,
        phone_number=phone_number,
        region=region,
        district=district,
        first_name=first_name,
        last_name=last_name,
        school_number=school_number,
        username=username
    )

def format_participant_ticket(participant: Participant, exam_info: dict | None = None) -> str:
    """
    Formats participant information into a clean, professional HTML ticket card.
    """
    exam_date_str = "15-noyabr"
    location_str = "Mirzo Ulug'bek xususiy maktabi"

    if exam_info:
        if exam_info.get("exam_date"):
            exam_date_str = exam_info["exam_date"].strftime("%d.%m.%Y %H:%M")
        if exam_info.get("exam_location"):
            location_str = exam_info["exam_location"]

    ticket = (
        f"🎫 <b>RASMIY ISHTIROKCHI CHIPTASI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>Chipta raqami:</b> <code>{participant.reg_number}</code>\n"
        f"👤 <b>F.I.Sh:</b> {participant.full_name}\n"
        f"📱 <b>Telefon:</b> {participant.phone_number}\n"
        f"📅 <b>Imtihon sanasi:</b> {exam_date_str}\n"
        f"🏫 <b>O'tkazilish joyi:</b> {location_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <i>Imtihonga kelganda ushbu <b>{participant.reg_number}</b> raqamingiz va "
        f"shaxsni tasdiqlovchi hujjat (pasport / ID karta / guvohnoma) ko'rsatilishi shart!</i>"
    )
    return ticket
