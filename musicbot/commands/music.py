import discord
from config import config
from discord.ext import commands
from musicbot import linkutils, utils
from musicbot.bot import MusicBot, Context


class Music(commands.Cog):
    """A collection of the commands related to music playback.

    Attributes:
        bot: The instance of the bot that is executing the commands.
    """

    def __init__(self, bot: MusicBot):
        self.bot = bot

    @commands.command(
        name="play",
        description=config.HELP_YT_LONG,
        help=config.HELP_YT_SHORT,
        aliases=["p", "yt", "pl"],
    )
    async def _play_song(self, ctx: Context, *, track: str):

        if not await utils.play_check(ctx):
            return

        if track.isspace() or not track:
            return

        audiocontroller = ctx.bot.audio_controllers[ctx.guild]

        # reset timer
        audiocontroller.timer.cancel()
        audiocontroller.timer = utils.Timer(audiocontroller.timeout_handler)

        # if audiocontroller.playlist.loop == True:
        #     await ctx.send("Loop is enabled! Use {}loop to disable".format(config.BOT_PREFIX))
        #     return

        song = await audiocontroller.process_song(track)

        if song is None:
            await ctx.send(config.SONGINFO_ERROR)
            return

        if song.origin == linkutils.Origins.Playlist:
            await ctx.send(config.SONGINFO_PLAYLIST_QUEUED)
        else:
            if (
                audiocontroller.current_song
                and len(audiocontroller.playlist.playque) == 0
            ):
                await ctx.send(
                    embed=song.info.format_output(config.SONGINFO_NOW_PLAYING)
                )
            else:
                await ctx.send(
                    embed=song.info.format_output(config.SONGINFO_QUEUE_ADDED)
                )

    @commands.command(
        name="loop",
        description=config.HELP_LOOP_LONG,
        help=config.HELP_LOOP_SHORT,
        aliases=["l"],
    )
    async def _loop(self, ctx: Context, mode=None):

        audiocontroller = ctx.bot.audio_controllers[ctx.guild]

        if not await utils.play_check(ctx):
            return

        if not audiocontroller.is_active():
            await ctx.send("No songs in queue!")
            return

        if mode is None:
            if audiocontroller.playlist.loop == "off":
                mode = "all"
            else:
                mode = "off"

        if mode not in ("all", "single", "off"):
            await ctx.send("Invalid loop mode!")
            return

        audiocontroller.playlist.loop = mode

        if mode in ("all", "single"):
            await ctx.send("Loop enabled :arrows_counterclockwise:")
        else:
            await ctx.send("Loop disabled :x:")

    @commands.command(
        name="shuffle",
        description=config.HELP_SHUFFLE_LONG,
        help=config.HELP_SHUFFLE_SHORT,
        aliases=["sh"],
    )
    async def _shuffle(self, ctx: Context):
        audiocontroller = ctx.bot.audio_controllers[ctx.guild]

        if not await utils.play_check(ctx):
            return

        if len(audiocontroller.playlist.playque) == 0:
            await ctx.send(config.QUEUE_EMPTY)
            return

        audiocontroller.playlist.shuffle()
        await ctx.send("Shuffled queue :twisted_rightwards_arrows:")

        for song in list(audiocontroller.playlist.playque)[: config.MAX_SONG_PRELOAD]:
            audiocontroller.add_task(audiocontroller.preload(song))

    @commands.command(
        name="pause", description=config.HELP_PAUSE_LONG, help=config.HELP_PAUSE_SHORT
    )
    async def _pause(self, ctx: Context):
        if not await utils.play_check(ctx):
            return

        if ctx.guild.voice_client is None:
            return

        if ctx.guild.voice_client.is_paused():
            return await self._resume(ctx)

        if not ctx.guild.voice_client.is_playing():
            return

        ctx.guild.voice_client.pause()
        await ctx.send("Playback Paused :pause_button:")

    @commands.command(
        name="queue",
        description=config.HELP_QUEUE_LONG,
        help=config.HELP_QUEUE_SHORT,
        aliases=["playlist", "q"],
    )
    async def _queue(self, ctx: Context):
        if not await utils.play_check(ctx):
            return

        audiocontroller = ctx.bot.audio_controllers[ctx.guild]
        if not audiocontroller.is_active():
            await ctx.send(config.QUEUE_EMPTY)
            return

        playlist = audiocontroller.playlist

        # Embeds are limited to 25 fields
        if config.MAX_SONG_PRELOAD > 25:
            config.MAX_SONG_PRELOAD = 25

        embed = discord.Embed(
            title=":scroll: Queue [{}]".format(len(playlist.playque)),
            color=config.EMBED_COLOR,
            inline=False,
        )

        for counter, song in enumerate(
            list(playlist.playque)[: config.MAX_SONG_PRELOAD], start=1
        ):
            embed.add_field(
                name="{}.".format(str(counter)),
                value="[{}]({})".format(
                    song.info.title or song.info.webpage_url, song.info.webpage_url
                ),
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command(
        name="stop",
        description=config.HELP_STOP_LONG,
        help=config.HELP_STOP_SHORT,
        aliases=["st"],
    )
    async def _stop(self, ctx: Context):
        if not await utils.play_check(ctx):
            return

        audiocontroller = ctx.bot.audio_controllers[ctx.guild]
        audiocontroller.playlist.loop = "off"
        await audiocontroller.stop_player()
        await ctx.send("Stopped all sessions :octagonal_sign:")

    @commands.command(
        name="move",
        description=config.HELP_MOVE_LONG,
        help=config.HELP_MOVE_SHORT,
        aliases=["mv"],
    )
    async def _move(self, ctx: Context, *args):
        if len(args) != 2:
            ctx.send("Wrong number of arguments")
            return

        try:
            oldindex, newindex = map(int, args)
        except ValueError:
            ctx.send("Wrong argument")
            return

        audiocontroller = ctx.bot.audio_controllers[ctx.guild]
        if not audiocontroller.is_active():
            await ctx.send(config.QUEUE_EMPTY)
            return
        try:
            audiocontroller.playlist.move(oldindex - 1, newindex - 1)
        except IndexError:
            await ctx.send("Wrong position")
            return
        await ctx.send("Moved")

    @commands.command(
        name="skip",
        description=config.HELP_SKIP_LONG,
        help=config.HELP_SKIP_SHORT,
        aliases=["s"],
    )
    async def _skip(self, ctx: Context):
        if not await utils.play_check(ctx):
            return

        audiocontroller = ctx.bot.audio_controllers[ctx.guild]
        # audiocontroller.playlist.loop = False

        audiocontroller.timer.cancel()
        audiocontroller.timer = utils.Timer(audiocontroller.timeout_handler)

        if not audiocontroller.is_active():
            await ctx.send(config.QUEUE_EMPTY)
            return
        ctx.guild.voice_client.stop()
        await ctx.send("Skipped current song :fast_forward:")

    @commands.command(
        name="clear",
        description=config.HELP_CLEAR_LONG,
        help=config.HELP_CLEAR_SHORT,
        aliases=["cl"],
    )
    async def _clear(self, ctx: Context):
        if not await utils.play_check(ctx):
            return

        audiocontroller = ctx.bot.audio_controllers[ctx.guild]
        audiocontroller.clear_queue()
        ctx.guild.voice_client.stop()
        audiocontroller.playlist.loop = "off"
        await ctx.send("Cleared queue :no_entry_sign:")

    @commands.command(
        name="prev",
        description=config.HELP_PREV_LONG,
        help=config.HELP_PREV_SHORT,
        aliases=["back"],
    )
    async def _prev(self, ctx: Context):
        if not await utils.play_check(ctx):
            return

        audiocontroller = ctx.bot.audio_controllers[ctx.guild]
        # audiocontroller.playlist.loop = False

        audiocontroller.timer.cancel()
        audiocontroller.timer = utils.Timer(audiocontroller.timeout_handler)

        if await audiocontroller.prev_song():
            await ctx.send("Playing previous song :track_previous:")
        else:
            await ctx.send("No previous track.")

    @commands.command(
        name="resume",
        description=config.HELP_RESUME_LONG,
        help=config.HELP_RESUME_SHORT,
    )
    async def _resume(self, ctx: Context):
        if not await utils.play_check(ctx):
            return

        if ctx.guild.voice_client and ctx.guild.voice_client.is_paused():
            ctx.guild.voice_client.resume()
            await ctx.send("Resumed playback :arrow_forward:")
        else:
            await ctx.send("Playback is not paused.")

    @commands.command(
        name="songinfo",
        description=config.HELP_SONGINFO_LONG,
        help=config.HELP_SONGINFO_SHORT,
        aliases=["np"],
    )
    async def _songinfo(self, ctx: Context):
        if not await utils.play_check(ctx):
            return

        song = ctx.bot.audio_controllers[ctx.guild].current_song
        if song is None:
            return
        await ctx.send(embed=song.info.format_output(config.SONGINFO_SONGINFO))

    @commands.command(
        name="history",
        description=config.HELP_HISTORY_LONG,
        help=config.HELP_HISTORY_SHORT,
    )
    async def _history(self, ctx: Context):
        if not await utils.play_check(ctx):
            return

        await ctx.send(ctx.bot.audio_controllers[ctx.guild].track_history())

    @commands.command(
        name="volume",
        aliases=["vol"],
        description=config.HELP_VOL_LONG,
        help=config.HELP_VOL_SHORT,
    )
    async def _volume(self, ctx: Context, value=None):
        if not await utils.play_check(ctx):
            return

        audiocontroller = ctx.bot.audio_controllers[ctx.guild]

        if value is None:
            await ctx.send(
                "Current volume: {}% :speaker:".format(audiocontroller.volume)
            )
            return

        try:
            volume = int(value)
            if volume > 100 or volume < 0:
                raise ValueError()
        except ValueError:
            await ctx.send("Error: Volume must be a number 1-100")
            return

        if audiocontroller.volume >= volume:
            await ctx.send("Volume set to {}% :sound:".format(str(volume)))
        else:
            await ctx.send("Volume set to {}% :loud_sound:".format(str(volume)))
        audiocontroller.volume = volume


def setup(bot: MusicBot):
    bot.add_cog(Music(bot))
