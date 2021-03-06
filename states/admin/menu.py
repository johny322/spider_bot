from aiogram.dispatcher.filters.state import State, StatesGroup


class AdminMenu(StatesGroup):
    IsAdmin = State()
    SelectLevel = State()
    SelectRoom = State()


class ChangeStartMessage(StatesGroup):
    SetText = State()
    SetData = State()
    ConfirmChanges = State()
