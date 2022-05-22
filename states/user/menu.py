from aiogram.dispatcher.filters.state import State, StatesGroup


class UserMenu(StatesGroup):
    IsUser = State()


class SelectRoom(StatesGroup):
    RoomLevel = State()
    Room = State()
