"""
Secure Backup and Disaster Recovery Service.
Safely exports and restores participant data in JSON and Excel formats.
Saves to the server's protected backups/ directory.
"""
import io
import json
import zipfile
from pathlib import Path
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from django.db import transaction

from core.models import Participant, ExamConfig
from core.services.export import export_participants_to_excel

class BackupError(Exception):
    """Base exception for backup/restore operations."""
    pass


def get_default_backup_dir() -> Path:
    """Returns the absolute path to the backups directory, creating it if needed."""
    backup_dir = getattr(settings, 'BACKUP_DIR', settings.BASE_DIR / 'backups')
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def create_backup(
    destination_dir: Path | None = None,
    include_excel: bool = True
) -> dict:
    """
    Creates a full snapshot backup of all registered participants.
    Generates a structured JSON dump and openpyxl Excel file bundled into a compressed ZIP archive.
    """
    out_dir = destination_dir or get_default_backup_dir()
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"backup_participants_{now_str}.zip"
    zip_path = out_dir / zip_filename

    participants = list(Participant.objects.all().order_by('id'))
    config = ExamConfig.get_solo()

    # 1. Prepare JSON snapshot data
    payload = {
        "metadata": {
            "created_at": timezone.now().isoformat(),
            "system": "RUSSIAN PROBA BOT",
            "version": "1.0",
            "total_participants": len(participants),
            "exam_config": {
                "title": config.title,
                "is_registration_open": config.is_registration_open,
                "max_capacity": config.max_capacity,
                "exam_date": config.exam_date.isoformat() if config.exam_date else None,
                "exam_location": config.exam_location,
            }
        },
        "participants": [
            {
                "id": p.id,
                "reg_number": p.reg_number,
                "telegram_id": p.telegram_id,
                "telegram_username": p.telegram_username,
                "first_name": p.first_name,
                "last_name": p.last_name,
                "phone_number": p.phone_number,
                "school_number": p.school_number,
                "region": p.region,
                "district": p.district,
                "is_attended": p.is_attended,
                "bot_blocked": p.bot_blocked,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in participants
        ]
    }
    json_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')

    # 2. Prepare Excel snapshot bytes if requested
    excel_bytes = None
    if include_excel:
        excel_response = export_participants_to_excel(participants)
        excel_bytes = excel_response.content

    # 3. Create ZIP archive
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"participants_{now_str}.json", json_bytes)
        if excel_bytes:
            zf.writestr(f"participants_{now_str}.xlsx", excel_bytes)

    file_size = zip_path.stat().st_size
    return {
        "backup_path": zip_path,
        "filename": zip_filename,
        "total_participants": len(participants),
        "file_size_bytes": file_size,
        "created_at": now_str,
    }


def restore_backup(
    backup_file_path: str | Path,
    overwrite_existing: bool = False,
    dry_run: bool = False
) -> dict:
    """
    Restores participants from a backup archive (.zip) or JSON dump.
    Preserves unique reg_numbers, timestamps, and attendance statuses.
    """
    path = Path(backup_file_path)
    if not path.exists():
        raise BackupError(f"Zaxira fayli topilmadi: {path}")

    # Extract JSON content
    json_data = None
    if path.suffix.lower() == '.zip':
        with zipfile.ZipFile(path, 'r') as zf:
            json_filenames = [name for name in zf.namelist() if name.endswith('.json')]
            if not json_filenames:
                raise BackupError("ZIP arxiv ichida JSON fayl topilmadi.")
            with zf.open(json_filenames[0]) as f:
                json_data = json.load(f)
    elif path.suffix.lower() == '.json':
        with open(path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    else:
        raise BackupError("Qo'llab-quvvatlanmaydigan fayl formati. Faqat .zip yoki .json qabul qilinadi.")

    participants_list = json_data.get("participants", [])
    created_count = 0
    updated_count = 0
    skipped_count = 0

    with transaction.atomic():
        for item in participants_list:
            telegram_id = item.get("telegram_id")
            reg_number = item.get("reg_number")
            if not telegram_id or not reg_number:
                continue

            existing = Participant.objects.filter(telegram_id=telegram_id).first()

            if existing:
                if overwrite_existing:
                    existing.reg_number = reg_number
                    existing.telegram_username = item.get("telegram_username")
                    existing.first_name = item.get("first_name", "")
                    existing.last_name = item.get("last_name", "")
                    existing.phone_number = item.get("phone_number", "")
                    existing.school_number = item.get("school_number", "")
                    existing.region = item.get("region", "")
                    existing.district = item.get("district", "")
                    existing.is_attended = bool(item.get("is_attended", False))
                    existing.bot_blocked = bool(item.get("bot_blocked", False))
                    existing.save()
                    updated_count += 1
                else:
                    skipped_count += 1
            else:
                Participant.objects.create(
                    telegram_id=telegram_id,
                    telegram_username=item.get("telegram_username"),
                    reg_number=reg_number,
                    first_name=item.get("first_name", ""),
                    last_name=item.get("last_name", ""),
                    phone_number=item.get("phone_number", ""),
                    school_number=item.get("school_number", ""),
                    region=item.get("region", ""),
                    district=item.get("district", ""),
                    is_attended=bool(item.get("is_attended", False)),
                    bot_blocked=bool(item.get("bot_blocked", False)),
                )
                created_count += 1

        if dry_run:
            transaction.set_rollback(True)

    return {
        "total_in_backup": len(participants_list),
        "created_count": created_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "is_dry_run": dry_run,
    }
