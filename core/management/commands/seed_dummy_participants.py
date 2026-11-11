"""
Management command to seed realistic test participants.
Usage:
    python manage.py seed_dummy_participants --count 15
"""
from django.core.management.base import BaseCommand
from core.models import ExamConfig, Participant
from core.services.registration import register_participant_sync

SAMPLE_STUDENTS = [
    ("Jasur", "Rahimov", "+998901234567", "15-IDUM", "Toshkent shahri", "Yunusobod tumani"),
    ("Madina", "Alimova", "+998911234568", "3-maktab", "Samarqand viloyati", "Samarqand shahri"),
    ("Rustam", "Qodirov", "+998931234569", "42-maktab", "Farg'ona viloyati", "Farg'ona shahri"),
    ("Zilola", "Karimova", "+998941234570", "Prezident maktabi", "Andijon viloyati", "Andijon shahri"),
    ("Bekzod", "Usmonov", "+998951234571", "1-Gimnaziya", "Buxoro viloyati", "Buxoro shahri"),
    ("Nilufar", "Sobirova", "+998971234572", "8-maktab", "Namangan viloyati", "Namangan shahri"),
    ("Sanjar", "Mirzayev", "+998981234573", "21-maktab", "Qashqadaryo viloyati", "Qarshi shahri"),
    ("Dilnoza", "Yoqubova", "+998991234574", "10-maktab", "Xorazm viloyati", "Urganch shahri"),
    ("Farrux", "Toshmatov", "+998331234575", "14-maktab", "Surxondaryo viloyati", "Termiz shahri"),
    ("Shaxnoza", "Nazarova", "+998881234576", "5-maktab", "Jizzax viloyati", "Jizzax shahri"),
    ("Ulug'bek", "G'aniyev", "+998901234577", "9-maktab", "Navoiy viloyati", "Navoiy shahri"),
    ("Malika", "Akbarova", "+998911234578", "2-maktab", "Sirdaryo viloyati", "Guliston shahri"),
    ("Temur", "Ergashev", "+998931234579", "11-maktab", "Qoraqalpog'iston Respublikasi", "Nukus shahri"),
    ("Shahzoda", "Jalilova", "+998941234580", "64-maktab", "Toshkent viloyati", "Chirchiq shahri"),
    ("Otabek", "Sultonov", "+998951234581", "18-IDUM", "Toshkent shahri", "Chilonzor tumani"),
]

class Command(BaseCommand):
    help = "Sinov uchun namunaviy ishtirokchilarni bazaga kiritish."

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=15, help="Qo'shiladigan ishtirokchilar soni")

    def handle(self, *args, **options):
        # Ensure exam config exists with capacity 1000
        config = ExamConfig.get_solo()
        config.is_registration_open = True
        config.max_capacity = 1000
        config.save()

        count = min(options['count'], len(SAMPLE_STUDENTS))
        created_count = 0

        for i in range(count):
            first, last, phone, school, region, district = SAMPLE_STUDENTS[i]
            tid = 900000000 + i

            if Participant.objects.filter(telegram_id=tid).exists():
                continue

            try:
                p = register_participant_sync(
                    telegram_id=tid,
                    first_name=first,
                    last_name=last,
                    phone_number=phone,
                    school_number=school,
                    region=region,
                    district=district,
                    username=f"{first.lower()}_{i}"
                )
                if i % 3 == 0:
                    p.is_attended = True
                    p.save(update_fields=['is_attended'])
                created_count += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Xatolik ({first} {last}): {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"{created_count} nafar test ishtirokchisi muvaffaqiyatli yaratildi!\n"
            f"Jami ishtirokchilar soni: {Participant.objects.count()} ta."
        ))
