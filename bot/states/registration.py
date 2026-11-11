"""
Registration FSM states for aiogram 3.
Sequential order: Full Name -> Phone Number -> Region -> District -> School -> Confirm.
"""
from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    full_name = State()       # 1. Ism va familiya birgalikda
    phone_number = State()    # 2. Telefon raqami (+998... yoki kontakt)
    region = State()          # 3. Viloyat (inline tugmalar)
    district = State()        # 4. Tuman (inline tugmalar)
    school_number = State()   # 5. Maktab / Ta'lim muassasasi
    confirm = State()         # 6. Ma'lumotlarni tasdiqlash
