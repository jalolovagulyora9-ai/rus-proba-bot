"""
Django management command to restore participants from backup archive or JSON dump.
Usage:
    python manage.py restore_data backups/backup_participants_20261110_180000.zip
    python manage.py restore_data backups/backup_participants_20261110_180000.zip --dry-run
    python manage.py restore_data backups/backup_participants_20261110_180000.zip --overwrite
"""
from django.core.management.base import BaseCommand, CommandError
from core.services.backup import restore_backup, BackupError

class Command(BaseCommand):
    help = "Zaxira faylidan ishtirokchilarni ma'lumotlar bazasiga qayta tiklash"

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help="Tiklanadigan zaxira faylining yo'li (.zip yoki .json)"
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help="Bazadagi mavjud ishtirokchilar ma'lumotlarini zaxiradagisi bilan yangilash"
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Sinov rejimi: bazaga o'zgarish kiritmasdan faqat tekshirish"
        )

    def handle(self, *args, **options):
        file_path = options['backup_file']
        overwrite = options.get('overwrite', False)
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️ SINOV REJIMI (DRY-RUN): Bazaga hech narsa yozilmaydi."))

        try:
            result = restore_backup(
                backup_file_path=file_path,
                overwrite_existing=overwrite,
                dry_run=dry_run
            )
        except BackupError as err:
            raise CommandError(f"Qayta tiklashda xatolik: {err}")
        except Exception as err:
            raise CommandError(f"Kutilmagan xatolik: {err}")

        status_text = "SINOV NATIJALARI (HECH NARSA O'ZGARTIRILMADI)" if dry_run else "MUVAFFAQIYATLI QAYTA TIKLANDI!"

        self.stdout.write(self.style.SUCCESS(
            "\n" + "="*55 + "\n"
            f"  {status_text}\n"
            + "="*55 + "\n"
            f"📦 Zaxiradagi jami qatorlar:  {result['total_in_backup']} ta\n"
            f"✅ Yangi qo'shildi:            {result['created_count']} ta\n"
            f"🔄 Yangilandi:                 {result['updated_count']} ta\n"
            f"⏭️ O'tkazib yuborildi:         {result['skipped_count']} ta\n"
            + "="*55 + "\n"
        ))
