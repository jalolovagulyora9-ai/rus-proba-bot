"""
Unit and integration tests for Telegram Bot, FSM states, services, and keyboards.
Tests all handlers, transitions, validations, and ticket formatting.
Uses a zero-dependency coroutine trampoline runner for pure in-memory execution.
"""
import inspect
from unittest.mock import AsyncMock, MagicMock, patch
from django.test import SimpleTestCase

from core.models import Participant
from bot.states import RegistrationStates
from bot.utils.regions import (
    get_region_list,
    get_region_by_index,
    get_region_index,
    get_districts_by_region,
    get_district_by_index,
)
from bot.keyboards import (
    get_main_menu_keyboard,
    get_phone_keyboard,
    get_cancel_keyboard,
    get_regions_inline_keyboard,
    get_districts_inline_keyboard,
    get_confirmation_inline_keyboard,
)
from bot.services import format_participant_ticket
from bot.handlers.common import (
    cmd_start,
    cmd_cancel,
    cb_cancel_reg,
    cmd_my_id,
    cmd_help,
)
from bot.handlers.registration import (
    start_registration_msg,
    process_full_name,
    process_phone_number,
    process_region_selection,
    back_to_regions,
    process_district_selection,
    process_school_number,
    restart_registration,
    execute_registration,
)
from core.services.registration import (
    AlreadyRegisteredError,
    CapacityExceededError,
)


def run_coro_sync(coro):
    """
    Pure-Python stack trampoline coroutine runner.
    Executes async coroutines synchronously without relying on OS loopback sockets.
    """
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


class MockFSMContext:
    """Mock FSMContext implementing state and data management for aiogram 3."""
    def __init__(self, current_state=None, data=None):
        self._state = current_state.state if hasattr(current_state, 'state') else current_state
        self._data = data or {}

    async def get_state(self):
        return self._state

    async def set_state(self, state):
        self._state = state.state if hasattr(state, 'state') else state

    async def get_data(self):
        return self._data.copy()

    async def update_data(self, **kwargs):
        self._data.update(kwargs)

    async def clear(self):
        self._state = None
        self._data = {}


class BotUtilsTestCase(SimpleTestCase):
    def test_region_helpers(self):
        regions = get_region_list()
        self.assertEqual(len(regions), 14)
        self.assertIn("Toshkent shahri", regions)
        self.assertIn("Samarqand viloyati", regions)

        first_region = get_region_by_index(0)
        self.assertEqual(first_region, regions[0])

        idx = get_region_index(first_region)
        self.assertEqual(idx, 0)
        self.assertIsNone(get_region_by_index(999))
        self.assertIsNone(get_region_index("Mavjud bo'lmagan hudud"))

    def test_district_helpers(self):
        tashkent_districts = get_districts_by_region("Toshkent shahri")
        self.assertGreater(len(tashkent_districts), 5)
        self.assertIn("Chilonzor tumani", tashkent_districts)

        first_district = get_district_by_index("Toshkent shahri", 0)
        self.assertEqual(first_district, tashkent_districts[0])
        self.assertIsNone(get_district_by_index("Toshkent shahri", 999))
        self.assertEqual(get_districts_by_region("Mavjud bo'lmagan hudud"), [])


class BotKeyboardsTestCase(SimpleTestCase):
    def test_reply_keyboards(self):
        kb_unregistered = get_main_menu_keyboard(is_registered=False)
        self.assertEqual(kb_unregistered.keyboard[0][0].text, "📝 Ro'yxatdan o'tish")

        kb_registered = get_main_menu_keyboard(is_registered=True)
        self.assertEqual(kb_registered.keyboard[0][0].text, "🎫 Mening chiptam")

        phone_kb = get_phone_keyboard()
        self.assertTrue(phone_kb.keyboard[0][0].request_contact)
        self.assertEqual(phone_kb.keyboard[1][0].text, "❌ Bekor qilish")

        cancel_kb = get_cancel_keyboard()
        self.assertEqual(cancel_kb.keyboard[0][0].text, "❌ Bekor qilish")

    def test_inline_keyboards(self):
        reg_kb = get_regions_inline_keyboard()
        self.assertGreaterEqual(len(reg_kb.inline_keyboard), 7)

        dist_kb = get_districts_inline_keyboard("Toshkent shahri")
        self.assertGreaterEqual(len(dist_kb.inline_keyboard), 2)
        has_back_button = any(
            btn.callback_data == "back_to_regions"
            for row in dist_kb.inline_keyboard for btn in row
        )
        self.assertTrue(has_back_button)

        conf_kb = get_confirmation_inline_keyboard()
        btn_callbacks = [btn.callback_data for row in conf_kb.inline_keyboard for btn in row]
        self.assertIn("confirm_reg", btn_callbacks)
        self.assertIn("restart_reg", btn_callbacks)
        self.assertIn("cancel_reg", btn_callbacks)


class BotTicketFormattingTestCase(SimpleTestCase):
    def test_format_participant_ticket(self):
        p = Participant(
            telegram_id=987,
            first_name="Madina",
            last_name="Alimova",
            phone_number="+998931112233",
            school_number="Mirzo Ulug'bek xususiy maktabi",
            region="Farg'ona",
            district="Mirzo Ulug'bek maktabi",
            reg_number="RU-0042"
        )
        ticket = format_participant_ticket(p)
        self.assertIn("RU-0042", ticket)
        self.assertIn("Madina Alimova", ticket)
        self.assertIn("+998931112233", ticket)
        self.assertIn("15-noyabr", ticket)
        self.assertIn("Mirzo Ulug'bek xususiy maktabi", ticket)


class BotFSMHandlersTestCase(SimpleTestCase):
    def setUp(self):
        self.mock_exam_open = {
            "title": "Rus tili va adabiyoti Milliy sertifikat sinov imtihoni",
            "is_open": True,
            "is_full": False,
            "max_capacity": 1000,
            "current_count": 50,
            "start_date": None,
            "end_date": None,
            "exam_date": None,
            "exam_location": "Toshkent shahri",
            "info_text": "Yo'riqnoma",
        }

    def test_cmd_start_unregistered(self):
        message = MagicMock()
        message.from_user.id = 10101
        message.from_user.full_name = "Test User"
        message.answer = AsyncMock()
        message.answer_photo = AsyncMock()
        state = MockFSMContext()

        with patch('bot.handlers.common.get_participant_by_telegram_id', new_callable=AsyncMock, return_value=None), \
             patch('bot.handlers.common.get_exam_status', new_callable=AsyncMock, return_value=self.mock_exam_open):
            run_coro_sync(cmd_start(message, state))

        # Checks that promo banner/caption was sent
        if message.answer_photo.called:
            caption = message.answer_photo.call_args[1].get('caption', '')
            self.assertIn("Jalolov Asrorjon", caption)
        else:
            args, kwargs = message.answer.call_args_list[0]
            self.assertIn("Jalolov Asrorjon", args[0])

    def test_cmd_start_registered(self):
        dummy_participant = Participant(
            telegram_id=20202,
            first_name="Dilnoza",
            last_name="Karimova",
            phone_number="+998901112233",
            school_number="7-maktab",
            region="Toshkent viloyati",
            district="Chirchiq shahri",
            reg_number="RU-0001"
        )
        message = MagicMock()
        message.from_user.id = 20202
        message.from_user.full_name = "Dilnoza Karimova"
        message.answer = AsyncMock()
        state = MockFSMContext()

        with patch('bot.handlers.common.get_participant_by_telegram_id', new_callable=AsyncMock, return_value=dummy_participant), \
             patch('bot.handlers.common.get_exam_status', new_callable=AsyncMock, return_value=self.mock_exam_open):
            run_coro_sync(cmd_start(message, state))

        message.answer.assert_called_once()
        args, kwargs = message.answer.call_args
        self.assertIn("allaqachon", args[0])
        self.assertIn("RU-0001", args[0])

    def test_cmd_cancel(self):
        message = MagicMock()
        message.from_user.id = 30303
        message.answer = AsyncMock()
        state = MockFSMContext(current_state=RegistrationStates.full_name)

        with patch('bot.handlers.common.get_participant_by_telegram_id', new_callable=AsyncMock, return_value=None):
            run_coro_sync(cmd_cancel(message, state))

        current_state = run_coro_sync(state.get_state())
        self.assertIsNone(current_state)
        self.assertIn("bekor qilindi", message.answer.call_args[0][0])

    def test_cb_cancel_reg(self):
        callback = MagicMock()
        callback.from_user.id = 30303
        callback.answer = AsyncMock()
        callback.message.delete = AsyncMock()
        callback.message.answer = AsyncMock()
        state = MockFSMContext(current_state=RegistrationStates.confirm)

        with patch('bot.handlers.common.get_participant_by_telegram_id', new_callable=AsyncMock, return_value=None):
            run_coro_sync(cb_cancel_reg(callback, state))

        self.assertIsNone(run_coro_sync(state.get_state()))
        callback.message.answer.assert_called_once()
        self.assertIn("bekor qilindi", callback.message.answer.call_args[0][0])

    def test_cmd_my_id_registered(self):
        dummy_participant = Participant(
            telegram_id=40404,
            first_name="Jasur",
            last_name="Rustamov",
            phone_number="+998901234567",
            school_number="15-maktab",
            region="Toshkent shahri",
            district="Yunusobod tumani",
            reg_number="RU-0015"
        )
        message = MagicMock()
        message.from_user.id = 40404
        message.answer = AsyncMock()

        with patch('bot.handlers.common.get_participant_by_telegram_id', new_callable=AsyncMock, return_value=dummy_participant), \
             patch('bot.handlers.common.get_exam_status', new_callable=AsyncMock, return_value=self.mock_exam_open):
            run_coro_sync(cmd_my_id(message))

        self.assertGreaterEqual(message.answer.call_count, 1)
        self.assertIn("RU-0015", message.answer.call_args_list[0][0][0])

    def test_cmd_help(self):
        message = MagicMock()
        message.from_user.id = 50505
        message.answer = AsyncMock()

        with patch('bot.handlers.common.get_participant_by_telegram_id', new_callable=AsyncMock, return_value=None), \
             patch('bot.handlers.common.get_exam_status', new_callable=AsyncMock, return_value=self.mock_exam_open):
            run_coro_sync(cmd_help(message))

        message.answer.assert_called_once()
        self.assertIn("Jalolov Asrorjon", message.answer.call_args[0][0])

    def test_full_fsm_registration_flow(self):
        user_id = 60606
        state = MockFSMContext()

        # 1. Start registration
        msg_start = MagicMock()
        msg_start.from_user.id = user_id
        msg_start.from_user.full_name = "Botir Zokirov"
        msg_start.answer = AsyncMock()

        with patch('bot.handlers.registration.get_participant_by_telegram_id', new_callable=AsyncMock, return_value=None), \
             patch('bot.handlers.registration.get_exam_status', new_callable=AsyncMock, return_value=self.mock_exam_open):
            run_coro_sync(start_registration_msg(msg_start, state))

        self.assertEqual(run_coro_sync(state.get_state()), RegistrationStates.full_name.state)

        # 2. Step 1: Full name (invalid -> valid)
        msg_name_invalid = MagicMock()
        msg_name_invalid.text = "Botir"  # single word
        msg_name_invalid.answer = AsyncMock()
        run_coro_sync(process_full_name(msg_name_invalid, state))
        self.assertEqual(run_coro_sync(state.get_state()), RegistrationStates.full_name.state)

        msg_name_valid = MagicMock()
        msg_name_valid.text = "Botir Zokirov"
        msg_name_valid.answer = AsyncMock()
        run_coro_sync(process_full_name(msg_name_valid, state))
        self.assertEqual(run_coro_sync(state.get_state()), RegistrationStates.phone_number.state)
        data = run_coro_sync(state.get_data())
        self.assertEqual(data["first_name"], "Botir")
        self.assertEqual(data["last_name"], "Zokirov")

        # 3. Step 2: Phone number via contact -> moves directly to confirm!
        msg_ph = MagicMock()
        msg_ph.contact = MagicMock()
        msg_ph.contact.phone_number = "998909876543"
        msg_ph.text = None
        msg_ph.answer = AsyncMock()
        run_coro_sync(process_phone_number(msg_ph, state))
        self.assertEqual(run_coro_sync(state.get_state()), RegistrationStates.confirm.state)
        data = run_coro_sync(state.get_data())
        self.assertEqual(data["phone_number"], "+998909876543")

        # 4. Step 3: Confirm registration callback
        dummy_registered = Participant(
            telegram_id=user_id,
            first_name="Botir",
            last_name="Zokirov",
            phone_number="+998909876543",
            school_number="Mirzo Ulug'bek maktabi",
            region="Farg'ona",
            district="Mirzo Ulug'bek maktabi",
            reg_number="RU-0007"
        )
        cb_conf = MagicMock()
        cb_conf.from_user.id = user_id
        cb_conf.from_user.username = "botir_z"
        cb_conf.answer = AsyncMock()
        cb_conf.message.delete = AsyncMock()
        cb_conf.message.answer = AsyncMock()
        cb_conf.message.answer_location = AsyncMock()

        with patch('bot.handlers.registration.register_participant_async', new_callable=AsyncMock, return_value=dummy_registered), \
             patch('bot.handlers.registration.get_exam_status', new_callable=AsyncMock, return_value=self.mock_exam_open):
            run_coro_sync(execute_registration(cb_conf, state))

        self.assertIsNone(run_coro_sync(state.get_state()))
        self.assertGreaterEqual(cb_conf.message.answer.call_count, 1)
        self.assertIn("RU-0007", cb_conf.message.answer.call_args_list[0][0][0])
        self.assertIn("TABRIKLAYMIZ", cb_conf.message.answer.call_args_list[0][0][0])
        cb_conf.message.answer_location.assert_called_once()

    def test_registration_duplicate_rejection(self):
        user_id = 70707
        state = MockFSMContext(
            current_state=RegistrationStates.confirm,
            data={
                "first_name": "Ali",
                "last_name": "Valiyev",
                "phone_number": "+998901234567",
                "school_number": "1-maktab",
                "region": "Toshkent shahri",
                "district": "Yunusobod tumani"
            }
        )

        cb_conf = MagicMock()
        cb_conf.from_user.id = user_id
        cb_conf.from_user.username = None
        cb_conf.answer = AsyncMock()
        cb_conf.message.edit_text = AsyncMock()
        cb_conf.message.answer = AsyncMock()

        with patch('bot.handlers.registration.register_participant_async', side_effect=AlreadyRegisteredError("Siz allaqachon ro'yxatdan o'tgansiz!")), \
             patch('bot.handlers.registration.get_participant_by_telegram_id', new_callable=AsyncMock, return_value=None), \
             patch('bot.handlers.registration.get_exam_status', new_callable=AsyncMock, return_value=self.mock_exam_open):
            run_coro_sync(execute_registration(cb_conf, state))

        self.assertIsNone(run_coro_sync(state.get_state()))
        self.assertIn("allaqachon", cb_conf.message.edit_text.call_args[0][0])

    def test_registration_capacity_exceeded(self):
        user_id = 80808
        state = MockFSMContext(
            current_state=RegistrationStates.confirm,
            data={
                "first_name": "Vali",
                "last_name": "Aliyev",
                "phone_number": "+998907654321",
                "school_number": "2-maktab",
                "region": "Toshkent shahri",
                "district": "Yunusobod tumani"
            }
        )

        cb_conf = MagicMock()
        cb_conf.from_user.id = user_id
        cb_conf.from_user.username = None
        cb_conf.answer = AsyncMock()
        cb_conf.message.edit_text = AsyncMock()
        cb_conf.message.answer = AsyncMock()

        with patch('bot.handlers.registration.register_participant_async', side_effect=CapacityExceededError("O'rinlar to'ldi")):
            run_coro_sync(execute_registration(cb_conf, state))

        self.assertIsNone(run_coro_sync(state.get_state()))
        self.assertIn("O'rinlar to'ldi", cb_conf.message.edit_text.call_args[0][0])
