import unittest
import concurrent.futures
from django.db import connection
from django.test import TransactionTestCase
from core.models import ExamConfig, Participant
from core.services.registration import register_participant_sync, CapacityExceededError

class ConcurrencyTestCase(TransactionTestCase):
    """
    Tests multi-threaded concurrent registration requests against capacity limit.
    Note: SQLite locks the entire database file during writes, so multi-threaded
    write concurrency tests require a client-server RDBMS like PostgreSQL.
    """
    def setUp(self):
        self.config = ExamConfig.objects.create(
            title="Konkurentlik Sinovi",
            is_registration_open=True,
            max_capacity=3
        )

    @unittest.skipIf(
        connection.vendor == 'sqlite',
        "SQLite butun bazani yozishda bloklaydi. Konkurentlik testi PostgreSQL talab qiladi."
    )
    def test_concurrent_registrations_limit(self):
        # 10 concurrent threads trying to take 3 available seats
        total_attempts = 10
        success_count = 0
        capacity_error_count = 0

        names = [
            "Ali Valiyev", "Vali Aliyev", "Hasan Usmonov", "Husan Usmonov",
            "Anvar Soliyev", "Sardor Qodirov", "Botir Zokirov", "Nodir Karimov",
            "Shavkat Rahimov", "Temur Po'latov"
        ]

        def attempt_registration(idx):
            return register_participant_sync(
                telegram_id=5000 + idx,
                full_name=names[idx],
                phone_number=f"+9989011122{idx:02d}",
                region="Toshkent shahri",
                district="Yunusobod tumani"
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(attempt_registration, i) for i in range(total_attempts)]
            for future in concurrent.futures.as_completed(futures):
                try:
                    p = future.result()
                    if p:
                        success_count += 1
                except CapacityExceededError:
                    capacity_error_count += 1

        # Exactly 3 must succeed, exactly 7 must be rejected
        self.assertEqual(success_count, 3)
        self.assertEqual(capacity_error_count, 7)
        self.assertEqual(Participant.objects.count(), 3)

        # Registration numbers must be distinct
        reg_numbers = list(Participant.objects.values_list('reg_number', flat=True))
        self.assertEqual(len(set(reg_numbers)), 3)
