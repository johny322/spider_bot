import asyncio

from config.data import REFER_TIME
from controller__init import Controller
from keyboards import user_menu_kb
from languages import get_string, get_string_with_args
from states import UserMenu
from tg_bot import bot, dp


async def start_room_game(room_id):
    room_users = await Controller.get_room_users(room_id)
    for room_user in room_users:
        try:
            await bot.send_message(room_user.tg_id, await get_string('start_game_message'))
        except Exception as e:
            print(e)


async def send_room_message(room_id, text, reply_markup=None, state=None):
    room_users = await Controller.get_room_users(room_id)
    for room_user in room_users:
        try:
            await bot.send_message(room_user.tg_id, text, reply_markup=reply_markup)
            if state:
                current_state = dp.current_state(chat=room_user.tg_id, user=room_user.tg_id)
                await current_state.set_state(state)
        except Exception as e:
            print(e)


async def end_room_message(room_id, text, reply_markup=None, state=None, increase_level=False):
    room_users = await Controller.get_room_users(room_id)
    # await bot.delete_message()
    for room_user in room_users:
        try:
            await bot.send_message(room_user.tg_id, text, reply_markup=reply_markup)
            if increase_level:
                max_level = room_user.max_level
                if max_level < 10:
                    await Controller.update_user(room_user.tg_id, max_level=max_level + 1)
            if state:
                current_state = dp.current_state(chat=room_user.tg_id, user=room_user.tg_id)
                await current_state.set_state(state)
        except Exception as e:
            print(e)
    await Controller.remove_room(room_id)


async def refer_sleep(room_id, hex_id):
    if await Controller.room_exist(room_id, hex_id):
        # print('refer_sleep for', REFER_TIME)
        await asyncio.sleep(REFER_TIME)
        # print('refer_sleep check')
    if await Controller.room_exist(room_id, hex_id):
        room_refers = await Controller.get_room_refers(room_id)
        if len(room_refers) > 1:
            return
        room_users = await Controller.get_room_users(room_id)
        for room_user in room_users:
            await bot.send_message(
                room_user.tg_id,
                await get_string_with_args('end_room_message', await get_string('end_room_refer_inaction_message')),
                reply_markup=await user_menu_kb()
            )
            current_state = dp.current_state(chat=room_user.tg_id, user=room_user.tg_id)
            await current_state.set_state(UserMenu.IsUser.state)
        await Controller.remove_room(room_id)


async def room_sleep(room_id, hex_id):
    if await Controller.room_exist(room_id, hex_id):
        room = await Controller.get_room(room_id)
        end_at = room.end_at
        sleep_time = (end_at - await Controller.get_datetime_now()).total_seconds()
        if sleep_time < 0:
            return
        # print('room_sleep for', sleep_time)
        await asyncio.sleep(sleep_time)
        # print('room_sleep check')
    if await Controller.room_exist(room_id, hex_id):
        room_users = await Controller.get_room_users(room_id)
        for room_user in room_users:
            await bot.send_message(
                room_user.tg_id,
                await get_string_with_args('end_room_message', await get_string('end_room_time_message')),
                reply_markup=await user_menu_kb()
            )
            current_state = dp.current_state(chat=room_user.tg_id, user=room_user.tg_id)
            await current_state.set_state(UserMenu.IsUser.state)
        await Controller.remove_room(room_id)


async def close_room(dp, bot, Controller, room_id, hex_id):
    print('close_room start')
    if not await Controller.room_exist(room_id, hex_id):
        print('close_room no room')
        return
    room_users = await Controller.get_room_users(room_id)
    for room_user in room_users:
        await bot.send_message(
            room_user.tg_id,
            await get_string_with_args('end_room_message', await get_string('end_room_time_message')),
            reply_markup=await user_menu_kb()
        )
        current_state = dp.current_state(chat=room_user.tg_id, user=room_user.tg_id)
        await current_state.set_state(UserMenu.IsUser.state)

    await Controller.remove_room(room_id)
    print('closed_room closed')
