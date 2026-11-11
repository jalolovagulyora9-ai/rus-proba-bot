import io
import openpyxl
from django.test import TestCase
from core.models import Participant
from core.services.export import export_participants_to_excel

class ExcelExportTestCase(TestCase):
    def setUp(self):
        self.p1 = Participant.objects.create(
            telegram_id=7001,
            first_name="Jasur",
            last_name="Rustamov",
            phone_number="+998901234567",
            school_number="15-maktab",
            region="Toshkent shahri",
            district="Yunusobod tumani",
            reg_number="RU-0001",
            is_attended=True
        )
        self.p2 = Participant.objects.create(
            telegram_id=7002,
            first_name="Madina",
            last_name="Alimova",
            phone_number="+998911234567",
            school_number="3-IDUM",
            region="Samarqand viloyati",
            district="Samarqand shahri",
            reg_number="RU-0002",
            is_attended=False
        )

    def test_excel_export_structure_and_content(self):
        queryset = Participant.objects.all().order_by('id')
        response = export_participants_to_excel(queryset)

        # Assert response headers
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertTrue('attachment; filename="ishtirokchilar_' in response['Content-Disposition'])

        # Load generated workbook from response binary content
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        self.assertIn("Ishtirokchilar", wb.sheetnames)
        ws = wb["Ishtirokchilar"]

        # Assert Header row (Row 1)
        expected_headers = [
            "№",
            "ID Raqami",
            "Ism",
            "Familiya",
            "Telefon Raqami",
            "Maktab Nomeri",
            "Viloyat",
            "Tuman / Shahar",
            "Imtihonga Keldi",
            "Ro'yxatdan O'tgan Vaqt"
        ]
        actual_headers = [cell.value for cell in ws[1]]
        self.assertEqual(actual_headers, expected_headers)

        # Assert Row 2 (p1)
        row2 = [cell.value for cell in ws[2]]
        self.assertEqual(row2[0], 1)
        self.assertEqual(row2[1], "RU-0001")
        self.assertEqual(row2[2], "Jasur")
        self.assertEqual(row2[3], "Rustamov")
        self.assertEqual(row2[4], "+998901234567")
        self.assertEqual(row2[5], "15-maktab")
        self.assertEqual(row2[6], "Toshkent shahri")
        self.assertEqual(row2[7], "Yunusobod tumani")
        self.assertEqual(row2[8], "Ha")

        # Assert Row 3 (p2)
        row3 = [cell.value for cell in ws[3]]
        self.assertEqual(row3[0], 2)
        self.assertEqual(row3[1], "RU-0002")
        self.assertEqual(row3[2], "Madina")
        self.assertEqual(row3[3], "Alimova")
        self.assertEqual(row3[4], "+998911234567")
        self.assertEqual(row3[5], "3-IDUM")
        self.assertEqual(row3[6], "Samarqand viloyati")
        self.assertEqual(row3[7], "Samarqand shahri")
        self.assertEqual(row3[8], "Yo'q")
