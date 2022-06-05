import os

import discord

from config import config
from musicbot.bot import MusicBot

initial_extensions = [
    "musicbot.commands.music",
    "musicbot.commands.general",
    "musicbot.plugins.button",
]


bot = MusicBot(
    command_prefix=config.BOT_PREFIX,
    pm_help=True,
    case_insensitive=True,
    status=discord.Status.online,
    activity=discord.Game(name="Music, type {}help".format(config.BOT_PREFIX)),
)


if __name__ == "__main__":

    config.ABSOLUTE_PATH = os.path.dirname(os.path.abspath(__file__))
    config.COOKIE_PATH = config.ABSOLUTE_PATH + config.COOKIE_PATH

    if not config.BOT_TOKEN:
        print("Error: No bot token!")
        exit()

    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(e)

    bot.run(config.BOT_TOKEN, bot=True, reconnect=True)
