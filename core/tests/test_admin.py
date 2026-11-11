from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from core.models import ExamConfig, Participant
from core.admin import ExamConfigAdmin, ParticipantAdmin

def setup_request(request):
    session_mid = SessionMiddleware(lambda req: None)
    session_mid.process_request(request)
    request.session.save()
    msg_mid = MessageMiddleware(lambda req: None)
    msg_mid.process_request(request)

class MockSuperUser:
    def __init__(self, is_superuser=True):
        self.is_superuser = is_superuser

class AdminTestCase(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staffpassword',
            is_staff=True,
            is_superuser=False
        )

        self.config = ExamConfig.objects.create(
            title="Sinov Imtihon",
            is_registration_open=True,
            max_capacity=500
        )
        self.p1 = Participant.objects.create(
            telegram_id=8001,
            first_name="Anvar",
            last_name="Saidov",
            phone_number="+998901234567",
            school_number="7-maktab",
            region="Toshkent shahri",
            district="Chilonzor tumani",
            reg_number="RU-0001",
            is_attended=False
        )

    def test_exam_config_admin_singleton_protections(self):
        admin_obj = ExamConfigAdmin(ExamConfig, self.site)
        request = self.factory.get('/admin/')
        request.user = self.superuser

        # Should not allow adding second config
        self.assertFalse(admin_obj.has_add_permission(request))
        # Should not allow deleting config
        self.assertFalse(admin_obj.has_delete_permission(request, self.config))

    def test_participant_admin_attendance_actions(self):
        admin_obj = ParticipantAdmin(Participant, self.site)
        request = self.factory.post('/admin/core/participant/')
        request.user = self.superuser
        setup_request(request)

        # Mark attended
        queryset = Participant.objects.filter(id=self.p1.id)
        admin_obj.mark_attended(request, queryset)
        self.p1.refresh_from_db()
        self.assertTrue(self.p1.is_attended)

        # Mark not attended
        admin_obj.mark_not_attended(request, queryset)
        self.p1.refresh_from_db()
        self.assertFalse(self.p1.is_attended)

    def test_participant_admin_excel_export_action(self):
        admin_obj = ParticipantAdmin(Participant, self.site)
        request = self.factory.post('/admin/core/participant/')
        request.user = self.superuser

        queryset = Participant.objects.filter(id=self.p1.id)
        response = admin_obj.export_as_excel(request, queryset)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_participant_admin_delete_permission_superuser_only(self):
        admin_obj = ParticipantAdmin(Participant, self.site)
        
        request_staff = self.factory.get('/admin/')
        request_staff.user = self.staff_user
        self.assertFalse(admin_obj.has_delete_permission(request_staff))

        request_admin = self.factory.get('/admin/')
        request_admin.user = self.superuser
        self.assertTrue(admin_obj.has_delete_permission(request_admin))
