from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message


from config import ADMIN_PASS


class CheckAdminPassword(BoundFilter):
    async def check(self, message: Message) -> bool:
        if not message.get_args():
            return False

        return True if message.get_args().strip() == ADMIN_PASS else False
