from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery

from admin_utils import get_start_message
from admin_utils.start_message import get_start_message_file
from config.data import MAX_PLAYERS
from controller__init import Controller
from handlers.user.room import room_sleep
from handlers.user.room import start_room_game, send_room_message
from keyboards import user_menu_kb, common_choose_level_inline_kb, cancel_cb, common_choose_room_inline_kb, \
    room_kb
from languages import get_string_with_args, get_string
from tg_bot import dp, bot
from filters import TextEquals
from states import UserMenu, SelectRoom, RoomMenu


@dp.callback_query_handler(cancel_cb.filter(is_admin='False'), state=[RoomMenu.IsPlayer, RoomMenu.IsRefer])
async def cancel_select_room_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()


@dp.callback_query_handler(cancel_cb.filter(is_admin='False'), state='*')
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await UserMenu.IsUser.set()


@dp.message_handler(commands=['start'], state=RoomMenu.IsRefer)
async def refer_start_handler(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, await get_string('start_refer_message'))


@dp.message_handler(commands=['start'], state=RoomMenu.IsPlayer)
async def player_start_handler(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, await get_string('start_player_message'))


@dp.message_handler(commands=['start'], state="*")
async def user_start_handler(message: Message, state: FSMContext):
    # state_name = await state.get_state()
    if not await Controller.user_exist(message.from_user.id):
        await Controller.add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    start_message_file_data = await get_start_message_file()
    start_text = await get_start_message()
    reply_markup = await user_menu_kb()
    if start_message_file_data:
        file_id, file_type = start_message_file_data.split(', ')
        if file_type == 'photo':
            await bot.send_photo(message.chat.id, file_id, caption=start_text, reply_markup=reply_markup,
                                 parse_mode="MarkdownV2")
        elif file_type == 'document':
            await bot.send_document(message.chat.id, file_id, caption=start_text, reply_markup=reply_markup,
                                    parse_mode="MarkdownV2")
        elif file_type == 'voice':
            await bot.send_voice(message.chat.id, file_id, caption=start_text, reply_markup=reply_markup,
                                 parse_mode="MarkdownV2")
        elif file_type == 'video':
            await bot.send_video(message.chat.id, file_id, caption=start_text, reply_markup=reply_markup,
                                 parse_mode="MarkdownV2")
    else:
        await bot.send_message(message.chat.id, start_text, reply_markup=reply_markup, parse_mode="MarkdownV2")
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('user_profile_button'), state=UserMenu.IsUser)
async def user_profile_handler(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, await get_string_with_args('user_profile_message',
                                                                       message.from_user.username))


@dp.message_handler(TextEquals('select_room_button'), state=UserMenu.IsUser)
async def rooms_handler(message: Message, state: FSMContext):
    user = await Controller.get_user(message.from_user.id)
    user_level = user.max_level
    await bot.send_message(message.chat.id, await get_string('select_level'),
                           reply_markup=await common_choose_level_inline_kb(user_level))

    await SelectRoom.RoomLevel.set()


@dp.callback_query_handler(state=SelectRoom.RoomLevel)
async def select_room_level_handler(callback: CallbackQuery, state: FSMContext):
    level = int(callback.data.split(':')[-1])
    await state.update_data(level=level)
    rooms = await Controller.get_rooms_by_level(level)
    free_rooms = await Controller.get_free_rooms(level)
    if (not rooms) or (not free_rooms):
        await Controller.add_room(level)
        rooms = await Controller.get_rooms_by_level(level)
    await callback.message.edit_text(
        'Выберите стол',
        reply_markup=await common_choose_room_inline_kb(rooms)
    )

    await SelectRoom.Room.set()


@dp.callback_query_handler(state=SelectRoom.Room)
async def select_room_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    level = data['level']
    room_id = int(callback.data.split(':')[-1])
    room_hex_id = callback.data.split(':')[-2]
    res, is_refer = await Controller.add_user_to_room(room_id, callback.from_user.id)
    if res:
        user_name = f'{callback.from_user.full_name} (@{callback.from_user.username})'
        await state.update_data(room_id=room_id, room_hex_id=room_hex_id)
        if is_refer:
            await RoomMenu.IsRefer.set()
            reply_markup = await room_kb(is_refer)
            text = await get_string_with_args('user_room_welcome_message', user_name) + '\n' + \
                   await get_string_with_args('user_room_refer_welcome_message', user_name)
        else:
            await RoomMenu.IsPlayer.set()
            reply_markup = await room_kb(is_refer)
            text = await get_string_with_args('user_room_welcome_message', user_name)

        await callback.message.delete()
        room = await Controller.get_room(room_id)
        await bot.send_message(
            callback.message.chat.id,
            await get_string_with_args('room_welcome_message', room_id, level, room.users_count),
            reply_markup=reply_markup
        )
        await send_room_message(room_id, text)
        room_users = await Controller.get_room_users(room_id)
        if len(room_users) == MAX_PLAYERS:
            await start_room_game(room_id)
            await room_sleep(room_id, room_hex_id)
    else:
        await callback.answer(await get_string('room_is_full_message'), show_alert=True)
