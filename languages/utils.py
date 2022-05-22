from typing import Union

from .strings import strings, levels_cost


async def get_string(string_code: str, lang_code: str = 'ru') -> Union[str, None]:
    try:
        return strings[lang_code][string_code]
    except KeyError:
        return None


async def get_string_with_args(string_code: str, *args, lang_code: str = 'ru') -> str:
    string = await get_string(string_code, lang_code)
    return string.format(*args) if string is not None else None


async def get_level_cost(level: int) -> int:
    return levels_cost[level]
