"""
Django management command to broadcast messages to participants via Telegram bot.
Usage:
    python manage.py broadcast_message --text "Imtihon qoidalari eslatmasi..."
    python manage.py broadcast_message --text "Farg'ona ishtirokchilariga xabar" --region "Farg'ona viloyati"
    python manage.py broadcast_message --text "Sinov xabari" --dry-run
"""
import asyncio
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from core.services.broadcast import broadcast_message_async

class Command(BaseCommand):
    help = "Ro'yxatdan o'tgan ishtirokchilarga Telegram orqali ommaviy xabarnoma yuborish"

    def add_arguments(self, parser):
        parser.add_argument(
            '--text',
            type=str,
            help="Yuboriladigan xabar matni (HTML formatida)"
        )
        parser.add_argument(
            '--reminder',
            type=int,
            choices=[1, 2],
            help="Imtihon eslatmasi: 2 (2 kun qoldi) yoki 1 (ertaga bo'ladi)"
        )
        parser.add_argument(
            '--region',
            type=str,
            help="Faqat tanlangan viloyat ishtirokchilariga yuborish"
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Sinov rejimi: xabar jo'natmasdan faqat qabul qiluvchilar sonini hisoblash"
        )

    def handle(self, *args, **options):
        text = options.get('text')
        reminder = options.get('reminder')
        region = options.get('region')
        dry_run = options.get('dry_run', False)

        if reminder == 2:
            text = (
                "📢 <b>DIQQAT! SINOV IMTIHONIGA 2 KUN QOLDI!</b>\n\n"
                "Hurmatli ishtirokchi!\n"
                "<b>15-noyabr</b> kuni <b>Mirzo Ulug'bek xususiy maktabida</b> Rus tili va adabiyotidan Milliy sertifikat sinov imtihoni bo'lib o'tadi.\n\n"
                "📍 <b>Manzil:</b> Mirzo Ulug'bek xususiy maktabi\n"
                "🗺 <b>Lokatsiya:</b> https://maps.app.goo.gl/2Yo3yHZZzHc8w79v7\n\n"
                "Iltimos, o'z vaqtida kelishingizni va o'zingiz bilan shaxsingizni tasdiqlovchi hujjat (pasport/ID karta) hamda ruchka olishingizni so'raymiz."
            )
        elif reminder == 1:
            text = (
                "⏳ <b>ESLATMA! IMTIHON ERTAGA BO'LIB O'TADI!</b>\n\n"
                "Hurmatli ishtirokchi!\n"
                "Ertaga, <b>15-noyabr</b> kuni <b>Mirzo Ulug'bek xususiy maktabida</b> Rus tili va adabiyotidan Milliy sertifikat sinov imtihoni o'tkaziladi.\n\n"
                "📍 <b>Manzil:</b> Mirzo Ulug'bek xususiy maktabi\n"
                "🗺 <b>Lokatsiya:</b> https://maps.app.goo.gl/2Yo3yHZZzHc8w79v7\n\n"
                "Barchangizga imtihonda omad va yuqori natijalar tilaymiz!"
            )
        elif not text:
            raise CommandError("Yo --text parametri orqali matn kiriting, yoki --reminder 1 / --reminder 2 tanlang!")

        bot_token = getattr(settings, 'BOT_TOKEN', '')
        if not dry_run and (not bot_token or 'dummy' in bot_token or '1234567890:ABCdef' in bot_token):
            raise CommandError("BOT_TOKEN sozlanmagan! Haqiqiy xabar yuborish uchun .env ga bot tokenini kiriting.")

        self.stdout.write("Xabarnoma tayyorlanmoqda...")

        async def run_broadcast():
            return await broadcast_message_async(
                message_text=text,
                target_region=region,
                dry_run=dry_run
            )

        result = asyncio.run(run_broadcast())

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\n[SINOV REJIMI] Jami {result['total_recipients']} ta ishtirokchiga xabar borishi mumkin edi. Hech narsa yuborilmadi."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "\n" + "="*50 + "\n"
                "  XABAR YUBORISH YAKUNLANDI!\n"
                + "="*50 + "\n"
                f"👥 Jami qabul qiluvchilar: {result['total_recipients']} ta\n"
                f"✅ Yetkazildi:             {result['sent_count']} ta\n"
                f"❌ Yetib bormadi (blok):   {result['failed_count']} ta\n"
                + "="*50 + "\n"
            ))
