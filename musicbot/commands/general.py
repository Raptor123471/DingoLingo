import discord
from config import config
from discord.ext import commands
from discord.ext.commands import has_permissions
from musicbot import utils
from musicbot.bot import Context, MusicBot
from musicbot.audiocontroller import AudioController


class General(commands.Cog):
    """A collection of the commands for moving the bot around in you server.

    Attributes:
        bot: The instance of the bot that is executing the commands.
    """

    def __init__(self, bot: MusicBot):
        self.bot = bot

    # logic is split to uconnect() for wide usage
    @commands.command(
        name="connect",
        description=config.HELP_CONNECT_LONG,
        help=config.HELP_CONNECT_SHORT,
        aliases=["c"],
    )
    async def _connect(self, ctx: Context):  # dest_channel_name: str
        audiocontroller = ctx.bot.audio_controllers[ctx.guild]
        await audiocontroller.uconnect(ctx)

    @commands.command(
        name="disconnect",
        description=config.HELP_DISCONNECT_LONG,
        help=config.HELP_DISCONNECT_SHORT,
        aliases=["dc"],
    )
    async def _disconnect(self, ctx: Context):
        audiocontroller = ctx.bot.audio_controllers[ctx.guild]
        await audiocontroller.udisconnect()

    @commands.command(
        name="reset",
        description=config.HELP_RESET_LONG,
        help=config.HELP_RESET_SHORT,
        aliases=["rs", "restart", "cc"],  # this command replaces removed changechannel
    )
    async def _reset(self, ctx: Context):
        await ctx.defer()
        if await ctx.bot.audio_controllers[ctx.guild].udisconnect():
            # bot was connected and need some rest
            await asyncio.sleep(1)

        audiocontroller = ctx.bot.audio_controllers[ctx.guild] = AudioController(
            self.bot, ctx.guild
        )
        if await audiocontroller.uconnect(ctx):
            await ctx.send(
                "{} Connected to {}".format(
                    ":white_check_mark:", ctx.author.voice.channel.name
                )
            )

    @commands.command(
        name="ping", description=config.HELP_PING_LONG, help=config.HELP_PING_SHORT
    )
    async def _ping(self, ctx):
        await ctx.send("Pong")

    @commands.command(
        name="setting",
        description=config.HELP_SHUFFLE_LONG,
        help=config.HELP_SETTINGS_SHORT,
        aliases=["settings", "set"],
    )
    @has_permissions(administrator=True)
    async def _settings(self, ctx: Context, *args):

        sett = ctx.bot.settings[ctx.guild]

        if len(args) == 0:
            await ctx.send(embed=sett.format(ctx))
            return

        response = await sett.process_setting(args[0], " ".join(args[1:]), ctx)

        if response is None:
            await ctx.send("`Error: Setting not found`")
        elif response is True:
            async with ctx.bot.DbSession() as session:
                session.add(sett)
                await session.commit()
            await ctx.send("Setting updated!")

    @commands.command(
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
