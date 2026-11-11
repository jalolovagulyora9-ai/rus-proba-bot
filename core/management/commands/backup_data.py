"""
Django management command to safely snapshot participants into encrypted/structured backup.
Usage:
    python manage.py backup_data
    python manage.py backup_data --out /custom/path/
"""
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from core.services.backup import create_backup, BackupError

class Command(BaseCommand):
    help = "Barcha ishtirokchilar ma'lumotlarini xavfsiz zaxira nusxa (backup) fayliga saqlash"

    def add_arguments(self, parser):
        parser.add_argument(
            '--out',
            type=str,
            help="Zaxira fayli saqlanadigan maxsus katalog yo'li"
        )
        parser.add_argument(
            '--no-excel',
            action='store_true',
            help="Faqat JSON formatda saqlash (Excel jadvalini kiritmaslik)"
        )

    def handle(self, *args, **options):
        custom_out = Path(options['out']) if options.get('out') else None
        include_excel = not options.get('no_excel', False)

        self.stdout.write("Zaxira nusxa yaratilmoqda...")

        try:
            result = create_backup(
                destination_dir=custom_out,
                include_excel=include_excel
            )
        except BackupError as err:
            raise CommandError(f"Zaxiralashda xatolik: {err}")
        except Exception as err:
            raise CommandError(f"Kutilmagan xatolik: {err}")

        file_size_kb = result['file_size_bytes'] / 1024

        self.stdout.write(self.style.SUCCESS(
            "\n" + "="*55 + "\n"
            "  ZAXIRA NUSXA MUVAFFAQIYATLI YARATILDI! 🎉\n"
            + "="*55 + "\n"
            f"📁 Fayl nomi:       {result['filename']}\n"
            f"📍 To'liq manzil:   {result['backup_path']}\n"
            f"👥 Ishtirokchilar:  {result['total_participants']} nafar\n"
            f"📊 Fayl hajmi:      {file_size_kb:.2f} KB\n"
            f"📅 Vaqti:           {result['created_at']}\n"
            + "="*55 + "\n"
        ))
