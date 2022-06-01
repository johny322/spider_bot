from configparser import ConfigParser

from aiogram.utils.callback_data import CallbackData

from .utils import validate_config

config = ConfigParser()
config.read('config.ini')

if not config.sections():
    validate_config(config)
    input('Файл конфигурации повреждён! Он будет восстановлен после нажатия Enter.\n'
          'Укажите данные запуска заново в файле config.ini!')
    quit()

TOKEN = config['BOT_SETTINGS']['Token']

if not TOKEN:
    input('В файле конфигурации не указан токен бота!\n'
          'Укажите токен бота в файле config.ini')
    quit()

ADMIN_PASS = config['BOT_SETTINGS']['AdminPassword'] if config['BOT_SETTINGS']['AdminPassword'] else '123'
REFERS_PER_PAGE = 10

MAX_PLAYERS = 3
ROOM_TIME = 60  # 24*60*60
WAIT_ROOM_TIME = 20  # 2*60*60
REFER_TIME = 50  # 30*60

MAX_LEVEL = 10
# url: https://t.me/
send_refer_request_cb = CallbackData('send_rq', 'action', 'room_id', 'user_tg_id', 'refer_id')
cancel_cb = CallbackData('cancel_cb', 'is_admin')
confirm_request_cb = CallbackData('confirm_rq', 'action', 'from_room_id', 'user_tg_id')
