from typing import List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.utils.callback_data import CallbackData

from controller__init import Controller
from database.models import Room
from languages import get_string


async def common_back_kb(lang_code: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    common_back_button = KeyboardButton(await get_string('common_back_button', lang_code))
    keyboard.row(common_back_button)
    return keyboard


async def common_skip_kb(lang_code: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    common_skip_button = KeyboardButton(await get_string('common_skip_button', lang_code))
    keyboard.row(common_skip_button)
    return keyboard


async def common_confirm_kb(lang_code: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    common_confirm_button = KeyboardButton(await get_string('common_confirm_button', lang_code))
    keyboard.row(common_confirm_button)
    return keyboard


async def common_back_skip_kb(lang_code: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    common_back_button = KeyboardButton(await get_string('common_back_button', lang_code))
    common_skip_button = KeyboardButton(await get_string('common_skip_button', lang_code))
    keyboard.row(common_back_button, common_skip_button)
    return keyboard


async def common_back_confirm_kb(lang_code: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    common_back_button = KeyboardButton(await get_string('common_back_button', lang_code))
    common_confirm_button = KeyboardButton(await get_string('common_confirm_button', lang_code))
    keyboard.row(common_back_button, common_confirm_button)
    return keyboard


async def common_back_skip_confirm_kb(lang_code: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    common_back_button = KeyboardButton(await get_string('common_back_button', lang_code))
    common_skip_button = KeyboardButton(await get_string('common_skip_button', lang_code))
    common_confirm_button = KeyboardButton(await get_string('common_confirm_button', lang_code))
    keyboard.row(common_skip_button)
    keyboard.row(common_back_button, common_confirm_button)
    return keyboard


async def common_reject_accept_kb(lang_code: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    common_reject_button = KeyboardButton(await get_string('common_reject_button', lang_code))
    common_accept_button = KeyboardButton(await get_string('common_accept_button', lang_code))
    keyboard.row(common_reject_button, common_accept_button)
    return keyboard


async def common_reject_accept_back_kb(lang_code: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    common_reject_button = KeyboardButton(await get_string('common_reject_button', lang_code))
    common_accept_button = KeyboardButton(await get_string('common_accept_button', lang_code))
    common_back_button = KeyboardButton(await get_string('common_back_button', lang_code))
    keyboard.row(common_reject_button, common_accept_button)
    keyboard.row(common_back_button)
    return keyboard


async def common_reject_accept_skip_kb(lang_code: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    common_skip_button = KeyboardButton(await get_string('common_skip_button', lang_code))
    common_reject_button = KeyboardButton(await get_string('common_reject_button', lang_code))
    common_accept_button = KeyboardButton(await get_string('common_accept_button', lang_code))
    keyboard.row(common_skip_button)
    keyboard.row(common_reject_button, common_accept_button)
    return keyboard


async def common_back_reject_accept_skip_kb(lang_code: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    common_skip_button = KeyboardButton(await get_string('common_skip_button', lang_code))
    common_reject_button = KeyboardButton(await get_string('common_reject_button', lang_code))
    common_accept_button = KeyboardButton(await get_string('common_accept_button', lang_code))
    common_back_button = KeyboardButton(await get_string('common_back_button', lang_code))
    keyboard.row(common_skip_button)
    keyboard.row(common_reject_button, common_accept_button)
    keyboard.row(common_back_button)
    return keyboard


async def common_empty_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


cancel_cb = CallbackData('cancel_cb', 'is_admin')


async def common_choose_level_inline_kb(max_level: int, is_admin: bool = False) -> InlineKeyboardMarkup:
    cb_data = CallbackData('level_choose', 'level')

    keyboard = InlineKeyboardMarkup(resize_keyboard=True, row_width=2)
    for num in range(1, max_level + 1):
        keyboard.insert(
            InlineKeyboardButton(
                text=str(num),
                callback_data=cb_data.new(level=str(num))
            )
        )
    keyboard.row(
        InlineKeyboardButton(
            text=await get_string('common_cancel_button'),
            callback_data=cancel_cb.new(is_admin=is_admin)
        )
    )
    return keyboard


async def common_back_cancel_inline_kb(is_admin=False) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        InlineKeyboardButton(
            text=await get_string('common_back_button'),
            callback_data='common_back_button'
        )
    )
    keyboard.row(
        InlineKeyboardButton(
            text=await get_string('common_cancel_button'),
            callback_data=cancel_cb.new(is_admin=is_admin)
        )
    )
    return keyboard


async def common_choose_room_inline_kb(rooms: List[Room], is_admin=False) -> InlineKeyboardMarkup:
    # rooms = await Controller.get_rooms_by_level(int(level))
    keyboard = InlineKeyboardMarkup(resize_keyboard=True, row_width=2)
    for room in rooms:
        # try:
        #     users = room.users.split(',')
        # except AttributeError:
        #     users = []
        # users_count = len(users)
        users_count = room.users_count
        keyboard.insert(
            InlineKeyboardButton(
                text=f'№{room.id}({users_count} уч.)',
                callback_data=f'room:{room.hex_id}:{room.id}'
            )
        )
    keyboard.row(
        InlineKeyboardButton(
            text=await get_string('common_back_button'),
            callback_data='common_back_button'
        )
    )
    keyboard.row(
        InlineKeyboardButton(
            text=await get_string('common_cancel_button'),
            callback_data=cancel_cb.new(is_admin=is_admin)
        )
    )
    return keyboard


async def common_reject_accept_inline_kb(callback_data=None, lang_code: str = 'ru') -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(resize_keyboard=True)
    common_reject_button = InlineKeyboardButton(await get_string('common_reject_button', lang_code),
                                                callback_data='common_reject_il_button' if callback_data is None else callback_data)
    common_accept_button = InlineKeyboardButton(await get_string('common_accept_button', lang_code),
                                                callback_data='common_accept_il_button' if callback_data is None else callback_data)
    keyboard.row(common_reject_button)
    keyboard.row(common_accept_button)
    return keyboard


send_refer_request_cb = CallbackData('send_rq', 'action', 'room_id', 'user_tg_id', 'refer_id')


async def refers_request_inline_kb(room_id: int, hex_id: str, user_tg_id: int, money: int = 100,
                                   lang_code: str = 'ru') -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(resize_keyboard=True, row_width=2)
    room_refers = await Controller.get_room_refers(room_id)
    for room_refer in room_refers:
        text = f'{room_refer.full_name} (@{room_refer.username})'
        keyboard.insert(
            InlineKeyboardButton(
                text,
                callback_data=send_refer_request_cb.new(
                    refer_id=room_refer.tg_id,
                    action='send',
                    user_tg_id=user_tg_id,
                    room_id=room_id
                )
            )
        )
    keyboard.row(
        InlineKeyboardButton(
            text=await get_string('common_cancel_button'),
            callback_data=send_refer_request_cb.new(action='cancel', room_id=room_id, user_tg_id=user_tg_id,
                                                    refer_id='')
        )
    )
    return keyboard


confirm_request_cb = CallbackData('confirm_rq', 'action', 'from_room_id', 'user_tg_id')


async def confirm_request_inline_kb(user_tg_id: int, from_room_id: int, lang_code: str = 'ru'):
    keyboard = InlineKeyboardMarkup(resize_keyboard=True)
    common_reject_button = InlineKeyboardButton(
        await get_string('common_reject_button', lang_code),
        callback_data=confirm_request_cb.new(action='reject_rq', user_tg_id=user_tg_id, from_room_id=from_room_id)
    )
    common_accept_button = InlineKeyboardButton(
        await get_string('common_accept_button', lang_code),
        callback_data=confirm_request_cb.new(action='accept_rq', user_tg_id=user_tg_id, from_room_id=from_room_id)
    )
    keyboard.row(common_reject_button)
    keyboard.row(common_accept_button)
    return keyboard
