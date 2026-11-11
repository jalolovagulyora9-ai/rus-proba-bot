"""
Django Admin configuration for RUSSIAN PROBA BOT.
Provides rich search, filters, one-click attendance check-in, and Excel export.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from core.models import ExamConfig, Participant, BroadcastLog
from core.services.export import export_participants_to_excel

# Customize Admin Site Branding
admin.site.site_header = "Russian National Certificate — Mock Exam Admin"
admin.site.site_title = "Mock Exam Boshqaruv Paneli"
admin.site.index_title = "Boshqaruv Paneli va Statistika"


@admin.register(ExamConfig)
class ExamConfigAdmin(admin.ModelAdmin):
    """
    Singleton admin interface for ExamConfig.
    Prevents duplicate configuration records and deletion of settings.
    """
    list_display = (
        'title',
        'status_badge',
        'max_capacity',
        'current_registered_count',
        'exam_date',
        'exam_location'
    )
    fieldsets = (
        ("Asosiy Imtihon Sozlamalari", {
            "fields": ("title", "is_registration_open", "max_capacity"),
            "description": "Ro'yxatdan o'tish holati va ishtirokchilar maksimal o'rinlar soni."
        }),
        ("Muddatlar va Joylashuv", {
            "fields": ("start_date", "end_date", "exam_date", "exam_location", "exam_latitude", "exam_longitude", "exam_maps_url"),
            "description": "Imtihon o'tkaziladigan sana, manzil, GPS koordinatalar va xarita havolasi."
        }),
        ("Qo'shimcha Xabar", {
            "fields": ("info_text",),
            "description": "Muvaffaqiyatli ro'yxatdan o'tgan nomzodga Telegram orqali yuboriladigan eslatma."
        }),
    )

    def has_add_permission(self, request):
        # Disallow adding more than one configuration
        if ExamConfig.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Protect singleton from accidental deletion
        return False

    @admin.display(description="Ro'yxat Holati")
    def status_badge(self, obj):
        if obj.is_registration_open:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 4px; font-weight: bold;">OCHIQ</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 4px; font-weight: bold;">YOPIQ</span>'
        )

    @admin.display(description="Hozirgi Ro'yxatdan O'tganlar")
    def current_registered_count(self, obj):
        count = Participant.objects.count()
        percent = (count / obj.max_capacity * 100) if obj.max_capacity else 0
        return format_html(f"<strong>{count}</strong> / {obj.max_capacity} ({percent:.1f}%)")


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    """
    Comprehensive admin interface for registered participants.
    Supports search, filtering, inline attendance marking, and Excel export.
    """
    list_display = (
        'reg_number',
        'first_name',
        'last_name',
        'phone_number',
        'school_number',
        'region',
        'district',
        'is_attended',
        'created_at'
    )
    list_display_links = ('reg_number', 'first_name', 'last_name')
    list_editable = ('is_attended',)  # One-click check-in at the exam entrance
    list_filter = ('is_attended', 'region', 'created_at')
    search_fields = (
        'reg_number',
        'first_name',
        'last_name',
        'phone_number',
        'school_number',
        'district',
        'telegram_id',
        'telegram_username'
    )
    readonly_fields = ('reg_number', 'telegram_id', 'telegram_username', 'created_at')
    actions = ['export_as_excel', 'send_reminder_2_days', 'send_reminder_1_day', 'mark_attended', 'mark_not_attended']

    fieldsets = (
        ("Ishtirokchi Ma'lumotlari", {
            "fields": ("reg_number", "first_name", "last_name", "phone_number", "school_number")
        }),
        ("Hududiy Ma'lumotlar", {
            "fields": ("region", "district")
        }),
        ("Imtihon Davomati", {
            "fields": ("is_attended",)
        }),
        ("Telegram Ma'lumotlari (Audit)", {
            "fields": ("telegram_id", "telegram_username", "bot_blocked", "created_at"),
            "classes": ("collapse",)
        }),
    )

    @admin.action(description="📢 Tanlanganlarga 'Imtihonga 2 kun qoldi' eslatmasini yuborish")
    def send_reminder_2_days(self, request, queryset):
        import asyncio
        from core.services.broadcast import broadcast_message_async
        msg = (
            "📢 <b>DIQQAT! SINOV IMTIHONIGA 2 KUN QOLDI!</b>\n\n"
            "Hurmatli ishtirokchi!\n"
            "<b>15-noyabr</b> kuni <b>Mirzo Ulug'bek xususiy maktabida</b> Rus tili va adabiyotidan Milliy sertifikat sinov imtihoni bo'lib o'tadi.\n\n"
            "📍 <b>Manzil:</b> Mirzo Ulug'bek xususiy maktabi\n"
            "🗺 <b>Lokatsiya:</b> https://maps.app.goo.gl/2Yo3yHZZzHc8w79v7\n\n"
            "Iltimos, o'z vaqtida kelishingizni va o'zingiz bilan shaxsingizni tasdiqlovchi hujjat (pasport/ID karta) hamda ruchka olishingizni so'raymiz."
        )
        try:
            res = asyncio.run(broadcast_message_async(message_text=msg, participants=list(queryset)))
            self.message_user(request, f"Eslatma {res['sent_count']} nafar ishtirokchiga muvaffaqiyatli yuborildi!", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Xatolik yuz berdi: {e}", messages.ERROR)

    @admin.action(description="⏳ Tanlanganlarga 'Imtihonga 1 kun qoldi' eslatmasini yuborish")
    def send_reminder_1_day(self, request, queryset):
        import asyncio
        from core.services.broadcast import broadcast_message_async
        msg = (
            "⏳ <b>ESLATMA! IMTIHON ERTAGA BO'LIB O'TADI!</b>\n\n"
            "Hurmatli ishtirokchi!\n"
            "Ertaga, <b>15-noyabr</b> kuni <b>Mirzo Ulug'bek xususiy maktabida</b> Rus tili va adabiyotidan Milliy sertifikat sinov imtihoni o'tkaziladi.\n\n"
            "📍 <b>Manzil:</b> Mirzo Ulug'bek xususiy maktabi\n"
            "🗺 <b>Lokatsiya:</b> https://maps.app.goo.gl/2Yo3yHZZzHc8w79v7\n\n"
            "Imtihonda barchangizga omad va yuqori natijalar tilaymiz!"
        )
        try:
            res = asyncio.run(broadcast_message_async(message_text=msg, participants=list(queryset)))
            self.message_user(request, f"Eslatma {res['sent_count']} nafar ishtirokchiga muvaffaqiyatli yuborildi!", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Xatolik yuz berdi: {e}", messages.ERROR)

    @admin.action(description="Tanlangan ishtirokchilarni Excel formatida yuklab olish")
    def export_as_excel(self, request, queryset):
        """Action to export selected participants into openpyxl Excel spreadsheet."""
        return export_participants_to_excel(queryset, filename_prefix="mock_imtihon_ishtirokchilari")

    @admin.action(description="Tanlanganlarni 'Imtihonga keldi' deb belgilash")
    def mark_attended(self, request, queryset):
        updated = queryset.update(is_attended=True)
        self.message_user(
            request,
            f"{updated} nafar ishtirokchi 'Imtihonga keldi' deb belgilandi.",
            messages.SUCCESS
        )

    @admin.action(description="Tanlanganlarni 'Kelmagan' deb belgilash")
    def mark_not_attended(self, request, queryset):
        updated = queryset.update(is_attended=False)
        self.message_user(
            request,
            f"{updated} nafar ishtirokchi 'Kelmagan' deb belgilandi.",
            messages.INFO
        )

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete participant records
        return request.user.is_superuser


@admin.register(BroadcastLog)
class BroadcastLogAdmin(admin.ModelAdmin):
    """
    Readonly audit log of Telegram broadcast campaigns.
    """
    list_display = ('id', 'short_message', 'total_recipients', 'sent_count', 'failed_count', 'created_at')
    readonly_fields = ('message_text', 'total_recipients', 'sent_count', 'failed_count', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    @admin.display(description="Xabar Matni")
    def short_message(self, obj):
        if len(obj.message_text) > 60:
            return f"{obj.message_text[:60]}..."
        return obj.message_text
