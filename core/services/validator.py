"""
Input validation and sanitization service.
Focuses on Uzbekistan phone numbers, names, and school information.
"""
import re

class ValidationError(Exception):
    pass

def normalize_uzbek_phone(phone_input: str) -> str:
    """
    Normalizes any Uzbekistan phone number format to standard E.164 (+998XXXXXXXXX).
    Examples:
        "+998 (90) 123-45-67" -> "+998901234567"
        "998901234567"        -> "+998901234567"
        "901234567"           -> "+998901234567"
    Raises ValidationError if invalid.
    """
    if not phone_input or not isinstance(phone_input, str):
        raise ValidationError("Telefon raqami bo'sh bo'lishi mumkin emas.")

    cleaned = re.sub(r'\D', '', phone_input)

    if len(cleaned) == 12 and cleaned.startswith('998'):
        normalized = f"+{cleaned}"
    elif len(cleaned) == 9:
        normalized = f"+998{cleaned}"
    else:
        raise ValidationError(
            "Noto'g'ri telefon raqami formati. Namuna: +998901234567"
        )

    operator_code = normalized[4:6]
    valid_codes = {
        '20', '33', '50', '55', '71', '72', '73', '74', '75', '76', '77', 
        '78', '79', '88', '90', '91', '93', '94', '95', '97', '98', '99'
    }
    if operator_code not in valid_codes:
        raise ValidationError(
            f"O'zbekiston mobil operatori kodi topilmadi ({operator_code}). Namuna: +998901234567"
        )

    return normalized


def validate_name_part(name_input: str, field_label: str = "Ism") -> str:
    """
    Validates a single name part (first_name or last_name).
    Ensures length between 2 and 50 characters, letters and apostrophes only.
    """
    if not name_input or not isinstance(name_input, str):
        raise ValidationError(f"{field_label} bo'sh bo'lishi mumkin emas.")

    cleaned = name_input.strip()
    if len(cleaned) < 2 or len(cleaned) > 50:
        raise ValidationError(f"{field_label} 2 tadan 50 tagacha belgidan iborat bo'lishi kerak.")

    if not re.match(r"^[a-zA-Zа-яА-ЯёЁўЎқҚғҒҳҲ'`ʻʼ\s-]+$", cleaned):
        raise ValidationError(f"{field_label}da faqat harflar va chiziqcha bo'lishi mumkin.")

    return " ".join(word.capitalize() for word in cleaned.split())


def validate_school_number(school_input: str) -> str:
    """
    Validates school number or institution name.
    Accepts numbers ("15", "42"), school types ("15-maktab", "3-IDUM", "Prezident maktabi").
    """
    if not school_input or not isinstance(school_input, str):
        raise ValidationError("Maktab nomeri yoki nomi bo'sh bo'lishi mumkin emas.")

    cleaned = school_input.strip()
    if len(cleaned) < 1 or len(cleaned) > 100:
        raise ValidationError("Maktab ma'lumoti 1 tadan 100 tagacha belgidan iborat bo'lishi kerak.")

    return cleaned


def validate_full_name(name_input: str) -> tuple[str, str]:
    """
    Splits and validates a two-part full name string into (first_name, last_name).
    """
    if not name_input or not isinstance(name_input, str):
        raise ValidationError("Ism va familiya bo'sh bo'lishi mumkin emas.")

    cleaned = name_input.strip()
    words = cleaned.split()

    if len(words) < 2:
        raise ValidationError(
            "Iltimos, ism va familiyangizni to'liq kiriting (masalan: Jasur Rustamov)."
        )

    first_name = validate_name_part(words[0], "Ism")
    last_name = validate_name_part(" ".join(words[1:]), "Familiya")
    return first_name, last_name
