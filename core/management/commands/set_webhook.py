"""
Django management command to manage Telegram Webhook.
Usage:
    python manage.py set_webhook
    python manage.py set_webhook --info
    python manage.py set_webhook --delete
    python manage.py set_webhook --url https://your-subdomain.onrender.com/webhook/telegram/
"""
import asyncio
from django.core.management.base import BaseCommand
from django.conf import settings
from bot.loader import get_bot

class Command(BaseCommand):
    help = "Telegram bot webhookini o'rnatish, tekshirish yoki o'chirish"

    def add_arguments(self, parser):
        parser.add_argument('--url', type=str, help='Webhook URL manzili')
        parser.add_argument('--delete', action='store_true', help='Webhookni o\'chirish')
        parser.add_argument('--info', action='store_true', help='Webhook holatini tekshirish')
        parser.add_argument('--drop-pending', action='store_true', help='Kutilayotgan xabarlarni tozalash')

    def handle(self, *args, **options):
        bot_token = getattr(settings, 'BOT_TOKEN', '')
        if not bot_token or 'dummy' in bot_token:
            self.stdout.write(self.style.ERROR("[XATOLIK] BOT_TOKEN sozlanmagan!"))
            return

        bot = get_bot(bot_token)
        target_url = options.get('url') or getattr(settings, 'WEBHOOK_URL', '')

        async def main():
            try:
                if options.get('delete'):
                    await bot.delete_webhook(drop_pending_updates=options.get('drop_pending', False))
                    self.stdout.write(self.style.SUCCESS("Webhook muvaffaqiyatli o'chirildi."))
                    return

                if options.get('info'):
                    info = await bot.get_webhook_info()
                    self.stdout.write(self.style.SUCCESS(f"Webhook ma'lumotlari: URL={info.url}, Pending={info.pending_update_count}, Last Error={info.last_error_message}"))
                    return

                if not target_url:
                    self.stdout.write(self.style.ERROR(
                        "URL ko'rsatilmadi! .env dagi WEBHOOK_URL yoki --url parametridan foydalaning."
                    ))
                    return

                await bot.set_webhook(
                    url=target_url,
                    drop_pending_updates=options.get('drop_pending', True)
                )
                self.stdout.write(self.style.SUCCESS(f"Webhook muvaffaqiyatli o'rnatildi: {target_url}"))
            finally:
                await bot.session.close()

        asyncio.run(main())
