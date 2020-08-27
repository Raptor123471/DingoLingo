import os
from discord.ext import commands

from config import config
from musicbot import utils
from musicbot.audiocontroller import AudioController
from musicbot.utils import guild_to_audiocontroller


class General(commands.Cog):
    """ A collection of the commands for moving the bot around in you server.

            Attributes:
                bot: The instance of the bot that is executing the commands.
    """

    def __init__(self, bot):
        self.bot = bot

    # logic is split to uconnect() for wide usage
    @commands.command(name='connect', description=config.HELP_CONNECT_LONG, help=config.HELP_CONNECT_SHORT, aliases=['c'])
    async def _connect(self, ctx):  # dest_channel_name: str
        await self.uconnect(ctx)

    async def uconnect(self, ctx):

        vchannel = await utils.is_connected(ctx)

        if vchannel is not None:
            if ctx.author.voice.channel == vchannel:
                return

            else:
                current_guild = utils.get_guild(self.bot, ctx.message)
                await utils.guild_to_audiocontroller[current_guild].stop_player()
                await current_guild.voice_client.disconnect(force=True)

        current_guild = utils.get_guild(self.bot, ctx.message)

        if current_guild is None:
            await utils.send_message(ctx, config.NO_GUILD_MESSAGE)
            return

        if utils.guild_to_audiocontroller[current_guild] is None:
            utils.guild_to_audiocontroller[current_guild] = AudioController(
                self.bot, current_guild)

        guild_to_audiocontroller[current_guild] = AudioController(
            self.bot, current_guild)
        await guild_to_audiocontroller[current_guild].register_voice_channel(ctx.author.voice.channel)

        await ctx.send("Connected to {} {}".format(ctx.author.voice.channel.name, ":white_check_mark:"))

    @commands.command(name='disconnect', description=config.HELP_DISCONNECT_LONG, help=config.HELP_DISCONNECT_SHORT, aliases=['dc'])
    async def _disconnect(self, ctx, guild=False):
        await self.udisconnect(ctx, guild)

    async def udisconnect(self, ctx, guild):

        if guild is not False:

            current_guild = guild

            await utils.guild_to_audiocontroller[current_guild].stop_player()
            await current_guild.voice_client.disconnect(force=True)

        else:
            current_guild = utils.get_guild(self.bot, ctx.message)

            if current_guild is None:
                await utils.send_message(ctx, config.NO_GUILD_MESSAGE)
                return

            if await utils.is_connected(ctx) is None:
                try:
                    await utils.guild_to_audiocontroller[current_guild].stop_player()
                    await current_guild.voice_client.disconnect(force=True)
                    await ctx.send("Disconnected from voice channel. Use '{}c' to rejoin.".format(config.BOT_PREFIX))
                except:
                    pass
                await utils.send_message(ctx, config.NO_GUILD_MESSAGE)
                return

            await utils.guild_to_audiocontroller[current_guild].stop_player()
            await current_guild.voice_client.disconnect(force=True)
            await ctx.send("Disconnected from voice channel. Use '{}c' to rejoin.".format(config.BOT_PREFIX))

    @commands.command(name='reset', description=config.HELP_DISCONNECT_LONG, help=config.HELP_DISCONNECT_SHORT, aliases=['rs', 'restart'])
    async def _reset(self, ctx):
        current_guild = utils.get_guild(self.bot, ctx.message)

        if current_guild is None:
            await utils.send_message(ctx, config.NO_GUILD_MESSAGE)
            return
        await utils.guild_to_audiocontroller[current_guild].stop_player()
        await current_guild.voice_client.disconnect(force=True)

        guild_to_audiocontroller[current_guild] = AudioController(
            self.bot, current_guild)
        await guild_to_audiocontroller[current_guild].register_voice_channel(guild.voice_channels[0])

        await ctx.send("{} Connected to {}".format(":white_check_mark:", guild.voice_channels[0].name))


    @commands.command(name='changechannel', aliases=['cc'])
    async def _change_channel(self, ctx):
        current_guild = utils.get_guild(self.bot, ctx.message)

        if current_guild is None:
            await utils.send_message(ctx, config.NO_GUILD_MESSAGE)
            return
        await utils.guild_to_audiocontroller[current_guild].stop_player()
        await current_guild.voice_client.disconnect(force=True)

        guild_to_audiocontroller[current_guild] = AudioController(
            self.bot, current_guild)
        await guild_to_audiocontroller[current_guild].register_voice_channel(ctx.author.voice.channel)

        await ctx.send("{} Connected to {}".format(":white_check_mark:", ctx.author.voice.channel.name))

    @commands.command(name='ping')
    async def _ping(self, ctx):
        await ctx.send("Pong")

    @commands.command(name='version', aliases=['v'])
    async def _version(self, ctx):
        await ctx.send(config.BOT_VERISON)


def setup(bot):
    bot.add_cog(General(bot))
