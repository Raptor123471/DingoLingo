"This file is here to automatically install the selected DB package"
import os
from setuptools import setup

# database url in SQL Alchemy-supported format, must be async-compatible
# CHANGE ONLY IF YOU KNOW WHAT YOU'RE DOING
DATABASE = "sqlite+aiosqlite:///settings.db"
if os.getenv("HEROKU"):
    # example with Heroku Postgres
    DATABASE = os.getenv(
        "DATABASE_URL",  # environment variable with the DB url
        "postgres",  # default url (as env vars are not available at build time)
    ).replace(
        "postgres", "postgresql+asyncpg", 1  # make url supported by SQL Alchemy
    )
    # another example with MySQL
    # DATABASE = os.getenv("DATABASE_URL", "mysql").replace("mysql", "mysql+aiomysql", 1)

setup(
    name="MusicBot DB",
    install_requires=[DATABASE.partition("+")[2].partition(":")[0]],
)




