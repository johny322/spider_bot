from configparser import ConfigParser

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

MAX_PLAYERS = 9
ROOM_TIME = 6*60*60
REFER_TIME = 30*60
# url: https://t.me/
