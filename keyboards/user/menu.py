from aiogram.types.reply_keyboard import ReplyKeyboardMarkup, KeyboardButton

from languages import get_string


async def user_menu_kb(lang_code: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    select_room_button = KeyboardButton(await get_string('select_room_button', lang_code))
    keyboard.row(select_room_button)

    user_profile_button = KeyboardButton(await get_string('user_profile_button', lang_code))
    keyboard.row(user_profile_button)
    return keyboard
