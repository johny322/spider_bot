from aiogram.dispatcher.filters.state import StatesGroup, State


class RoomMenu(StatesGroup):
    IsPlayer = State()
    IsRefer = State()
    NextRoom = State()
