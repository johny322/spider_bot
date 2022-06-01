import asyncio
from datetime import datetime
from typing import Optional

from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ContentTypes

from config.data import MAX_PLAYERS, MAX_LEVEL, WAIT_ROOM_TIME, send_refer_request_cb, confirm_request_cb
from controller__init import Controller
from filters import TextEquals
from keyboards import user_menu_kb, confirm_request_inline_kb, room_kb, \
    refers_request_inline_kb, common_reject_accept_kb
from languages import get_string, get_string_with_args
from languages.utils import get_level_cost
from states import UserMenu
from states.user.room import RoomMenu
from tg_bot import dp, bot
from tg_bot.__main__ import scheduler
from utils import start_room_game, send_room_message, end_room_message, refer_sleep, close_room, \
    check_room_wait, set_new_room_refer


@dp.message_handler(TextEquals('exit_room_button'), state=RoomMenu.IsPlayer)
async def exit_room_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    room_id = data['room_id']
    await Controller.remove_user_from_room(room_id, message.from_user.id)
    await bot.send_message(message.chat.id, await get_string('exit_room_message'), reply_markup=await user_menu_kb())
    user_name = f'{message.from_user.full_name} (t.me/{message.from_user.username})'
    text = await get_string_with_args('user_exit_room_message', user_name)
    await send_room_message(room_id, text)
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('time_left_button'), state=[RoomMenu.IsPlayer, RoomMenu.IsRefer])
async def room_left_time_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    room_id = data['room_id']
    room = await Controller.get_room(room_id)

    if room.users_count < MAX_PLAYERS:
        await bot.send_message(
            message.chat.id,
            await get_string_with_args('not_started_yet_message', await get_string('wait_max_players_message'))
        )
        return
    if room.wait_refer:
        await bot.send_message(
            message.chat.id,
            await get_string_with_args('not_started_yet_message', await get_string('wait_refer_message'))
        )
        return
    left_time = await Controller.get_left_time(room_id)
    left_hours = left_time.seconds // 3600
    left_minutes = (left_time.seconds - left_hours * 3600) // 60
    left_seconds = left_time.seconds - left_hours * 3600 - left_minutes * 60
    await bot.send_message(message.chat.id,
                           await get_string_with_args('room_left_time_message',
                                                      left_hours,
                                                      left_minutes,
                                                      left_seconds
                                                      ))


@dp.callback_query_handler(send_refer_request_cb.filter(action='cancel'), state=RoomMenu.IsPlayer)
async def cancel_send_refer_handler(callback: CallbackQuery, state: FSMContext, raw_state: Optional[str],
                                    callback_data: dict):
    await callback.message.delete()


@dp.callback_query_handler(send_refer_request_cb.filter(), state=RoomMenu.IsPlayer)
async def chose_send_refer_handler(callback: CallbackQuery, state: FSMContext):
    cb_data = callback.data
    refer_id = cb_data.split(':')[-1]
    user_tg_id = cb_data.split(':')[-2]
    from_room_id = cb_data.split(':')[-3]
    refer = await Controller.get_user(int(refer_id))
    if not refer.is_refer:
        await callback.answer(await get_string('user_is_not_refer_message'), show_alert=True)
        await callback.message.delete()
        return
    user = await Controller.get_user(int(user_tg_id))
    user_name = f'{user.full_name} (t.me/{user.username})'
    await callback.answer(await get_string('good_rq_message'), show_alert=True)
    await callback.message.delete()
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

    from_room = await Controller.get_room(from_room_id)
    room_hex_id = from_room.hex_id if from_room else ''

    if not await Controller.room_exist(room_id, room_hex_id):
        await callback.answer(await get_string('room_already_closed_message'), show_alert=True)
        await callback.message.delete()
        return

    if (room_hex_id != current_room_hex_id) or (from_room_id != room_id):
        await callback.answer(await get_string('already_exit_room_message'), show_alert=True)
        await callback.message.delete()
        return

    user = await Controller.get_user(user_tg_id)
    if user.room_id != room_id:
        await callback.answer(await get_string('user_not_in_room_message'), show_alert=True)
        await callback.message.delete()
        return
    if user.is_refer:
        await callback.answer(await get_string('user_is_refer_message'), show_alert=True)
        await callback.message.delete()
        return

    await Controller.update_user(user_tg_id, is_refer=True)
    if level < MAX_LEVEL:
        level += 1
    next_room_id = await Controller.add_refer_room(level=level, user_tg_id=user_tg_id)
    await bot.send_message(
        user_tg_id,
        await get_string('room_refer_welcome_message'),
        reply_markup=await room_kb(True)
    )
    current_state = dp.current_state(chat=user_tg_id, user=user_tg_id)
    await current_state.set_state(RoomMenu.IsRefer.state)
    user_name = f'{user.full_name} (t.me/{user.username})'
    await send_room_message(user.room_id,
                            await get_string_with_args('user_room_refer_welcome_message', user_name, next_room_id,
                                                       level))
    await callback.message.delete()
    room_refers = await Controller.get_room_refers(room_id)
    if len(room_refers) == MAX_PLAYERS:
        next_level_offer_text = await get_string_with_args('next_level_message', level)
        await end_room_message(room_id, next_level_offer_text, await common_reject_accept_kb(),
                               state=RoomMenu.NextRoom.state, increase_level=True)
        # if level < MAX_LEVEL:
        #     next_level_offer_text = await get_string_with_args('next_level_message', level + 1)
        #     await end_room_message(room_id, next_level_offer_text, await common_reject_accept_kb(),
        #                            state=RoomMenu.NextRoom.state, increase_level=True)
        # else:
        #     text = await get_string_with_args('end_room_message', await get_string('all_players_are_refers_message'))
        #     await end_room_message(room_id, text, await user_menu_kb(), state=UserMenu.IsUser.state,
        #                            increase_level=True)


@dp.callback_query_handler(confirm_request_cb.filter(action='accept_rq'), state='*')
async def player_rq_handler(callback: CallbackQuery):
    await callback.answer(await get_string('not_refer_message'))
    await callback.message.delete()


@dp.message_handler(TextEquals('common_accept_button'), state=RoomMenu.NextRoom)
async def accept_next_level_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    level = data['level']
    if level < MAX_LEVEL:
        level += 1
    user = await Controller.get_user(message.from_user.id)
    room_id = user.next_room_id
    room = await Controller.get_room(room_id)
    room_hex_id = room.hex_id

    # rooms = await Controller.get_rooms_by_level(level)
    # free_rooms = await Controller.get_free_rooms(level)
    # if (not rooms) or (not free_rooms):
    #     room_id = await Controller.add_room(level)
    #     room = await Controller.get_room(room_id)
    #     room_hex_id = room.hex_id
    #     scheduler.add_job(close_room, "date", run_date=room.end_at, args=(dp, bot, Controller, room_id, room_hex_id),
    #                       timezone='Europe/Moscow')
    # else:
    #     room = free_rooms[0]
    #     room_id = room.id
    #     room_hex_id = room.hex_id
    await state.reset_state()

    # room_refers = await Controller.get_room_refers(room_id)
    # room_refer = room_refers[0]
    # next_room_id = room_refer.next_room_id
    # refer_tg_id = room_refer.tg_id

    res, is_refer = await Controller.add_user_to_room(room_id, message.from_user.id)
    if res:
        user_name = f'{message.from_user.full_name} (t.me/{message.from_user.username})'
        if level < MAX_LEVEL:
            next_level = level + 1
        else:
            next_level = level
        await state.update_data(room_id=room_id, room_hex_id=room_hex_id, level=level)
        # if is_refer:
        refer_tg_id = message.from_user.id
        next_room_id = await Controller.add_refer_room(level=next_level, user_tg_id=message.from_user.id)
        await RoomMenu.IsRefer.set()
        reply_markup = await room_kb(is_refer)
        text = await get_string_with_args('user_room_welcome_message', user_name) + '\n' + \
               await get_string_with_args('user_room_refer_welcome_message', user_name, next_room_id, next_level)
        run_date = await Controller.set_room_end_time(room_id, WAIT_ROOM_TIME)
        # добавление таска на проверку начала игры через WAIT_ROOM_TIME
        print('add WAIT_ROOM_TIME')
        scheduler.add_job(check_room_wait, "date", run_date=run_date,
                          args=(dp, bot, Controller, room_id, room_hex_id,
                                next_room_id, refer_tg_id, level), timezone='Europe/Moscow')
        # else:
        #     await RoomMenu.IsPlayer.set()
        #     reply_markup = await room_kb(is_refer)
        #     text = await get_string_with_args('user_room_welcome_message', user_name)

        room = await Controller.get_room(room_id)
        await bot.send_message(
            message.chat.id,
            await get_string_with_args('room_welcome_message', room_id, level, room.users_count),
            reply_markup=reply_markup
        )
        await send_room_message(room_id, text)
        room_users = await Controller.get_room_users(room_id)
        if len(room_users) == MAX_PLAYERS:
            # run_date = await Controller.set_room_end_time(room_id)
            # print('add ROOM_TIME')
            # scheduler.add_job(close_room, "date", run_date=run_date, args=(dp, bot, Controller, room_id, room_hex_id),
            #                   timezone='Europe/Moscow')
            # await start_room_game(room_id)
            #
            # await refer_sleep(room_id, room_hex_id)

            run_date = await Controller.set_room_end_time(room_id)
            print('add ROOM_TIME')
            scheduler.add_job(close_room, "date", run_date=run_date, args=(dp, bot, Controller, room_id, room_hex_id,
                                                                           next_room_id, refer_tg_id, level),
                              timezone='Europe/Moscow')
            await start_room_game(room_id)
            await refer_sleep(room_id, room_hex_id, next_room_id, refer_tg_id, level)
    else:
        await message.answer(await get_string('room_is_full_message'), reply_markup=await user_menu_kb())
        await state.reset_state()
        await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('common_reject_button'), state=RoomMenu.NextRoom)
async def reject_next_level_handler(message: Message, state: FSMContext):
    user = await Controller.get_user(message.from_user.id)
    tg_id = user.tg_id
    next_room_id = user.next_room_id
    await bot.send_message(message.chat.id, message.text, reply_markup=await user_menu_kb())
    data = await state.get_data()
    level = data['level']
    await set_new_room_refer(next_room_id, tg_id, level)
    # await Controller.remove_refer_from_room(next_room_id, tg_id)
    # new_refer_tg_id = await Controller.set_random_room_refer(next_room_id)
    # new_refer = await Controller.get_user(new_refer_tg_id)
    # if new_refer_tg_id:
    #     await bot.send_message(
    #         new_refer_tg_id,
    #         await get_string('room_refer_welcome_message'),
    #         reply_markup=await room_kb(True)
    #     )
    #     data = await state.get_data()
    #     level = data['level']
    #     if level < MAX_LEVEL:
    #         level += 1
    #     user_name = f'{new_refer.full_name} (t.me/{new_refer.username})'
    #     await send_room_message(next_room_id, await get_string_with_args('user_room_refer_welcome_message', user_name,
    #                                                                      new_refer.next_room_id, level))
    #     current_state = dp.current_state(chat=new_refer, user=new_refer)
    #     await current_state.set_state(RoomMenu.IsRefer.state)
    await state.reset_state()
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('send_request_button'), state=RoomMenu.IsPlayer)
async def send_refer_request_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    room_id = data['room_id']
    level = data['level']
    room_users_count = await Controller.get_room_users_count(room_id)
    if room_users_count < MAX_PLAYERS:
        await bot.send_message(message.chat.id,
                               await get_string_with_args('not_started_yet_message',
                                                          await get_string('wait_max_players_message')))
        return
    room = await Controller.get_room(room_id)
    if room.wait_refer:
        await bot.send_message(
            message.chat.id,
            await get_string_with_args('not_started_yet_message', await get_string('wait_refer_message'))
        )
        return
    room_hex_id = data['room_hex_id']
    level_cost = await get_level_cost(level)
    await bot.send_message(message.chat.id,
                           await get_string_with_args('select_refer_message', level_cost),
                           reply_markup=await refers_request_inline_kb(room_id, room_hex_id, message.from_user.id))


@dp.message_handler(content_types=ContentTypes.TEXT, state=RoomMenu.IsRefer)
async def refer_chat_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        room_id = data['room_id']
    users = await Controller.get_room_users(room_id)
    for user in users:
        if message.from_user.id == user.tg_id:
            continue
        await bot.send_message(user.tg_id, message.text)
