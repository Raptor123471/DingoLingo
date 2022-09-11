import os

import discord
from discord.ext import commands

from config import config
from musicbot.bot import MusicBot
from musicbot.utils import check_dependencies

initial_extensions = [
    "musicbot.commands.music",
    "musicbot.commands.general",
]


intents = discord.Intents.default()
if config.BOT_PREFIX is not None:
    intents.message_content = True
    prefix = config.BOT_PREFIX
else:
    config.BOT_PREFIX = config.actual_prefix
    prefix = " "  # messages can't start with space
if config.MENTION_AS_PREFIX:
    prefix = commands.when_mentioned_or(prefix)

if config.ENABLE_BUTTON_PLUGIN:
    intents.message_content = True
    initial_extensions.append("musicbot.plugins.button")

bot = MusicBot(
    command_prefix=prefix,
    case_insensitive=True,
    status=discord.Status.online,
    activity=discord.Game(name="Music, type {}help".format(config.BOT_PREFIX)),
    intents=intents,
    allowed_mentions=discord.AllowedMentions.none(),
)


if __name__ == "__main__":

    config.ABSOLUTE_PATH = os.path.dirname(os.path.abspath(__file__))
    config.COOKIE_PATH = config.ABSOLUTE_PATH + config.COOKIE_PATH

    check_dependencies()

    if not config.BOT_TOKEN:
        print("Error: No bot token!")
        exit()

    bot.load_extensions(*initial_extensions)

    bot.run(config.BOT_TOKEN, reconnect=True)
