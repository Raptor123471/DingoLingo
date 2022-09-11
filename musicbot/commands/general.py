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
        description=config.HELP_DISCONNECT_LONG,
        help=config.HELP_DISCONNECT_SHORT,
        aliases=["rs", "restart"],
    )
    async def _reset(self, ctx: Context):
        await ctx.bot.audio_controllers[ctx.guild].stop_player()
        await ctx.guild.voice_client.disconnect(force=True)

        ctx.bot.audio_controllers[ctx.guild] = AudioController(self.bot, ctx.guild)
        await ctx.bot.audio_controllers[ctx.guild].register_voice_channel(
            ctx.author.voice.channel
        )

        await ctx.send(
            "{} Connected to {}".format(
                ":white_check_mark:", ctx.author.voice.channel.name
            )
        )

    @commands.command(
        name="changechannel",
        description=config.HELP_CHANGECHANNEL_LONG,
        help=config.HELP_CHANGECHANNEL_SHORT,
        aliases=["cc"],
    )
    async def _change_channel(self, ctx: Context):
        vchannel = await utils.is_connected(ctx)
        if vchannel == ctx.author.voice.channel:
            await ctx.send(
                "{} Already connected to {}".format(":white_check_mark:", vchannel.name)
            )
            return

        await ctx.bot.audio_controllers[ctx.guild].stop_player()
        await ctx.guild.voice_client.disconnect(force=True)

        ctx.bot.audio_controllers[ctx.guild] = AudioController(self.bot, ctx.guild)
        await ctx.bot.audio_controllers[ctx.guild].register_voice_channel(
            ctx.author.voice.channel
        )

        await ctx.send(
            "{} Switched to {}".format(
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
        description=config.HELP_SETTINGS_LONG,
        help=config.HELP_SETTINGS_SHORT,
        aliases=["settings", "set"],
    )
    @has_permissions(administrator=True)
    async def _settings(self, ctx: Context, *args):

        sett = ctx.bot.settings[ctx.guild]

        if len(args) == 0:
            await ctx.send(embed=await sett.format())
            return

        args_list = list(args)
        args_list.remove(args[0])

        response = await sett.write(args[0], " ".join(args_list), ctx)

        if response is None:
            await ctx.send("`Error: Setting not found`")
        elif response is True:
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
