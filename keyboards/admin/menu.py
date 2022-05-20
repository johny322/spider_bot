from aiogram.types.reply_keyboard import ReplyKeyboardMarkup, KeyboardButton

from languages import get_string


async def admin_menu_kb(lang_code: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    # add_room_button = KeyboardButton(await get_string('admin_add_room_button', lang_code))
    # keyboard.row(add_room_button)

    sending_message_button = KeyboardButton(await get_string('admin_sending_message_button', lang_code))
    keyboard.row(sending_message_button)

    change_start_message_button = KeyboardButton(await get_string('admin_change_start_message_button', lang_code))
    keyboard.row(change_start_message_button)

    admin_switch_state_to_user_button = KeyboardButton(await get_string('admin_switch_state_to_user_button', lang_code))
    keyboard.row(admin_switch_state_to_user_button)
    return keyboard
