from aiogram.dispatcher.filters.state import StatesGroup, State


class RoomMenu(StatesGroup):
    Game = State()
    IsPlayer = State()
    IsRefer = State()
    NextRoom = State()
