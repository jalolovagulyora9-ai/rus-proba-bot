"""
Atomic registration service with PostgreSQL row-level locking.
Guarantees duplicate prevention and strict capacity limits under concurrent requests.
"""
from django.db import transaction, IntegrityError
from django.utils import timezone
from core.models import ExamConfig, Participant
from core.services.validator import (
    normalize_uzbek_phone,
    validate_name_part,
    validate_school_number,
    validate_full_name,
    ValidationError
)

class RegistrationError(Exception):
    """Base registration exception."""
    pass

class RegistrationClosedError(RegistrationError):
    """Raised when registration is disabled or outside active dates."""
    pass

class CapacityExceededError(RegistrationError):
    """Raised when the maximum participant capacity is reached."""
    pass

class AlreadyRegisteredError(RegistrationError):
    """Raised when user with the same telegram_id is already registered."""
    def __init__(self, message: str, participant: Participant = None):
        super().__init__(message)
        self.participant = participant


@transaction.atomic
def register_participant_sync(
    telegram_id: int,
    phone_number: str,
    region: str = "Farg'ona",
    district: str = "Mirzo Ulug'bek maktabi",
    first_name: str = None,
    last_name: str = None,
    school_number: str = "",
    full_name: str = None,
    username: str = None
) -> Participant:
    """
    Synchronous atomic registration function.
    Safely acquires row-level lock on ExamConfig to prevent race conditions at capacity limit.
    
    Accepts either (first_name, last_name) or full_name for backward compatibility.
    """
    # 1. Resolve and validate first_name & last_name
    if first_name and last_name:
        cleaned_first = validate_name_part(first_name, "Ism")
        cleaned_last = validate_name_part(last_name, "Familiya")
    elif full_name:
        cleaned_first, cleaned_last = validate_full_name(full_name)
    else:
        raise ValidationError("Ism va familiya ko'rsatilishi shart.")

    cleaned_phone = normalize_uzbek_phone(phone_number)
    cleaned_school = validate_school_number(school_number) if school_number else ""
    cleaned_region = region.strip() if region else "Farg'ona"
    cleaned_district = district.strip() if district else "Mirzo Ulug'bek maktabi"

    # 2. Acquire exclusive lock on ExamConfig row
    config = ExamConfig.objects.select_for_update().first()
    if not config:
        config = ExamConfig.objects.create()

    # 3. Check if registration is open
    if not config.is_registration_open:
        raise RegistrationClosedError(
            "Kechirasiz, ro'yxatdan o'tish hozirda to'xtatilgan."
        )

    # 4. Check active date window if dates are set
    now = timezone.now()
    if config.start_date and now < config.start_date:
        raise RegistrationClosedError(
            f"Ro'yxatdan o'tish hali boshlanmadi. Boshlanish vaqti: {config.start_date.strftime('%Y-%m-%d %H:%M')}"
        )
    if config.end_date and now > config.end_date:
        raise RegistrationClosedError(
            f"Ro'yxatdan o'tish muddati yakunlandi ({config.end_date.strftime('%Y-%m-%d %H:%M')})."
        )

    # 5. Check if user with this telegram_id is already registered
    existing_participant = Participant.objects.filter(telegram_id=telegram_id).first()
    if existing_participant:
        raise AlreadyRegisteredError(
            f"Siz allaqachon ro'yxatdan o'tgansiz!\nSizning ro'yxat raqamingiz: {existing_participant.reg_number}",
            participant=existing_participant
        )

    # 6. Check capacity limit inside the lock
    current_count = Participant.objects.count()
    if current_count >= config.max_capacity:
        raise CapacityExceededError(
            f"Afsuski, barcha ajratilgan {config.max_capacity} ta o'rin to'ldi. Ro'yxatdan o'tish yakunlandi."
        )

    # 7. Generate safe sequential unique registration number (Format: RU-0001, RU-0002, ...)
    next_number = current_count + 1
    reg_number = f"RU-{next_number:04d}"
    
    counter = next_number
    while Participant.objects.filter(reg_number=reg_number).exists():
        counter += 1
        reg_number = f"RU-{counter:04d}"

    # 8. Save participant
    try:
        participant = Participant.objects.create(
            telegram_id=telegram_id,
            telegram_username=username,
            first_name=cleaned_first,
            last_name=cleaned_last,
            phone_number=cleaned_phone,
            school_number=cleaned_school,
            region=cleaned_region,
            district=cleaned_district,
            reg_number=reg_number
        )
        return participant
    except IntegrityError as err:
        existing = Participant.objects.filter(telegram_id=telegram_id).first()
        if existing:
            raise AlreadyRegisteredError(
                f"Siz allaqachon ro'yxatdan o'tgansiz!\nSizning ro'yxat raqamingiz: {existing.reg_number}",
                participant=existing
            )
        raise RegistrationError(f"Ma'lumotlar bazasiga saqlashda xatolik: {err}")
