"This file is here to automatically install the selected DB package"
from setuptools import setup
from typing import Type, TypeVar

DATABASE = "sqlite+aiosqlite:///settings.db"


setup(
    name="MusicBot DB",
    install_requires=[DATABASE.partition("+")[2].partition(":")[0]],
)


T = TypeVar('T')

def get_env_var(key: str, fallback: T) -> T:
    if key in os.environ:
        return type(fallback)(os.environ[key])
    return fallback


