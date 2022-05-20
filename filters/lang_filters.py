from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message

from languages import get_string


class TextEquals(BoundFilter):
    def __init__(self, string_code: str, lang_code: str = 'ru'):
        self.string_code = string_code
        self.lang_code = lang_code

    async def check(self, message: Message) -> bool:
        return True if await get_string(self.string_code, self.lang_code) == message.text.strip() else False
