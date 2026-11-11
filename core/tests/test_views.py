"""
Tests for Web Views (/health/ and /webhook/telegram/).
Uses pure-Python trampoline runner for async webhook view testing.
"""
import inspect
import json
from unittest.mock import AsyncMock, MagicMock, patch
from django.test import TestCase, Client
from core.views import health_check, telegram_webhook

def run_coro_sync(coro):
    """Executes a coroutine synchronously by stepping through it without an event loop."""
    stack = [coro]
    result = None
    while stack:
        curr = stack[-1]
        try:
            yielded = curr.send(result)
            if inspect.iscoroutine(yielded):
                stack.append(yielded)
                result = None
            else:
                result = yielded
        except StopIteration as exc:
            stack.pop()
            result = exc.value
    return result


class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check_endpoint(self):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'russian_proba_bot')
        self.assertEqual(data['database'], 'connected')

    def test_telegram_webhook_get_rejected(self):
        req = MagicMock(method="GET")
        response = run_coro_sync(telegram_webhook(req))
        self.assertEqual(response.status_code, 405)

    def test_telegram_webhook_invalid_json(self):
        req = MagicMock(method="POST", body=b"not a valid json")
        response = run_coro_sync(telegram_webhook(req))
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content.decode('utf-8'))
        self.assertFalse(data['ok'])

    def test_telegram_webhook_empty_body(self):
        req = MagicMock(method="POST", body=b"")
        response = run_coro_sync(telegram_webhook(req))
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content.decode('utf-8'))
        self.assertFalse(data['ok'])

    def test_telegram_webhook_valid_update(self):
        dummy_update_payload = {
            "update_id": 999999,
            "message": {
                "message_id": 1,
                "date": 1700000000,
                "chat": {"id": 12345, "type": "private"},
                "from": {"id": 12345, "is_bot": False, "first_name": "Test"},
                "text": "/start"
            }
        }
        req = MagicMock(
            method="POST",
            body=json.dumps(dummy_update_payload).encode('utf-8')
        )

        with patch('bot.loader.dp.feed_update', new_callable=AsyncMock) as mock_feed:
            mock_feed.return_value = None
            response = run_coro_sync(telegram_webhook(req))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertTrue(data['ok'])
        mock_feed.assert_called_once()
