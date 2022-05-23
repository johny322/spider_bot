from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData

from languages import get_string


async def admin_menu_kb(lang_code: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    # add_room_button = KeyboardButton(await get_string('admin_add_room_button', lang_code))
    # keyboard.row(add_room_button)
    admin_get_refers_button = KeyboardButton(await get_string('admin_get_refers_button', lang_code))
    admin_get_rooms_button = KeyboardButton(await get_string('admin_get_rooms_button', lang_code))
    keyboard.row(admin_get_refers_button, admin_get_rooms_button)

    sending_message_button = KeyboardButton(await get_string('admin_sending_message_button', lang_code))
    keyboard.row(sending_message_button)

    change_start_message_button = KeyboardButton(await get_string('admin_change_start_message_button', lang_code))
    keyboard.row(change_start_message_button)

    admin_switch_state_to_user_button = KeyboardButton(await get_string('admin_switch_state_to_user_button', lang_code))
    keyboard.row(admin_switch_state_to_user_button)
    return keyboard


PaginateCallback = CallbackData('paginate', 'key', 'page')


async def paginate_markup(max_pages: int, key: str = 'users', page: int = 1, count=None):
    previous_page = page - 1
    previous_page_text = '⏪'
    if count is not None:
        current_page_text = f'Всего {count}'
    else:
        current_page_text = f'{page}'
    next_page = page + 1
    next_page_text = '⏩'
    keyboard = InlineKeyboardMarkup(resize_keyboard=True)

    if previous_page > 0:
        keyboard.insert(
            InlineKeyboardButton(
                text=previous_page_text,
                callback_data=PaginateCallback.new(key=key, page=previous_page)
            )
        )
    keyboard.insert(
        InlineKeyboardButton(
            text=current_page_text,
            callback_data='current_page'
        )
    )
    if next_page <= max_pages:
        keyboard.insert(
            InlineKeyboardButton(
                text=next_page_text,
                callback_data=PaginateCallback.new(key=key, page=next_page)
            )
        )
    keyboard.row(
        InlineKeyboardButton(
            text=await get_string('common_close_button'),
            callback_data='close_users'
        )
    )

    return keyboard
