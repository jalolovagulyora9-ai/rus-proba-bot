"""
Django management command to run Telegram Bot in long-polling mode (for local testing).
Usage: python manage.py run_bot
"""
import asyncio
import logging
import sys
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from bot.loader import get_bot, dp

logger = logging.getLogger("bot")

class Command(BaseCommand):
    help = "Telegram botni polling rejimida ishga tushirish (lokal test uchun)"

    def handle(self, *args, **options):
        bot_token = getattr(settings, 'BOT_TOKEN', '')
        if not bot_token or 'dummy' in bot_token or '1234567890:ABCdef' in bot_token:
            self.stdout.write(self.style.ERROR(
                "\n[XATOLIK] BOT_TOKEN sozlanmagan!\n"
                "Iltimos, .env fayliga @BotFather orqali olingan haqiqiy Telegram bot tokeningizni kiriting:\n"
                "BOT_TOKEN=123456789:AAF_haqiqiy_token\n"
            ))
            return

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )

        self.stdout.write(self.style.SUCCESS(
            "\n" + "="*50 + "\n"
            "  RUSSIAN PROBA BOT MUVOFIQ ISHGA TUSHMOQDA...\n"
            "  Rejim: Long-Polling (Mahalliy ishlab chiqish)\n"
            "  To'xtatish uchun: Ctrl + C bosing\n"
            + "="*50 + "\n"
        ))

        bot = get_bot(bot_token)

        async def main():
            # Drop any lingering webhooks or pending updates to avoid conflicts
            await bot.delete_webhook(drop_pending_updates=True)
            self.stdout.write(self.style.SUCCESS("Webhook tozalandi. Polling tinglash boshlandi..."))
            await dp.start_polling(bot)

        try:
            asyncio.run(main())
        except (KeyboardInterrupt, SystemExit):
            self.stdout.write(self.style.WARNING("\nBot to'xtatildi."))
