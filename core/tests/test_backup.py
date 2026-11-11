"""
Tests for Backup and Disaster Recovery Service.
"""
import json
import zipfile
from pathlib import Path
import tempfile
from django.test import TestCase

from core.models import Participant, ExamConfig
from core.services.backup import create_backup, restore_backup, BackupError

class BackupTestCase(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dest_dir = Path(self.temp_dir.name)

        self.config = ExamConfig.get_solo()
        self.config.title = "Mock Imtihon Test"
        self.config.save()

        self.p1 = Participant.objects.create(
            telegram_id=11111,
            telegram_username="user1",
            first_name="Jasur",
            last_name="Rustamov",
            phone_number="+998901112233",
            school_number="15-maktab",
            region="Toshkent shahri",
            district="Yunusobod tumani",
            reg_number="RU-0001",
            is_attended=True
        )
        self.p2 = Participant.objects.create(
            telegram_id=22222,
            telegram_username="user2",
            first_name="Nodira",
            last_name="Aliyeva",
            phone_number="+998934445566",
            school_number="2-IDUM",
            region="Samarqand viloyati",
            district="Samarqand shahri",
            reg_number="RU-0002",
            is_attended=False
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_backup_archive(self):
        result = create_backup(destination_dir=self.dest_dir, include_excel=True)

        self.assertTrue(result['backup_path'].exists())
        self.assertEqual(result['total_participants'], 2)
        self.assertGreater(result['file_size_bytes'], 0)

        # Inspect ZIP contents
        with zipfile.ZipFile(result['backup_path'], 'r') as zf:
            namelist = zf.namelist()
            self.assertTrue(any(f.endswith('.json') for f in namelist))
            self.assertTrue(any(f.endswith('.xlsx') for f in namelist))

            json_name = [f for f in namelist if f.endswith('.json')][0]
            with zf.open(json_name) as jf:
                data = json.load(jf)
                self.assertEqual(data['metadata']['total_participants'], 2)
                self.assertEqual(len(data['participants']), 2)
                reg_numbers = [p['reg_number'] for p in data['participants']]
                self.assertIn("RU-0001", reg_numbers)
                self.assertIn("RU-0002", reg_numbers)

    def test_restore_backup_new_database(self):
        backup_result = create_backup(destination_dir=self.dest_dir)
        zip_path = backup_result['backup_path']

        # Clear participants
        Participant.objects.all().delete()
        self.assertEqual(Participant.objects.count(), 0)

        # Restore
        restore_result = restore_backup(zip_path, overwrite_existing=False, dry_run=False)
        self.assertEqual(restore_result['total_in_backup'], 2)
        self.assertEqual(restore_result['created_count'], 2)
        self.assertEqual(restore_result['skipped_count'], 0)
        self.assertEqual(Participant.objects.count(), 2)

        # Verify restored integrity
        restored_p1 = Participant.objects.get(telegram_id=11111)
        self.assertEqual(restored_p1.reg_number, "RU-0001")
        self.assertEqual(restored_p1.first_name, "Jasur")
        self.assertEqual(restored_p1.last_name, "Rustamov")
        self.assertTrue(restored_p1.is_attended)

    def test_restore_backup_skip_existing(self):
        backup_result = create_backup(destination_dir=self.dest_dir)
        zip_path = backup_result['backup_path']

        # Run restore when records already exist
        restore_result = restore_backup(zip_path, overwrite_existing=False, dry_run=False)
        self.assertEqual(restore_result['created_count'], 0)
        self.assertEqual(restore_result['skipped_count'], 2)

    def test_restore_backup_overwrite_existing(self):
        backup_result = create_backup(destination_dir=self.dest_dir)
        zip_path = backup_result['backup_path']

        # Modify local record
        self.p1.first_name = "O'zgargan Ism"
        self.p1.save()

        # Restore with overwrite=True
        restore_result = restore_backup(zip_path, overwrite_existing=True, dry_run=False)
        self.assertEqual(restore_result['updated_count'], 2)

        self.p1.refresh_from_db()
        self.assertEqual(self.p1.first_name, "Jasur")

    def test_restore_backup_dry_run(self):
        backup_result = create_backup(destination_dir=self.dest_dir)
        zip_path = backup_result['backup_path']

        Participant.objects.all().delete()
        self.assertEqual(Participant.objects.count(), 0)

        restore_result = restore_backup(zip_path, dry_run=True)
        self.assertEqual(restore_result['created_count'], 2)
        self.assertTrue(restore_result['is_dry_run'])

        # DB must still be empty because dry_run rolled back
        self.assertEqual(Participant.objects.count(), 0)

    def test_restore_invalid_path(self):
        with self.assertRaises(BackupError):
            restore_backup(self.dest_dir / "non_existent_file.zip")
