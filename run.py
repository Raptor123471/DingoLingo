import os

import discord
from discord.ext import commands

from config import config
from musicbot.audiocontroller import AudioController
from musicbot.settings import Settings
from musicbot.utils import guild_to_audiocontroller, guild_to_settings

initial_extensions = ['musicbot.commands.music',
                      'musicbot.commands.general', 'musicbot.plugins.button']
bot = commands.Bot(command_prefix=config.BOT_PREFIX,
                   pm_help=True, case_insensitive=True,
                   status=discord.Status.online,
                   activity=discord.Game(name="Music, type {}help".format(config.BOT_PREFIX)))


@bot.event
async def on_ready():
    print(config.STARTUP_MESSAGE)

    for guild in bot.guilds:
        await register(guild)
        print("Joined {}".format(guild.name))

    print(config.STARTUP_COMPLETE_MESSAGE)


@bot.event
async def on_guild_join(guild):
    print(guild.name)
    await register(guild)


async def register(guild: discord.Guild):
    if guild in guild_to_settings:
        return

    sett = guild_to_settings[guild] = Settings(guild)
    controller = guild_to_audiocontroller[guild] = AudioController(bot, guild)

    if config.GLOBAL_DISABLE_AUTOJOIN_VC:
        return

    if not sett.get('vc_timeout'):
        try:
            await controller.register_voice_channel(
                guild.get_channel(sett.get('start_voice_channel'))
                or guild.voice_channels[0]
            )
        except Exception as e:
            print(e)


if __name__ == '__main__':

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
