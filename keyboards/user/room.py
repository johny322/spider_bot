from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from languages import get_string


async def room_kb(is_refer: bool = False, lang_code: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    time_left_button = KeyboardButton(await get_string('time_left_button', lang_code))
    keyboard.row(time_left_button)

    if not is_refer:
        send_request_button = KeyboardButton(await get_string('send_request_button', lang_code))
        keyboard.row(send_request_button)

        exit_room_button = KeyboardButton(await get_string('exit_room_button', lang_code))
        keyboard.row(exit_room_button)
    return keyboard

