from aiogram.fsm.state import StatesGroup, State


class Reg(StatesGroup):
    wb_token = State()
    sheet_id = State()