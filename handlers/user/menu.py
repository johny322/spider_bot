from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.callback_data import CallbackData

from admin_utils import get_start_message
from admin_utils.start_message import get_start_message_file
from controller__init import Controller
from keyboards import user_menu_kb, common_choose_level_inline_kb, cancel_cb, common_choose_room_inline_kb, \
    room_kb
from languages import get_string_with_args, get_string
from tg_bot import dp, bot
from filters import TextEquals
from states import UserMenu, SelectRoom, RoomMenu


@dp.callback_query_handler(cancel_cb.filter(is_admin='False'), state='*')
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await UserMenu.IsUser.set()


@dp.message_handler(commands=['start'], state="*")
async def user_start_handler(message: Message, state: FSMContext):
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
    rooms = await Controller.get_rooms_by_level(level)
    if not rooms:
        await Controller.add_room(level)
        rooms = await Controller.get_rooms_by_level(level)
    await callback.message.edit_text(
        'Выберите комнату',
        reply_markup=await common_choose_room_inline_kb(rooms)
    )

    await SelectRoom.Room.set()


@dp.callback_query_handler(state=SelectRoom.Room)
async def select_room_handler(callback: CallbackQuery, state: FSMContext):
    room_id = int(callback.data.split(':')[-1])
    res, is_refer = await Controller.add_user_to_room(room_id, callback.from_user.id)
    if res:
        await state.update_data(room_id=room_id)
        if is_refer:
            await RoomMenu.IsRefer.set()
            reply_markup = await room_kb(is_refer)
            text = await get_string('room_welcome_message') + '\n' + await get_string('room_refer_welcome_message')
        else:
            await RoomMenu.IsPlayer.set()
            reply_markup = await room_kb(is_refer)
            text = await get_string('room_welcome_message')

        await callback.message.delete()
        await bot.send_message(
            callback.message.chat.id,
            text,
            reply_markup=reply_markup
        )
    else:
        await callback.answer('Стол заполнен', show_alert=True)


@dp.message_handler(TextEquals('exit_room_button'), state=[RoomMenu.IsPlayer, RoomMenu.IsRefer])
async def exit_room_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    room_id = data['room_id']
    await Controller.delete_user_to_room(room_id, message.from_user.id)
    await bot.send_message(message.chat.id, await get_string('exit_room_message'), reply_markup=await user_menu_kb())
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('time_left_button'), state=[RoomMenu.IsPlayer, RoomMenu.IsRefer])
async def room_left_time_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    room_id = data['room_id']
    left_time = await Controller.get_left_time(room_id)
    await bot.send_message(message.chat.id,
                           await get_string_with_args('room_left_time_message', left_time))


@dp.message_handler(commands=['room'], state=UserMenu.IsUser)
async def user_add_to_queue(message: Message, state: FSMContext):
    room_num = message.get_args()
    if room_num:
        room_num = int(room_num.strip())
        await Controller.add_user_to_queue(room_num, message.from_user.id)
        print('Added user to queue')
