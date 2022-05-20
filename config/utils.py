from configparser import ConfigParser


def validate_config(config: ConfigParser):
    config['BOT_SETTINGS'] = {'Token': '',
                              'AdminPassword': '123'}
    with open('config.ini', 'w') as config_file:
        config.write(config_file)
