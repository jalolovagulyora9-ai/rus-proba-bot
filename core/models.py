from django.db import models
from django.core.exceptions import ValidationError

class ExamConfig(models.Model):
    """
    Singleton configuration model for exam settings.
    Stores dynamic capacity, registration status, and event details.
    """
    title = models.CharField(
        max_length=255,
        default="Rus tili va adabiyoti Milliy sertifikat sinov imtihoni",
        verbose_name="Imtihon nomi"
    )
    is_registration_open = models.BooleanField(
        default=True,
        verbose_name="Ro'yxatga olish ochiqmi?"
    )
    max_capacity = models.PositiveIntegerField(
        default=1000,
        verbose_name="Maksimal o'rinlar sig'imi"
    )
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ro'yxatga olish boshlanish vaqti"
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ro'yxatga olish tugash vaqti"
    )
    exam_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Imtihon o'tkazilish kuni va vaqti"
    )
    exam_location = models.CharField(
        max_length=255,
        default="Mirzo Ulug'bek xususiy maktabi",
        blank=True,
        verbose_name="Imtihon manzili"
    )
    exam_latitude = models.FloatField(
        default=40.619075,
        verbose_name="Kenglik (Latitude)"
    )
    exam_longitude = models.FloatField(
        default=70.982239,
        verbose_name="Uzunlik (Longitude)"
    )
    exam_maps_url = models.URLField(
        default="https://maps.app.goo.gl/2Yo3yHZZzHc8w79v7",
        blank=True,
        verbose_name="Xarita havolasi"
    )
    info_text = models.TextField(
        blank=True,
        verbose_name="Qo'shimcha eslatma / Yo'riqnoma"
    )

    class Meta:
        verbose_name = "Imtihon Sozlamasi"
        verbose_name_plural = "Imtihon Sozlamalari"

    def clean(self):
        super().clean()
        if not self.pk and ExamConfig.objects.exists():
            raise ValidationError("Faqat bitta imtihon sozlamasi mavjud bo'lishi mumkin!")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        """Returns the single configuration row or creates default."""
        obj = cls.objects.first()
        if not obj:
            obj = cls.objects.create()
        return obj

    def __str__(self):
        status = "Ochiq" if self.is_registration_open else "Yopiq"
        return f"{self.title} (Holati: {status}, Sig'im: {self.max_capacity})"


class Participant(models.Model):
    """
    Participant model.
    telegram_id and reg_number are strictly UNIQUE.
    phone_number is indexed but NOT unique to allow families/teachers to use the same contact.
    """
    telegram_id = models.BigIntegerField(
        unique=True,
        db_index=True,
        verbose_name="Telegram ID"
    )
    telegram_username = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Telegram Username"
    )
    first_name = models.CharField(
        max_length=100,
        default="",
        verbose_name="Ismi"
    )
    last_name = models.CharField(
        max_length=100,
        default="",
        verbose_name="Familiyasi"
    )
    phone_number = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name="Telefon raqami"
    )  # UNIQUE EMAS! Indekslangan.
    school_number = models.CharField(
        max_length=100,
        default="",
        blank=True,
        verbose_name="Maktab nomeri / nomi"
    )
    region = models.CharField(
        max_length=100,
        default="Farg'ona",
        blank=True,
        verbose_name="Viloyat"
    )
    district = models.CharField(
        max_length=100,
        default="Mirzo Ulug'bek maktabi",
        blank=True,
        verbose_name="Tuman / Shahar"
    )
    reg_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        verbose_name="Unikal Ro'yxat Raqami"
    )
    is_attended = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Imtihonga keldi"
    )
    bot_blocked = models.BooleanField(
        default=False,
        verbose_name="Botni bloklagan"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ro'yxatdan o'tgan vaqt"
    )

    class Meta:
        verbose_name = "Ishtirokchi"
        verbose_name_plural = "Ishtirokchilar"
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(fields=['telegram_id'], name='unique_participant_telegram_id'),
            models.UniqueConstraint(fields=['reg_number'], name='unique_participant_reg_number'),
        ]
        permissions = [
            ('can_export_excel', 'Ishtirokchilar ro\'yxatini Excel formatida yuklab olish'),
            ('can_mark_attendance', 'Imtihon davomatini belgilash huquqi'),
        ]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.reg_number} - {self.full_name} ({self.school_number})"


class BroadcastLog(models.Model):
    """
    Log of broadcast messages sent to participants.
    """
    message_text = models.TextField(verbose_name="Xabar matni")
    total_recipients = models.PositiveIntegerField(default=0, verbose_name="Jami qabul qiluvchilar")
    sent_count = models.PositiveIntegerField(default=0, verbose_name="Muvaffaqiyatli yetkazildi")
    failed_count = models.PositiveIntegerField(default=0, verbose_name="Yetib bormadi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuborilgan vaqt")

    class Meta:
        verbose_name = "Xabarnoma Tarixi"
        verbose_name_plural = "Xabarnomalar Tarixi"
        ordering = ['-created_at']

    def __str__(self):
        return f"Xabar {self.created_at.strftime('%Y-%m-%d %H:%M')} (Yetkazildi: {self.sent_count}/{self.total_recipients})"
