import discord
from discord.ext import commands

from config import config
from musicbot.audiocontroller import AudioController
from musicbot import utils
from musicbot.utils import guild_to_audiocontroller

from musicbot.commands.general import General


initial_extensions = ['musicbot.commands.music',
                      'musicbot.commands.general', 'musicbot.button']
bot = commands.Bot(command_prefix=config.BOT_PREFIX, pm_help=True)

if __name__ == '__main__':

    if config.BOT_TOKEN == "":
        print("Error: No bot token!")
        exit

    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(e)


@bot.event
async def on_ready():
    print(config.STARTUP_MESSAGE)
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Music, type {}help".format(config.BOT_PREFIX)))

    config.BOT_VERISON = "0.9.7"

    for guild in bot.guilds:

        guild_to_audiocontroller[guild] = AudioController(bot, guild)

        await guild_to_audiocontroller[guild].register_voice_channel(guild.voice_channels[0])

        await General.udisconnect(self=None, ctx=None, guild=guild)

        try:
            await guild_to_audiocontroller[guild].register_voice_channel(guild.voice_channels[0])
        except:
            pass

        print("Joined {}".format(guild.name))

    print(config.STARTUP_COMPLETE_MESSAGE)


@bot.event
async def on_guild_join(guild):
    print(guild.name)
    guild_to_audiocontroller[guild] = AudioController(bot, guild)

    await guild_to_audiocontroller[guild].register_voice_channel(guild.voice_channels[0])


bot.run(config.BOT_TOKEN, bot=True, reconnect=True)
