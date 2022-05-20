from aiogram.dispatcher.filters.state import State, StatesGroup


class AdminMenu(StatesGroup):
    IsAdmin = State()


class ChangeStartMessage(StatesGroup):
    SetText = State()
    SetData = State()
    ConfirmChanges = State()


class SendingMessage(StatesGroup):
    SetText = State()
    SetData = State()
    ConfirmChanges = State()


class AddRoom(StatesGroup):
    RoomLevel = State()
    ConfirmRoom = State()


class SelectRoom(StatesGroup):
    RoomLevel = State()
    Room = State()


class RoomMenu(StatesGroup):
    IsPlayer = State()
    IsRefer = State()
