from datetime import timedelta, datetime
from typing import Union, List, Tuple

from database.models import User, BotSettings, conn, Room, RoomQueue, get_datetime_now
from peewee import DoesNotExist, IntegrityError

from config.data import MAX_PLAYERS


# MAX_PLAYERS = 2


class Controller:
    def __init__(self):
        self.users = User
        self.settings = BotSettings
        self.rooms = Room
        self.queues = RoomQueue
        conn.connect()
        conn.create_tables([self.users, self.settings, self.rooms, self.queues], safe=True)
        conn.close()

    async def get_settings(self) -> BotSettings:
        try:
            return self.settings.get()
        except DoesNotExist:
            self.settings.insert().execute()
        return self.settings.get()

    async def update_settings(self, **kwargs) -> None:
        try:
            self.settings.insert(kwargs).execute()
        except IntegrityError:
            self.settings.update(kwargs).execute()

    async def user_exist(self, tg_id: int) -> bool:
        try:
            self.users.get(self.users.tg_id == tg_id)
        except DoesNotExist:
            return False
        return True

    async def update_user(self, tg_id, **kwargs):
        user = self.users.get(self.users.tg_id == tg_id)
        user.update(kwargs).execute()

    async def add_user(self, tg_id: int, username: Union[str, None], full_name: Union[str, None]) -> None:
        try:
            self.users.insert(tg_id=tg_id, username=username, full_name=full_name).execute()
        except IntegrityError:
            pass

    async def get_user(self, tg_id: int = None, username: str = None) -> Union[None, User]:
        if tg_id is None and username is None:
            pass
        if tg_id is not None and username is not None:
            return self.users.get_or_none((self.users.tg_id == tg_id) & (self.users.username == username))
        return self.users.get_or_none(self.users.tg_id == tg_id if tg_id is not None
                                      else self.users.username == username)

    async def remove_user(self, tg_id: int = None, username: Union[str, None] = None) -> None:
        if tg_id is None and username is None:
            pass
        try:
            if tg_id is None:
                self.users.delete().where(self.users.username == username).execute()
            elif username is None:
                self.users.delete().where(self.users.tg_id == tg_id).execute()
            else:
                self.users.delete().where((self.users.username == username) & (self.users.tg_id == tg_id)).execute()
        except DoesNotExist:
            pass

    async def add_room(self, level: int) -> int:
        try:
            now = get_datetime_now()
            created_at = now
            end_at = now + timedelta(hours=6)
            return self.rooms.insert(level=level, created_at=created_at, end_at=end_at).execute()
        except IntegrityError:
            pass

    async def get_room(self, room_id: int) -> Room:
        return self.rooms.get(self.rooms.id == room_id)

    async def room_exist(self, room_id: int, hex_id: str) -> bool:
        try:
            self.rooms.get((self.rooms.id == room_id) & (self.rooms.hex_id == hex_id))
        except DoesNotExist:
            return False
        return True

    async def add_user_to_queue(self, room_level: int, user_tg_id: int):
        try:
            queue: RoomQueue = self.queues.get(self.queues.room_level == room_level)
            try:
                queue_users = queue.users.split(',')
            except AttributeError:
                queue_users = []
            user_tg_id = str(user_tg_id)
            if user_tg_id not in queue_users:
                queue_users.append(user_tg_id)
            queue.update(users=','.join(queue_users)).execute()
        except DoesNotExist:
            self.queues.insert(room_level=room_level, users=user_tg_id).execute()

    async def add_user_to_room(self, room_id: int, user_tg_id: int) -> Tuple[bool, bool]:
        try:
            room: Room = self.rooms.get(self.rooms.id == room_id)
            is_refer = False
            users_count = room.users_count
            if users_count == MAX_PLAYERS:
                return False, is_refer
            if users_count == 0:
                is_refer = True
            # try:
            #     room_users = room.users.split(',')
            # except AttributeError:
            #     room_users = []

            # if len(room_users) == MAX_PLAYERS:
            #     return False, False
            # if not room_users:
            #     is_refer = True
            # if str(user_tg_id) not in room_users:
            #     room_users.append(str(user_tg_id))
            # room.update(users=','.join(room_users)).execute()
            # room.update(users_count=users_count + 1).execute()
            self.rooms.update(users_count=users_count + 1).where(self.rooms.id == room_id).execute()
            # user = self.users.get(self.users.tg_id == user_tg_id)
            self.users.update(room_id=room_id, is_refer=is_refer).where(self.users.tg_id == user_tg_id).execute()
            # await self.update_user(user_tg_id, room_id=room_id, is_refer=is_refer)
            return True, is_refer
        except DoesNotExist:
            return False, False

    async def get_room_users_count(self, room_id: int) -> int:
        room: Room = self.rooms.get(self.rooms.id == room_id)
        return room.users_count

    # async def get_room_users(self, room_id: int) -> List[str]:
    #     room: Room = self.rooms.get(self.rooms.id == room_id)
    #     try:
    #         room_users = room.users.split(',')
    #     except AttributeError:
    #         room_users = []
    #     return room_users

    async def remove_user_from_room(self, room_id: int, user_tg_id: int):
        room: Room = self.rooms.get(self.rooms.id == room_id)
        users_count = room.users_count
        # room.update(users_count=users_count - 1).execute()
        if users_count == 0:
            return
        self.rooms.update(users_count=users_count - 1).where(self.rooms.id == room_id).execute()
        # user = self.users.get(self.users.tg_id == user_tg_id)
        # user.update(room_id=None, is_refer=False).execute()
        self.users.update(room_id=None, is_refer=False).where(self.users.tg_id == user_tg_id).execute()
        # await self.update_user(user_tg_id, room_id=None, is_refer=False)
        # room_users: list = room.users.split(',')
        # room_users.remove(str(user_tg_id))
        # users = ','.join(room_users) if room_users else None
        # room.update(users=users).execute()
        # await self.update_user(user_tg_id, room_id=None, is_refer=False)

    async def remove_room(self, room_id: int):
        room: Room = self.rooms.get(self.rooms.id == room_id)
        room_users = self.users.select().where(self.users.room_id == room_id)
        for room_user in room_users:
            self.users.update(room_id=None, is_refer=False).where(self.users.tg_id == room_user.tg_id).execute()
            # room_user.update(room_id=None, is_refer=False).execute()
            # await self.update_user(room_user.tg_id, room_id=None, is_refer=False)
        # room.delete().execute()
        self.rooms.delete().where(self.rooms.id == room_id).execute()

    async def get_room_refers(self, room_id: int) -> List[User]:
        return self.users.select().where((self.users.room_id == room_id) & (self.users.is_refer == True))

    async def make_user_refer(self, tg_id: int):
        pass

    async def get_rooms_by_level(self, level: int) -> List[Room]:
        return self.rooms.select().where(self.rooms.level == level)

    async def get_free_rooms(self, level: int) -> List[Room]:
        return self.rooms.select().where((self.rooms.level == level) & (self.rooms.users_count < MAX_PLAYERS))

    async def get_room_users(self, room_id) -> List[User]:
        return self.users.select().where(self.users.room_id == room_id)

    async def get_left_time(self, room_id) -> datetime:
        room: Room = self.rooms.get(self.rooms.id == room_id)
        delta = room.end_at - get_datetime_now()
        return delta
