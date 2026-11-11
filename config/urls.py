"""
URL configuration for RUSSIAN PROBA BOT project.
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from core.views import health_check, telegram_webhook

urlpatterns = [
    path(settings.ADMIN_URL_PATH, admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('webhook/telegram/', telegram_webhook, name='telegram_webhook'),
]
