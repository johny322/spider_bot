import asyncio

from config.data import REFER_TIME, MAX_LEVEL, WAIT_ROOM_TIME
from controller__init import Controller
from keyboards import user_menu_kb, room_kb
from languages import get_string, get_string_with_args
from states import UserMenu, RoomMenu
from tg_bot import bot, dp
from tg_bot.__main__ import scheduler


async def start_room_game(room_id):
    await Controller.update_room(room_id, is_started=True)
    room_users = await Controller.get_room_users(room_id)
    for room_user in room_users:
        try:
            await bot.send_message(room_user.tg_id, await get_string('start_game_message'))
        except Exception as e:
            pass


async def send_room_message(room_id, text, reply_markup=None, state=None):
    room_users = await Controller.get_room_users(room_id)
    for room_user in room_users:
        try:
            await bot.send_message(room_user.tg_id, text, reply_markup=reply_markup, disable_web_page_preview=True)
            if state:
                current_state = dp.current_state(chat=room_user.tg_id, user=room_user.tg_id)
                await current_state.set_state(state)
        except Exception as e:
            pass


async def end_room_message(room_id, text, reply_markup=None, state=None, increase_level=False):
    room_users = await Controller.get_room_users(room_id)
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
            pass
    await Controller.remove_room(room_id)


async def refer_sleep(room_id, hex_id, next_room_id, refer_tg_id, level):
    if await Controller.room_exist(room_id, hex_id):
        await asyncio.sleep(REFER_TIME)
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
        await set_new_room_refer(next_room_id, refer_tg_id, level)
        await Controller.remove_room(room_id)


async def set_new_room_refer(room_id, refer_tg_id, level):
    await Controller.remove_refer_from_room(room_id, refer_tg_id)
    new_refer_tg_id = await Controller.set_random_room_refer(room_id)
    if new_refer_tg_id:
        new_refer = await Controller.get_user(new_refer_tg_id)
        await bot.send_message(
            new_refer_tg_id,
            await get_string('room_refer_welcome_message'),
            reply_markup=await room_kb(True)
        )
        if level < MAX_LEVEL:
            level += 1
        user_name = f'{new_refer.full_name} (t.me/{new_refer.username})'
        await send_room_message(room_id, await get_string_with_args('user_room_refer_welcome_message', user_name,
                                                                         new_refer.next_room_id, level))
        next_room_id = new_refer.next_room_id
        current_state = dp.current_state(chat=new_refer_tg_id, user=new_refer_tg_id)
        await current_state.set_state(RoomMenu.IsRefer.state)
        run_date = await Controller.set_room_end_time(room_id, WAIT_ROOM_TIME)
        room = await Controller.get_room(room_id)
        room_hex_id = room.hex_id

        scheduler.add_job(check_room_wait, "date", run_date=run_date,
                          args=(dp, bot, Controller, room_id, room_hex_id,
                                next_room_id, refer_tg_id, level), timezone='Europe/Moscow')


async def check_room_wait(dp, bot, Controller, room_id, hex_id, next_room_id, refer_tg_id, level):
    room = await Controller.get_room(room_id, hex_id)
    if room is None:
        return
    if room.is_started:
        return
    await close_room(dp, bot, Controller, room_id, hex_id, next_room_id, refer_tg_id, level)


async def close_room(dp, bot, Controller, room_id, hex_id, next_room_id, refer_tg_id, level):
    if not await Controller.room_exist(room_id, hex_id):
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
    await set_new_room_refer(next_room_id, refer_tg_id, level)
    await Controller.remove_room(room_id)
