import asyncio
from typing import Optional

from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery

from config.data import MAX_PLAYERS
from controller__init import Controller
from filters import TextEquals
from keyboards import user_menu_kb, send_refer_request_cb, confirm_request_inline_kb, confirm_request_cb, room_kb, \
    refers_request_inline_kb, common_reject_accept_kb
from languages import get_string, get_string_with_args
from languages.utils import get_level_cost
from states import UserMenu
from states.user.room import RoomMenu
from tg_bot import dp, bot
from tg_bot.__main__ import scheduler
from utils import start_room_game, send_room_message, end_room_message, refer_sleep, room_sleep, close_room


@dp.message_handler(TextEquals('exit_room_button'), state=RoomMenu.IsPlayer)
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
async def cancel_send_refer_handler(callback: CallbackQuery, state: FSMContext, raw_state: Optional[str],
                                    callback_data: dict):
    print(raw_state)
    print(callback_data)
    await callback.message.delete()
    print('delete')


@dp.callback_query_handler(send_refer_request_cb.filter(), state=RoomMenu.IsPlayer)
async def chose_send_refer_handler(callback: CallbackQuery, state: FSMContext):
    cb_data = callback.data
    refer_id = cb_data.split(':')[-1]
    user_tg_id = cb_data.split(':')[-2]
    from_room_id = cb_data.split(':')[-3]
    user = await Controller.get_user(int(user_tg_id))
    user_name = f'{user.full_name} (@{user.username})'
    await callback.answer(await get_string('good_rq_message'), show_alert=True)
    await callback.message.delete()
    # await bot.send_message(
    #     callback.message.chat.id,
    #     await get_string('good_rq_message')
    # )
    data = await state.get_data()
    level = data['level']
    level_cost = await get_level_cost(level)
    await bot.send_message(
        refer_id,
        await get_string_with_args('confirm_user_rq_message', level_cost, user_name),
        reply_markup=await confirm_request_inline_kb(int(user_tg_id), int(from_room_id))
    )


@dp.callback_query_handler(confirm_request_cb.filter(), state=UserMenu.IsUser)
async def rq_outside_room_handler(callback: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(
        callback.id,
        'Вы покинули комнату',
        show_alert=True
    )
    await callback.message.delete()


@dp.callback_query_handler(confirm_request_cb.filter(action='reject_rq'), state=RoomMenu.IsRefer)
async def reject_rq_handler(callback: CallbackQuery):
    await callback.message.delete()


@dp.callback_query_handler(confirm_request_cb.filter(action='accept_rq'), state=RoomMenu.IsRefer)
async def accept_rq_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    room_id = data['room_id']
    level = data['level']
    current_room_hex_id = data['room_hex_id']
    cb_data = callback.data
    user_tg_id = int(cb_data.split(':')[-1])
    from_room_id = int(cb_data.split(':')[-2])
    # room_hex_id = cb_data.split(':')[-2]
    # if not await Controller.room_exist(room_id, room_hex_id):
    #     await callback.answer('Комната уже закрыта', show_alert=True)
    #     await callback.message.delete()
    #     return
    from_room = await Controller.get_room(from_room_id)
    room_hex_id = from_room.hex_id
    if room_hex_id != current_room_hex_id:
        await callback.answer('Вы уже покинули эту комнату', show_alert=True)
        await callback.message.delete()
        return
    user = await Controller.get_user(user_tg_id)
    if user.is_refer:
        await callback.answer('Игрок уже является рефером', show_alert=True)
        await callback.message.delete()
        return
    await Controller.update_user(user_tg_id, is_refer=True)
    await bot.send_message(
        user_tg_id,
        await get_string('room_refer_welcome_message'),
        reply_markup=await room_kb(True)
    )
    # print('pre user')
    # await asyncio.sleep(10)
    # user = await Controller.get_user(user_tg_id)
    # print('post user')
    user_name = f'{user.full_name} (@{user.username})'
    await send_room_message(user.room_id, await get_string_with_args('user_room_refer_welcome_message', user_name))
    await callback.message.delete()
    room_refers = await Controller.get_room_refers(room_id)
    if len(room_refers) == MAX_PLAYERS:
        if level < 10:
            next_level_offer_text = await get_string_with_args('next_level_message', level + 1)
            await end_room_message(room_id, next_level_offer_text, await common_reject_accept_kb(),
                                   state=RoomMenu.NextRoom.state, increase_level=True)
        else:
            text = await get_string_with_args('end_room_message', await get_string('all_players_are_refers_message'))
            await end_room_message(room_id, text, await user_menu_kb(), state=UserMenu.IsUser.state,
                                   increase_level=True)


@dp.message_handler(TextEquals('common_accept_button'), state=RoomMenu.NextRoom)
async def accept_next_level_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    level = data['level'] + 1
    rooms = await Controller.get_rooms_by_level(level)
    free_rooms = await Controller.get_free_rooms(level)
    if (not rooms) or (not free_rooms):
        room_id = await Controller.add_room(level)
        room = await Controller.get_room(room_id)
        room_hex_id = room.hex_id
        scheduler.add_job(close_room, "date", run_date=room.end_at, args=(room_id, room_hex_id),
                          timezone='Europe/Moscow')
    else:
        room = free_rooms[0]
        room_id = room.id
        room_hex_id = room.hex_id
    await state.reset_state()
    res, is_refer = await Controller.add_user_to_room(room_id, message.from_user.id)
    if res:
        user_name = f'{message.from_user.full_name} (@{message.from_user.username})'
        await state.update_data(room_id=room_id, room_hex_id=room_hex_id, level=level)
        if is_refer:
            await RoomMenu.IsRefer.set()
            reply_markup = await room_kb(is_refer)
            text = await get_string_with_args('user_room_welcome_message', user_name) + '\n' + \
                   await get_string_with_args('user_room_refer_welcome_message', user_name)
        else:
            await RoomMenu.IsPlayer.set()
            reply_markup = await room_kb(is_refer)
            text = await get_string_with_args('user_room_welcome_message', user_name)

        room = await Controller.get_room(room_id)
        await bot.send_message(
            message.chat.id,
            await get_string_with_args('room_welcome_message', room_id, level, room.users_count),
            reply_markup=reply_markup
        )
        await send_room_message(room_id, text)
        room_users = await Controller.get_room_users(room_id)
        if len(room_users) == MAX_PLAYERS:
            await start_room_game(room_id)
            await refer_sleep(room_id, room_hex_id)
            # await room_sleep(room_id, room_hex_id)
    else:
        await message.answer(await get_string('room_is_full_message'), reply_markup=await user_menu_kb())
        await state.reset_state()
        await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('common_reject_button'), state=RoomMenu.NextRoom)
async def reject_next_level_handler(message: Message, state: FSMContext):
    await UserMenu.IsUser.set()
    await bot.send_message(message.chat.id, message.text, reply_markup=await user_menu_kb())


@dp.message_handler(TextEquals('send_request_button'), state=RoomMenu.IsPlayer)
async def send_refer_request_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    room_id = data['room_id']
    level = data['level']
    room_users_count = await Controller.get_room_users_count(room_id)
    if room_users_count < MAX_PLAYERS:
        await bot.send_message(message.chat.id, await get_string('not_started_yet_message'))
        return
    room_hex_id = data['room_hex_id']
    level_cost = await get_level_cost(level)
    await bot.send_message(message.chat.id,
                           await get_string_with_args('select_refer_message', level_cost),
                           reply_markup=await refers_request_inline_kb(room_id, room_hex_id, message.from_user.id))

# @dp.message_handler(commands=['room'], state=UserMenu.IsUser)
# async def user_add_to_queue(message: Message, state: FSMContext):
#     room_num = message.get_args()
#     if room_num:
#         room_num = int(room_num.strip())
#         await Controller.add_user_to_queue(room_num, message.from_user.id)
#         print('Added user to queue')
