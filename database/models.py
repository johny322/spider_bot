import uuid

from playhouse.sqliteq import SqliteQueueDatabase
from peewee import Model, PrimaryKeyField, IntegerField, TextField, Check, BooleanField, DateTimeField, AutoField
from datetime import datetime

import pytz


def get_datetime_now() -> datetime:
    return datetime.now(pytz.timezone("Europe/Moscow")).replace(tzinfo=None)


def get_room_hex() -> str:
    return uuid.uuid4().hex


conn = SqliteQueueDatabase('main.db')


class BaseModel(Model):
    class Meta:
        database = conn


class BotSettings(BaseModel):
    id = PrimaryKeyField(null=False, constraints=[Check('id=1')])


class User(BaseModel):
    id = PrimaryKeyField(null=False)
    tg_id = IntegerField(null=False, unique=True)
    username = TextField(null=True)
    full_name = TextField(null=True)
    room_id = IntegerField(null=True)
    max_level = IntegerField(default=1)
    is_refer = BooleanField(default=False)


class RoomQueue(BaseModel):
    id = PrimaryKeyField(null=False)
    room_level = IntegerField(null=False)
    users = TextField(null=True)


class Room(BaseModel):
    id = AutoField(primary_key=True, null=False, unique=True)
    hex_id = TextField(default=get_room_hex)
    level = IntegerField(null=False)
    # users = TextField(null=True)
    created_at = DateTimeField(default=get_datetime_now)
    end_at = DateTimeField(null=False)
    users_count = IntegerField(default=0)
