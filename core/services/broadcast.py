"""
Broadcast notification service.
Sends broadcast announcements to registered participants and logs execution.
"""
import asyncio
import logging
from django.utils import timezone
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from core.models import Participant, BroadcastLog
from bot.loader import get_bot

logger = logging.getLogger(__name__)

async def broadcast_message_async(
    message_text: str,
    target_region: str | None = None,
    delay_between_messages: float = 0.05,
    dry_run: bool = False
) -> dict:
    """
    Sends a broadcast message to participants asynchronously.
    Updates bot_blocked flag if a participant blocked the bot.
    Logs broadcast metrics into BroadcastLog model.
    """
    qs = Participant.objects.filter(bot_blocked=False)
    if target_region:
        qs = qs.filter(region=target_region)

    participants = list(qs)
    total_recipients = len(participants)

    if dry_run or total_recipients == 0:
        return {
            "total_recipients": total_recipients,
            "sent_count": 0,
            "failed_count": 0,
            "dry_run": dry_run,
        }

    bot = get_bot()
    sent_count = 0
    failed_count = 0

    try:
        for participant in participants:
            try:
                await bot.send_message(
                    chat_id=participant.telegram_id,
                    text=message_text,
                    parse_mode="HTML"
                )
                sent_count += 1
            except TelegramForbiddenError:
                # User blocked the bot
                participant.bot_blocked = True
                await participant.asave(update_fields=['bot_blocked'])
                failed_count += 1
            except TelegramBadRequest as err:
                logger.warning(f"TelegramBadRequest for user {participant.telegram_id}: {err}")
                failed_count += 1
            except Exception as err:
                logger.error(f"Unexpected error sending to user {participant.telegram_id}: {err}")
                failed_count += 1

            if delay_between_messages > 0:
                await asyncio.sleep(delay_between_messages)
    finally:
        await bot.session.close()

    # Save to BroadcastLog
    await BroadcastLog.objects.acreate(
        message_text=message_text,
        total_recipients=total_recipients,
        sent_count=sent_count,
        failed_count=failed_count
    )

    return {
        "total_recipients": total_recipients,
        "sent_count": sent_count,
        "failed_count": failed_count,
        "dry_run": False,
    }
