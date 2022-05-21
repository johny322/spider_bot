from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.callback_data import CallbackData

from admin_utils import get_start_message
from admin_utils.start_message import get_start_message_file
# from config.data import MAX_PLAYERS
from controller__init import Controller
from keyboards import user_menu_kb, common_choose_level_inline_kb, cancel_cb, common_choose_room_inline_kb, \
    room_kb, refers_request_inline_kb, send_refer_request_cb, confirm_request_inline_kb, confirm_request_cb
from languages import get_string_with_args, get_string
from tg_bot import dp, bot
from filters import TextEquals
from states import UserMenu, SelectRoom, RoomMenu

MAX_PLAYERS = 2


@dp.callback_query_handler(cancel_cb.filter(is_admin='False'), state=[RoomMenu.IsPlayer, RoomMenu.IsRefer])
async def cancel_select_room_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()


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
        user_name = f'{callback.from_user.full_name} (@{callback.from_user.username})'
        await state.update_data(room_id=room_id)
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

        await bot.send_message(
            callback.message.chat.id,
            await get_string('room_welcome_message'),
            reply_markup=reply_markup
        )
        await send_room_message(room_id, text)
        room_users = await Controller.get_room_users(room_id)
        if len(room_users) == MAX_PLAYERS:
            await start_room_game(room_id)
    else:
        await callback.answer('Стол заполнен', show_alert=True)


@dp.message_handler(TextEquals('exit_room_button'), state=[RoomMenu.IsPlayer, RoomMenu.IsRefer])
async def exit_room_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    room_id = data['room_id']
    await Controller.remove_user_from_room(room_id, message.from_user.id)
    await bot.send_message(message.chat.id, await get_string('exit_room_message'), reply_markup=await user_menu_kb())
    user_name = f'{message.from_user.full_name} (@{message.from_user.username})'
    text = await get_string_with_args('user_exit_room_message', user_name)
    await send_room_message(room_id, text)
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('time_left_button'), state=[RoomMenu.IsPlayer, RoomMenu.IsRefer])
async def room_left_time_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    room_id = data['room_id']
    left_time = await Controller.get_left_time(room_id)
    await bot.send_message(message.chat.id,
                           await get_string_with_args('room_left_time_message', left_time))


@dp.callback_query_handler(send_refer_request_cb.filter(action='cancel'), state=RoomMenu.IsPlayer)
async def cancel_send_refer_handler(callback: CallbackQuery):
    await callback.message.delete()


@dp.callback_query_handler(send_refer_request_cb.filter(), state=RoomMenu.IsPlayer)
async def chose_send_refer_handler(callback: CallbackQuery):
    cb_data = callback.data
    refer_id = cb_data.split(':')[-1]
    user_tg_id = cb_data.split(':')[-2]
    money = cb_data.split(':')[-3]
    user = await Controller.get_user(int(user_tg_id))
    user_name = f'{user.full_name} (@{user.username})'
    await callback.answer(await get_string('good_rq_message'), show_alert=True)
    await callback.message.delete()
    # await bot.send_message(
    #     callback.message.chat.id,
    #     await get_string('good_rq_message')
    # )
    await bot.send_message(
        refer_id,
        await get_string_with_args('confirm_user_rq_message', money, user_name),
        reply_markup=await confirm_request_inline_kb(int(user_tg_id))
    )


@dp.callback_query_handler(confirm_request_cb.filter(action='reject_rq'), state=RoomMenu.IsRefer)
async def reject_rq_handler(callback: CallbackQuery):
    await callback.message.delete()


@dp.callback_query_handler(confirm_request_cb.filter(action='accept_rq'), state=RoomMenu.IsRefer)
async def accept_rq_handler(callback: CallbackQuery):
    cb_data = callback.data
    user_tg_id = int(cb_data.split(':')[-1])
    await Controller.update_user(user_tg_id, is_refer=True)
    await bot.send_message(
        user_tg_id,
        await get_string('room_refer_welcome_message'),
        reply_markup=await room_kb(True)
    )
    user = await Controller.get_user(user_tg_id)
    user_name = f'{user.full_name} (@{user.username})'
    await send_room_message(user.room_id, await get_string_with_args('user_room_refer_welcome_message', user_name))
    await callback.message.delete()


@dp.message_handler(TextEquals('send_request_button'), state=RoomMenu.IsPlayer)
async def send_refer_request_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    room_id = data['room_id']
    await bot.send_message(message.chat.id,
                           await get_string('select_refer_message'),
                           reply_markup=await refers_request_inline_kb(room_id, message.from_user.id))


@dp.message_handler(commands=['room'], state=UserMenu.IsUser)
async def user_add_to_queue(message: Message, state: FSMContext):
    room_num = message.get_args()
    if room_num:
        room_num = int(room_num.strip())
        await Controller.add_user_to_queue(room_num, message.from_user.id)
        print('Added user to queue')


async def start_room_game(room_id):
    room_users = await Controller.get_room_users(room_id)
    for room_user in room_users:
        try:
            await bot.send_message(room_user.tg_id, await get_string('start_game_message'))
        except Exception as e:
            print(e)


async def send_room_message(room_id, text, reply_markup=None):
    room_users = await Controller.get_room_users(room_id)
    for room_user in room_users:
        try:
            await bot.send_message(room_user.tg_id, text, reply_markup=reply_markup)
        except Exception as e:
            print(e)
