from django.test import TestCase
from core.models import ExamConfig, Participant
from core.services.registration import (
    register_participant_sync,
    RegistrationClosedError,
    CapacityExceededError,
    AlreadyRegisteredError
)

class RegistrationServiceTestCase(TestCase):
    def setUp(self):
        self.config = ExamConfig.objects.create(
            title="Sinov Imtihoni 2026",
            is_registration_open=True,
            max_capacity=3
        )

    def test_successful_registration_with_full_name(self):
        p1 = register_participant_sync(
            telegram_id=1001,
            full_name="Jasur Rahimov",
            phone_number="+998901234567",
            school_number="15-maktab",
            region="Toshkent shahri",
            district="Yunusobod tumani",
            username="jasur_r"
        )
        self.assertEqual(p1.telegram_id, 1001)
        self.assertEqual(p1.first_name, "Jasur")
        self.assertEqual(p1.last_name, "Rahimov")
        self.assertEqual(p1.full_name, "Jasur Rahimov")
        self.assertEqual(p1.school_number, "15-maktab")
        self.assertEqual(p1.reg_number, "RU-0001")
        self.assertEqual(Participant.objects.count(), 1)

    def test_successful_registration_with_separate_names(self):
        p = register_participant_sync(
            telegram_id=1005,
            first_name="Dilnoza",
            last_name="Karimova",
            phone_number="+998901234567",
            school_number="42-IDUM",
            region="Samarqand viloyati",
            district="Samarqand shahri"
        )
        self.assertEqual(p.first_name, "Dilnoza")
        self.assertEqual(p.last_name, "Karimova")
        self.assertEqual(p.school_number, "42-IDUM")

    def test_sequential_registration_numbers(self):
        p1 = register_participant_sync(
            telegram_id=1001,
            full_name="Jasur Rahimov",
            phone_number="+998901234567",
            school_number="15",
            region="Toshkent shahri",
            district="Yunusobod tumani"
        )
        p2 = register_participant_sync(
            telegram_id=1002,
            full_name="Nodira Aliyeva",
            phone_number="+998911234567",
            school_number="28",
            region="Samarqand viloyati",
            district="Samarqand shahri"
        )
        self.assertEqual(p1.reg_number, "RU-0001")
        self.assertEqual(p2.reg_number, "RU-0002")

    def test_duplicate_telegram_id_rejected(self):
        register_participant_sync(
            telegram_id=1001,
            full_name="Jasur Rahimov",
            phone_number="+998901234567",
            region="Toshkent shahri",
            district="Yunusobod tumani"
        )
        with self.assertRaises(AlreadyRegisteredError):
            register_participant_sync(
                telegram_id=1001,
                full_name="Boshqa Ism",
                phone_number="+998939998877",
                region="Buxoro viloyati",
                district="Buxoro shahri"
            )

    def test_shared_phone_number_allowed(self):
        p1 = register_participant_sync(
            telegram_id=1001,
            full_name="Jasur Rahimov",
            phone_number="+998901234567",
            region="Toshkent shahri",
            district="Yunusobod tumani"
        )
        p2 = register_participant_sync(
            telegram_id=1002,
            full_name="Botir Rahimov",
            phone_number="+998901234567",
            region="Toshkent shahri",
            district="Yunusobod tumani"
        )
        self.assertEqual(p1.phone_number, p2.phone_number)
        self.assertEqual(Participant.objects.count(), 2)

    def test_capacity_exceeded_rejected(self):
        names = ["Ali Valiyev", "Hasan Usmonov", "Zuhra Karimova"]
        for i, name in enumerate(names, start=1):
            register_participant_sync(
                telegram_id=2000 + i,
                full_name=name,
                phone_number=f"+99890123456{i}",
                region="Toshkent shahri",
                district="Chilonzor tumani"
            )

        self.assertEqual(Participant.objects.count(), 3)

        with self.assertRaises(CapacityExceededError):
            register_participant_sync(
                telegram_id=9999,
                full_name="Dilshod Saidov",
                phone_number="+998909999999",
                region="Toshkent shahri",
                district="Chilonzor tumani"
            )

    def test_registration_closed_rejected(self):
        self.config.is_registration_open = False
        self.config.save()

        with self.assertRaises(RegistrationClosedError):
            register_participant_sync(
                telegram_id=3001,
                full_name="Kechikkan Talaba",
                phone_number="+998901112233",
                region="Farg'ona viloyati",
                district="Farg'ona shahri"
            )
