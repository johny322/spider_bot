from languages import get_string

from aiofiles import open


async def get_start_message():
    try:
        async with open('start_message.txt', 'r', encoding='utf8') as file:
            return await file.read()
    except FileNotFoundError:
        async with open('start_message.txt', 'w', encoding='utf8') as file:
            await file.write(await get_string('common_default_start_message'))
            return await get_string('common_default_start_message')


async def edit_start_message(new_start_message: str):
    async with open('start_message.txt', 'w', encoding='utf8') as file:
        await file.write(new_start_message)


async def get_start_message_file():
    try:
        async with open('start_message_file.txt', 'r', encoding='utf8') as file:
            return await file.read()
    except FileNotFoundError:
        async with open('start_message_file.txt', 'w', encoding='utf8') as file:
            await file.write(await get_string('common_default_start_message'))
            return None


async def edit_start_message_file(new_start_message_file: str):
    async with open('start_message_file.txt', 'w', encoding='utf8') as file:
        await file.write(new_start_message_file)
