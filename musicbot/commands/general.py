import asyncio

import discord
from discord.ext import commands, bridge
from discord.ext.commands import has_permissions

from config import config
from musicbot.bot import Context, MusicBot
from musicbot.settings import CONFIG_OPTIONS, ConversionError
from musicbot.audiocontroller import AudioController


class General(commands.Cog):
    """A collection of the commands for moving the bot around in you server.

    Attributes:
        bot: The instance of the bot that is executing the commands.
    """

    def __init__(self, bot: MusicBot):
        self.bot = bot

    # logic is split to uconnect() for wide usage
    @bridge.bridge_command(
        name="connect",
        description=config.HELP_CONNECT_LONG,
        help=config.HELP_CONNECT_SHORT,
        aliases=["c", "cc"],  # this command replaces removed changechannel
    )
    async def _connect(self, ctx: Context):  # dest_channel_name: str
        audiocontroller = ctx.bot.audio_controllers[ctx.guild]
        await audiocontroller.uconnect(ctx, move=True)
        await ctx.send("Connected.")

    @bridge.bridge_command(
        name="disconnect",
        description=config.HELP_DISCONNECT_LONG,
        help=config.HELP_DISCONNECT_SHORT,
        aliases=["dc"],
    )
    async def _disconnect(self, ctx: Context):
        audiocontroller = ctx.bot.audio_controllers[ctx.guild]
        if await audiocontroller.udisconnect():
            await ctx.send("Disconnected.")
        else:
            await ctx.send(config.NOT_CONNECTED_MESSAGE)

    @bridge.bridge_command(
        name="reset",
        description=config.HELP_RESET_LONG,
        help=config.HELP_RESET_SHORT,
        aliases=["rs", "restart"],
    )
    async def _reset(self, ctx: Context):
        await ctx.defer()
        if await ctx.bot.audio_controllers[ctx.guild].udisconnect():
            # bot was connected and need some rest
            await asyncio.sleep(1)

        audiocontroller = ctx.bot.audio_controllers[ctx.guild] = AudioController(
            self.bot, ctx.guild
        )
        await audiocontroller.uconnect(ctx)
        await ctx.send(
            "{} Connected to {}".format(
                ":white_check_mark:", ctx.author.voice.channel.name
            )
        )

    @bridge.bridge_command(
        name="ping", description=config.HELP_PING_LONG, help=config.HELP_PING_SHORT
    )
    async def _ping(self, ctx):
        await ctx.send("Pong")

    @bridge.bridge_group(
        name="setting",
        description=config.HELP_SETTINGS_LONG,
        help=config.HELP_SETTINGS_SHORT,
        aliases=["settings", "set"],
        invoke_without_command=True,
    )
    @has_permissions(administrator=True)
    async def _settings(self, ctx: Context, *, inexistent_setting=None):
        if inexistent_setting is not None:
            await ctx.send("`Error: Setting not found`")
        else:
            await self._show_settings_callback(ctx)

    async def _show_settings_callback(self, ctx: Context):
        sett = ctx.bot.settings[ctx.guild]
        await ctx.send(embed=sett.format(ctx))

    _show_settings = _settings.command(name="show")(_show_settings_callback)

    for name, type_ in CONFIG_OPTIONS.items():

        @_settings.command(name=name)
        async def _set_setting(self, ctx: Context, *, value: type_):
            sett = ctx.bot.settings[ctx.guild]
            try:
                sett.process_setting(ctx.command.name, value, ctx)
            except ConversionError as e:
                await ctx.send(f"`Error: {e}`")
                return

            print(f"{ctx.command.name}, {type(value)}, {value}")
            async with ctx.bot.DbSession() as session:
                session.add(sett)
                await session.commit()
            await ctx.send("Setting updated!")

    @bridge.bridge_command(
        name="addbot",
        description=config.HELP_ADDBOT_LONG,
        help=config.HELP_ADDBOT_SHORT,
    )
    async def _addbot(self, ctx):
        embed = discord.Embed(
            title="Invite",
            description=config.ADD_MESSAGE
            + "({})".format(discord.utils.oauth_url(self.bot.user.id)),
        )

        await ctx.send(embed=embed)


def setup(bot: MusicBot):
    bot.add_cog(General(bot))
