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
            "fields": ("start_date", "end_date", "exam_date", "exam_location"),
            "description": "7 kunlik ro'yxatga olish oynasi va imtihon o'tkaziladigan sana/manzil."
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
    actions = ['export_as_excel', 'mark_attended', 'mark_not_attended']

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
