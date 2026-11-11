"""
Management command to create a local development superuser.
Usage:
    python manage.py create_dev_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "Lokal testlash uchun avtomatik superuser (admin) yaratish."

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Admin foydalanuvchi nomi')
        parser.add_argument('--password', type=str, default='admin123', help='Admin paroli')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']

        user, created = User.objects.get_or_create(username=username)
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(
                f"Superuser '{username}' muvaffaqiyatli yaratildi! Parol: '{password}'"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"Mavjud '{username}' foydalanuvchisiga superuser huquqi berildi va paroli yangilandi ('{password}')."
            ))
