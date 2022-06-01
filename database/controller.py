import random
from datetime import timedelta, datetime
from typing import Union, List, Tuple

from database.models import User, BotSettings, conn, Room, RoomQueue, get_datetime_now
from peewee import DoesNotExist, IntegrityError

from config.data import MAX_PLAYERS, ROOM_TIME, MAX_LEVEL


class Controller:
    def __init__(self):
        self.users = User
        self.settings = BotSettings
        self.rooms = Room
        self.queues = RoomQueue
        conn.connect()
        conn.create_tables([self.users, self.settings, self.rooms, self.queues], safe=True)
        conn.close()

    async def get_datetime_now(self) -> datetime:
        return get_datetime_now()

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
        # user = self.users.get(self.users.tg_id == tg_id)
        # user.update(kwargs).execute()
        self.users.update(kwargs).where(self.users.tg_id == tg_id).execute()

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
            end_at = now + timedelta(seconds=ROOM_TIME)
            return self.rooms.insert(level=level, created_at=created_at, end_at=end_at).execute()
            # return self.rooms.insert(level=level, created_at=created_at).execute()
        except IntegrityError:
            pass

    async def update_room(self, room_id: int, **kwargs):
        self.rooms.update(kwargs).where(self.rooms.id == room_id).execute()

    async def set_room_end_time(self, room_id: int, seconds: int = None) -> datetime:
        now = get_datetime_now()
        if not seconds:
            seconds = ROOM_TIME
        end_at = now + timedelta(seconds=seconds)
        self.rooms.update(end_at=end_at).where(self.rooms.id == room_id).execute()
        return end_at

    async def get_room(self, room_id: int, hex_id: str = None) -> Union[Room, None]:
        try:
            if hex_id:
                return self.rooms.get(self.rooms.id == room_id, self.rooms.hex_id == hex_id)
            else:
                return self.rooms.get(self.rooms.id == room_id)
        except DoesNotExist:
            return None

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
            user = self.users.get(self.users.tg_id == user_tg_id)
            wait_refer = room.wait_refer
            is_refer = False
            users_count = room.users_count
            if user.next_room_id == room_id:
                wait_refer = False
                is_refer = True
                new_users_count = users_count
            else:
                new_users_count = users_count + 1
            if (users_count == MAX_PLAYERS) and (user.next_room_id != room_id):
                return False, is_refer
            if users_count == 0:
                if self.users.select().where(self.users.next_room_id == room_id):
                    is_refer = False
                    wait_refer = True
                else:
                    is_refer = True
                    wait_refer = False
            self.rooms.update(users_count=new_users_count, wait_refer=wait_refer).where(self.rooms.id == room_id).execute()
            self.users.update(room_id=room_id, is_refer=is_refer).where(self.users.tg_id == user_tg_id).execute()
            return True, is_refer
        except DoesNotExist:
            return False, False

    async def add_refer_room(self, level: int, user_tg_id: int):
        empty_rooms = await self.get_empty_rooms(level)

        if not empty_rooms:
            room_id = await self.add_room(level)
            # now = get_datetime_now()
            # created_at = now
            # end_at = now + timedelta(seconds=ROOM_TIME)
            # room_id = self.rooms.insert(level=level, created_at=created_at, end_at=end_at).execute()
            room: Room = self.rooms.get(self.rooms.id == room_id)
            users_count = room.users_count
            wait_refer = True
            self.rooms.update(users_count=users_count + 1, wait_refer=wait_refer).where(self.rooms.id == room_id).execute()
            self.users.update(next_room_id=room_id).where(self.users.tg_id == user_tg_id).execute()
        else:
            room = empty_rooms[0]
            room_id = room.id
            users_count = room.users_count
            wait_refer = True
            self.rooms.update(users_count=users_count + 1, wait_refer=wait_refer).where(
                self.rooms.id == room_id).execute()
            self.users.update(next_room_id=room_id).where(self.users.tg_id == user_tg_id).execute()
        return room_id

    async def get_room_users_count(self, room_id: int) -> int:
        room: Room = self.rooms.get(self.rooms.id == room_id)
        return room.users_count

    async def remove_user_from_room(self, room_id: int, user_tg_id: int):
        room: Room = self.rooms.get(self.rooms.id == room_id)
        users_count = room.users_count
        if users_count == 0:
            return
        self.rooms.update(users_count=users_count - 1).where(self.rooms.id == room_id).execute()
        self.users.update(room_id=None, is_refer=False).where(self.users.tg_id == user_tg_id).execute()

    async def remove_room(self, room_id: int):
        try:
            room: Room = self.rooms.get(self.rooms.id == room_id)
        except DoesNotExist:
            return
        room_users = self.users.select().where(self.users.room_id == room_id)
        for room_user in room_users:
            self.users.update(room_id=None, is_refer=False).where(self.users.tg_id == room_user.tg_id).execute()
        self.rooms.delete().where(self.rooms.id == room_id).execute()

    async def get_room_refers(self, room_id: int) -> List[User]:
        return self.users.select().where((self.users.room_id == room_id) & (self.users.is_refer == True)) or \
               self.users.select().where(self.users.next_room_id == room_id)

    async def get_rooms_by_level(self, level: int) -> List[Room]:
        return self.rooms.select().where(self.rooms.level == level)

    async def get_free_rooms(self, level: int) -> List[Room]:
        return self.rooms.select().where((self.rooms.level == level) & (self.rooms.users_count < MAX_PLAYERS))

    async def get_empty_rooms(self, level: int) -> List[Room]:
        return self.rooms.select().where((self.rooms.level == level) & (self.rooms.users_count == 0))

    async def get_room_users(self, room_id) -> List[User]:
        return self.users.select().where(self.users.room_id == room_id)

    async def get_left_time(self, room_id) -> datetime:
        room: Room = self.rooms.get(self.rooms.id == room_id)
        delta = room.end_at - get_datetime_now()
        return delta

    async def get_all_refers(self):
        return self.users.select().where(self.users.is_refer == True).order_by(self.users.room_id)

    async def set_random_room_refer(self, room_id) -> Union[None, int]:
        try:
            room = self.rooms.get(self.rooms.id == room_id)
        except DoesNotExist:
            return
        if room.users_count == 0:
            return
        users = await self.get_room_users(room_id)
        new_refer = random.choice(users)
        self.users.update(is_refer=True).where(self.users.tg_id == new_refer.tg_id).execute()
        self.rooms.update(wait_refer=False).where(self.rooms.id == room_id).execute()
        level = room.level
        if level < MAX_LEVEL:
            next_level = level + 1
        else:
            next_level = level
        await self.add_refer_room(next_level, new_refer.tg_id)
        return new_refer.tg_id

    async def remove_refer_from_room(self, room_id, tg_id):
        room = self.rooms.get(self.rooms.id == room_id)
        # refer = self.users.get((self.users.tg_id == tg_id) & (self.users.is_refer == True))
        self.users.update(is_refer=False, next_room_id=None).where(self.users.tg_id == tg_id).execute()
        self.rooms.update(users_count=room.users_count-1).where(self.rooms.id == room_id).execute()

    async def clean_rooms(self):
        rooms = self.rooms.select()
        for room in rooms:
            await self.remove_room(room.id)
        self.users.update(next_room_id=None).execute()
