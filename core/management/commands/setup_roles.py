"""
Management command to create RBAC User Groups and Permissions.
Usage:
    python manage.py setup_roles
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Participant, ExamConfig, BroadcastLog

class Command(BaseCommand):
    help = "Registratorlar va Administratorlar guruhlari va huquqlarini o'rnatish."

    def handle(self, *args, **options):
        # 1. Registratorlar Guruhi
        reg_group, created = Group.objects.get_or_create(name="Registratorlar")
        
        participant_ct = ContentType.objects.get_for_model(Participant)
        config_ct = ContentType.objects.get_for_model(ExamConfig)

        # Desired permissions for Registratorlar
        reg_perms = Permission.objects.filter(
            content_type=participant_ct,
            codename__in=['view_participant', 'change_participant', 'can_export_excel', 'can_mark_attendance']
        ) | Permission.objects.filter(
            content_type=config_ct,
            codename__in=['view_examconfig']
        )

        reg_group.permissions.set(reg_perms)
        self.stdout.write(self.style.SUCCESS(
            f"'{reg_group.name}' guruhi muvaffaqiyatli sozlandi ({reg_perms.count()} ta huquq)."
        ))

        # 2. Administratorlar Guruhi
        admin_group, created = Group.objects.get_or_create(name="Administratorlar")
        all_core_perms = Permission.objects.filter(
            content_type__in=[participant_ct, config_ct, ContentType.objects.get_for_model(BroadcastLog)]
        )
        admin_group.permissions.set(all_core_perms)
        self.stdout.write(self.style.SUCCESS(
            f"'{admin_group.name}' guruhi muvaffaqiyatli sozlandi ({all_core_perms.count()} ta huquq)."
        ))
