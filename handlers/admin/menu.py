from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ContentType, ContentTypes, CallbackQuery

from admin_utils import get_start_message, edit_start_message
from admin_utils.start_message import edit_start_message_file
from controller__init import Controller
from keyboards import admin_menu_kb, user_menu_kb, common_skip_kb, common_reject_accept_kb, \
    common_choose_level_inline_kb, common_reject_accept_inline_kb, cancel_cb
from languages import get_string
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


@dp.message_handler(TextEquals('admin_add_room_button'), state=AdminMenu.IsAdmin)
async def add_room_handler(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, await get_string('select_level'),
                           reply_markup=await common_choose_level_inline_kb(10, True))
    await AddRoom.RoomLevel.set()


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
