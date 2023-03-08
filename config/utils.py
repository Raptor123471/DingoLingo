import os
import ast
from typing import TypeVar


T = TypeVar("T")


def get_env_var(key: str, default: T) -> T:
    value = os.getenv(key)
    if value is None:
        return default
    try:
        value = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        pass
    assert type(value) == type(default), f"invalid value for {key}: {value!r}"
    return value


def alchemize_url(url: str) -> str:
    SCHEMES = (
        ("sqlite", "sqlite+aiosqlite"),
        ("postgres", "postgresql+asyncpg"),
        ("mysql", "mysql+aiomysql"),
    )

    for name, scheme in SCHEMES:
        if url.startswith(name):
            return url.replace(name, scheme, 1)
    return url
