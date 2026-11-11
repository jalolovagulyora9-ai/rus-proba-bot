"""
Web views for RUSSIAN PROBA BOT.
Includes /health/ (monitoring) and /webhook/telegram/ (Telegram updates in production).
"""
import json
import logging
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.conf import settings
from aiogram.types import Update
from bot.loader import dp, get_bot

logger = logging.getLogger(__name__)

def health_check(request):
    """
    Keep-alive and health check endpoint for monitoring (e.g. UptimeRobot, Render).
    Verifies service status and database connectivity.
    """
    db_ok = True
    db_detail = "connected"
    try:
        connection.ensure_connection()
    except Exception as err:
        db_ok = False
        db_detail = f"error: {str(err)}"

    status_code = 200 if db_ok else 503
    return JsonResponse({
        "status": "healthy" if db_ok else "unhealthy",
        "service": "russian_proba_bot",
        "database": db_detail,
    }, status=status_code)


@csrf_exempt
async def telegram_webhook(request):
    """
    Asynchronous Webhook endpoint for Telegram updates.
    Feeds incoming updates into the aiogram 3 Dispatcher.
    """
    if request.method != "POST":
        return HttpResponse("Method Not Allowed. Telegram Webhook requires POST.", status=405)

    # Optional security secret token validation
    expected_secret = getattr(settings, 'TELEGRAM_WEBHOOK_SECRET', '')
    if expected_secret:
        client_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if client_secret != expected_secret:
            logger.warning("Rejected webhook request: Invalid secret token.")
            return HttpResponseForbidden("Forbidden: Invalid secret token.")

    try:
        raw_body = request.body.decode("utf-8")
        if not raw_body:
            return JsonResponse({"ok": False, "error": "Empty body"}, status=400)

        data = json.loads(raw_body)
        bot = get_bot()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot=bot, update=update)
        return JsonResponse({"ok": True})
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)
    except Exception as err:
        logger.error(f"Error processing Telegram webhook update: {err}", exc_info=True)
        # Always return 200 to Telegram to prevent update delivery retry storms
        return JsonResponse({"ok": False, "error": str(err)}, status=200)
