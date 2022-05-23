from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ContentType, ContentTypes, CallbackQuery, ParseMode

from admin_utils import get_start_message, edit_start_message
from admin_utils.start_message import edit_start_message_file
from controller__init import Controller
from keyboards import admin_menu_kb, user_menu_kb, common_skip_kb, common_reject_accept_kb, \
    common_choose_level_inline_kb, common_reject_accept_inline_kb, cancel_cb, paginate_markup, PaginateCallback, \
    common_choose_room_inline_kb, common_back_cancel_inline_kb
from languages import get_string, get_string_with_args
from tg_bot import dp, bot
from filters import CheckAdminPassword, TextEquals
from states import AdminMenu, UserMenu, ChangeStartMessage, AddRoom


@dp.message_handler(CheckAdminPassword(), commands=['admin'], state="*")
async def admin_get_status_handler(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, await get_string('admin_got_status_message'),
                           reply_markup=await admin_menu_kb())
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('admin_sending_message_button'), state=AdminMenu.IsAdmin)
@dp.message_handler(TextEquals('admin_change_start_message_button'), state=AdminMenu.IsAdmin)
async def change_start_message_handler(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, await get_string('send_start_message_text'),
                           reply_markup=await common_skip_kb())
    await state.update_data(action=message.text)
    await ChangeStartMessage.SetText.set()


@dp.message_handler(TextEquals('common_skip_button'), state=ChangeStartMessage.SetText)
async def skip_change_start_message_text_handler(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, await get_string('send_start_message_data'),
                           reply_markup=await common_skip_kb())
    await ChangeStartMessage.SetData.set()


@dp.message_handler(state=ChangeStartMessage.SetText)
async def change_start_message_data_handler(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, await get_string('send_start_message_data'),
                           reply_markup=await common_skip_kb())

    await state.update_data(new_message_text=message.text)
    await ChangeStartMessage.SetData.set()


@dp.message_handler(TextEquals('common_skip_button'), state=ChangeStartMessage.SetData)
async def skip_change_start_message_data_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    new_message_text = data.get('new_message_text')
    text = await get_string('new_start_message')
    await bot.send_message(message.chat.id, text.format(new_message_text),
                           reply_markup=await common_reject_accept_kb(), parse_mode="MarkdownV2")

    await ChangeStartMessage.ConfirmChanges.set()


@dp.message_handler(state=ChangeStartMessage.SetData, content_types=ContentTypes.PHOTO | ContentTypes.DOCUMENT |
                                                                    ContentTypes.VIDEO | ContentTypes.VOICE)
async def set_start_message_data_handler(message: Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = 'photo'
    elif message.document:
        file_id = message.document.file_id
        file_type = 'document'
    elif message.voice:
        file_id = message.voice.file_id
        file_type = 'voice'
    elif message.video:
        file_id = message.video.file_id
        file_type = 'video'
    else:
        await bot.send_message(message.chat.id, await get_string('send_start_message_data'),
                               reply_markup=await common_skip_kb())
        return
    await state.update_data(file_id=file_id, file_type=file_type)

    data = await state.get_data()
    new_message_text = data.get('new_message_text')
    if new_message_text:
        text = await get_string('new_start_message')
        text = text.format(new_message_text)
    else:
        text = None
    reply_markup = await common_reject_accept_kb()
    if file_type == 'photo':
        await bot.send_photo(message.chat.id, file_id, caption=text, reply_markup=reply_markup, parse_mode="MarkdownV2")
    elif file_type == 'document':
        await bot.send_document(message.chat.id, file_id, caption=text, reply_markup=reply_markup,
                                parse_mode="MarkdownV2")
    elif file_type == 'voice':
        await bot.send_voice(message.chat.id, file_id, caption=text, reply_markup=reply_markup, parse_mode="MarkdownV2")
    elif file_type == 'video':
        await bot.send_video(message.chat.id, file_id, caption=text, reply_markup=reply_markup, parse_mode="MarkdownV2")
    elif text:
        await bot.send_message(message.chat.id, text, reply_markup=reply_markup, parse_mode="MarkdownV2")

    await ChangeStartMessage.ConfirmChanges.set()


@dp.message_handler(TextEquals('common_accept_button'), state=ChangeStartMessage.ConfirmChanges)
async def accept_changes_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    action = data['action']
    new_message_text = data.get('new_message_text', '')
    file_id = data.get('file_id', '')
    file_type = data.get('file_type', '')
    if action == await get_string("admin_change_start_message_button"):
        await edit_start_message(new_message_text)
        if file_id and file_type:
            await edit_start_message_file(f'{file_id}, {file_type}')
        else:
            await edit_start_message_file('')

        await bot.send_message(message.chat.id, 'Сохранено', reply_markup=await admin_menu_kb())
        await AdminMenu.IsAdmin.set()
    elif action == await get_string("admin_sending_message_button"):
        await bot.send_message(message.chat.id, 'Начал рассылку', reply_markup=await admin_menu_kb())
        await AdminMenu.IsAdmin.set()
        for user in Controller.users.select():
            try:
                if file_type == 'photo':
                    await bot.send_photo(user.tg_id, file_id, caption=new_message_text, parse_mode="MarkdownV2")
                elif file_type == 'document':
                    await bot.send_document(user.tg_id, file_id, caption=new_message_text, parse_mode="MarkdownV2")
                elif file_type == 'voice':
                    await bot.send_voice(user.tg_id, file_id, caption=new_message_text, parse_mode="MarkdownV2")
                elif file_type == 'video':
                    await bot.send_video(user.tg_id, file_id, caption=new_message_text, parse_mode="MarkdownV2")
                elif new_message_text:
                    await bot.send_message(user.tg_id, new_message_text, parse_mode="MarkdownV2")
            except Exception as e:
                print(e)
                pass
        await bot.send_message(message.chat.id, 'Рассылка завершена')


@dp.message_handler(TextEquals('common_reject_button'), state=ChangeStartMessage.ConfirmChanges)
async def reject_changes_handler(message: Message, state: FSMContext):
    await admin_get_status_handler(message, state)


@dp.message_handler(TextEquals('send_start_message_text'), state=ChangeStartMessage.SetText)
async def change_start_message_text_handler(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, await get_string('send_start_message_text'),
                           reply_markup=await common_skip_kb())
    await ChangeStartMessage.SetText.set()


@dp.message_handler(TextEquals('admin_switch_state_to_user_button'), state=AdminMenu.IsAdmin)
async def admin_switch_state_to_user_handler(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, message.text,
                           reply_markup=await user_menu_kb())
    await UserMenu.IsUser.set()


@dp.callback_query_handler(cancel_cb.filter(is_admin='True'), state='*')
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('admin_get_rooms_button'), state=AdminMenu.IsAdmin)
async def admin_get_rooms_handler(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, await get_string('select_level'),
                           reply_markup=await common_choose_level_inline_kb(10, True))
    await AdminMenu.SelectLevel.set()


@dp.callback_query_handler(text='common_back_button', state=AdminMenu.SelectRoom)
async def back_get_level_handler(callback: CallbackQuery, state: FSMContext):
    # await bot.send_message(message.chat.id, await get_string('select_level'),
    #                        reply_markup=await common_choose_level_inline_kb(10, True))
    await callback.message.edit_text(
        await get_string('select_level'), reply_markup=await common_choose_level_inline_kb(10, True)
    )
    await AdminMenu.SelectLevel.set()


@dp.callback_query_handler(state=AdminMenu.SelectLevel)
async def admin_get_level_handler(callback: CallbackQuery, state: FSMContext):
    level = int(callback.data.split(':')[-1])
    await state.update_data(level=level)
    rooms = await Controller.get_rooms_by_level(level)
    if not rooms:
        await callback.answer(await get_string('no_rooms_message'))
        return
    await callback.message.edit_text(
        await get_string('select_room_message'),
        reply_markup=await common_choose_room_inline_kb(rooms, True)
    )
    await AdminMenu.SelectRoom.set()


@dp.callback_query_handler(state=AdminMenu.SelectRoom)
async def admin_get_room_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    level = data['level']
    room_id = int(callback.data.split(':')[-1])
    room_hex_id = callback.data.split(':')[-2]
    users = await Controller.get_room_users(room_id)
    text = []
    for user in users:
        is_refer = await get_string('yes_message') if user.is_refer else await get_string('no_message')
        text.append(
            await get_string_with_args('room_user_message', user.full_name, user.username, is_refer, user.max_level))

    # await bot.send_message(
    #     callback.message.chat.id,
    #     await get_string_with_args('room_info_message', room_id, level, '\n'.join(text))
    # )
    await callback.message.edit_text(
        await get_string_with_args('room_info_message', room_id, level, '\n'.join(text)),
        reply_markup=await common_back_cancel_inline_kb(True)
    )
    # await state.reset_state()
    # await AdminMenu.IsAdmin.set()


# @dp.message_handler(TextEquals('admin_add_room_button'), state=AdminMenu.IsAdmin)
# async def add_room_handler(message: Message, state: FSMContext):
#     await bot.send_message(message.chat.id, await get_string('select_level'),
#                            reply_markup=await common_choose_level_inline_kb(10, True))
#     await AddRoom.RoomLevel.set()


@dp.callback_query_handler(state=AddRoom.ConfirmRoom)
async def accept_add_room_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'common_accept_il_button':
        data = await state.get_data()
        level = data['level']
        await Controller.add_room(int(level))
        await callback.answer(f'Стол на уровне {level} добавлен', show_alert=True)
    elif callback.data == 'common_reject_il_button':
        await callback.answer()
    await bot.edit_message_text(await get_string('select_level'), callback.message.chat.id, callback.message.message_id,
                                reply_markup=await common_choose_level_inline_kb(10, True))
    await AddRoom.RoomLevel.set()


@dp.callback_query_handler(state=AddRoom.RoomLevel)
async def get_room_handler(callback: CallbackQuery, state: FSMContext):
    level = callback.data.split(':')[-1]
    await state.update_data(level=level)
    await callback.message.edit_text(
        f'Добавить комнату на уровень {level}?',
        reply_markup=await common_reject_accept_inline_kb()
    )
    await AddRoom.ConfirmRoom.set()


@dp.message_handler(TextEquals('admin_get_refers_button'), state=AdminMenu.IsAdmin)
async def get_refers_handler(message: Message, state: FSMContext):
    refers = await Controller.get_all_refers()
    if not refers:
        return
    users = [
        (user.full_name, user.username, user.room_id, user.max_level) for user in refers
    ]
    n = 10
    users_split = [users[i:i + n] for i in range(0, len(users), n)]
    await state.set_state('users_list')
    count = len(users)
    await state.update_data(users_split=users_split, count=count)
    page_users = users_split[0]
    text = []
    for page_user in page_users:
        text.append(
            await get_string_with_args('refers_info_message', *page_user)
        )
    await message.answer(
        text='\n'.join(text),
        reply_markup=await paginate_markup(max_pages=len(users_split), page=1, count=count),
        parse_mode=ParseMode.HTML
    )


@dp.callback_query_handler(PaginateCallback.filter(), state='users_list')
async def get_paginate(query: CallbackQuery, callback_data: PaginateCallback, state: FSMContext):
    data = await state.get_data()
    users_split = data['users_split']
    next_page = int(callback_data.get('page'))
    page_users = users_split[next_page - 1]
    count = data['count']
    text = []
    for page_user in page_users:
        text.append(
            await get_string_with_args('refers_info_message', *page_user)
        )
    await query.message.edit_text(
        text='\n'.join(text),
        reply_markup=await paginate_markup(max_pages=len(users_split), page=next_page, count=count),
        parse_mode=ParseMode.HTML
    )


@dp.callback_query_handler(text='close_users', state='users_list')
async def close_users_handler(query: CallbackQuery, state: FSMContext):
    await query.message.delete()
    await state.finish()
    await AdminMenu.IsAdmin.set()


@dp.callback_query_handler(text='current_page', state='users_list')
async def current_page_handler(query: CallbackQuery, state: FSMContext):
    await query.answer(cache_time=60)
