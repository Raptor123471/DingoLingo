import discord
from discord.ext import commands, bridge

from config import config
from musicbot import linkutils, utils
from musicbot.bot import MusicBot, Context


class Music(commands.Cog):
    """A collection of the commands related to music playback.

    Attributes:
        bot: The instance of the bot that is executing the commands.
    """

    def __init__(self, bot: MusicBot):
        self.bot = bot

    @bridge.bridge_command(
        name="play",
        description=config.HELP_YT_LONG,
        help=config.HELP_YT_SHORT,
        aliases=["p", "yt", "pl"],
    )
    async def _play_song(self, ctx: Context, *, track: str):
        await ctx.defer()

        if not await utils.play_check(ctx):
            return

        audiocontroller = ctx.bot.audio_controllers[ctx.guild]

        # reset timer
        audiocontroller.timer.cancel()
        audiocontroller.timer = utils.Timer(audiocontroller.timeout_handler)

        # if audiocontroller.playlist.loop == True:
        #     await ctx.send("Loop is enabled! Use {}loop to disable".format(config.BOT_PREFIX))
        #     return

        audiocontroller.command_channel = ctx
        song = await audiocontroller.process_song(track)

        if song is None:
            await ctx.send(config.SONGINFO_ERROR)
            return

        if song.origin == linkutils.Origins.Playlist:
            await ctx.send(config.SONGINFO_PLAYLIST_QUEUED)
        else:
            if len(audiocontroller.playlist.playque) != 0:
                await ctx.send(
                    embed=song.info.format_output(config.SONGINFO_QUEUE_ADDED)
                )
            elif not ctx.bot.settings[ctx.guild].announce_songs:
                # auto-announce is disabled, announce here
                await ctx.send(
                    embed=song.info.format_output(config.SONGINFO_NOW_PLAYING)
                )

    @bridge.bridge_command(
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

    @bridge.bridge_command(
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

    @bridge.bridge_command(
        name="pause",
        description=config.HELP_PAUSE_LONG,
        help=config.HELP_PAUSE_SHORT,
        aliases=["resume"],
    )
    async def _pause(self, ctx: Context):
        if not await utils.play_check(ctx):
            return

        result = ctx.bot.audio_controllers[ctx.guild].pause()
        await ctx.send(result.value)

    @bridge.bridge_command(
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

    @bridge.bridge_command(
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

    @bridge.bridge_command(
        name="move",
        description=config.HELP_MOVE_LONG,
        help=config.HELP_MOVE_SHORT,
        aliases=["mv"],
    )
    async def _move(self, ctx: Context, src_pos: int, dest_pos: int):
        audiocontroller = ctx.bot.audio_controllers[ctx.guild]
        if not audiocontroller.is_active():
            await ctx.send(config.QUEUE_EMPTY)
            return
        try:
            audiocontroller.playlist.move(src_pos - 1, dest_pos - 1)
        except IndexError:
            await ctx.send("Wrong position")
            return
        await ctx.send("Moved")
       
    
    @bridge.bridge_command(name='remove', description=config.HELP_REMOVE_LONG, help=config.HELP_REMOVE_SHORT, aliases=['rm'])
    async def _remove(self, ctx, *, queue_number: int):
        ctx.guild = utils.get_guild(self.bot, ctx.message)

        if queue_number is None:
            ctx.send("You need to enter in queue number of the song you want to get out of the playlist.")

        audiocontroller = ctx.bot.audio_controllers[ctx.guild]

        response = audiocontroller.remove_song(queue_number)
        await ctx.message.add_reaction('👍')
        await ctx.send(response)


    @bridge.bridge_command(
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

    @bridge.bridge_command(
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

    @bridge.bridge_command(
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

    @bridge.bridge_command(
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
            await ctx.send("No song is playing now.")
            return
        await ctx.send(embed=song.info.format_output(config.SONGINFO_SONGINFO))

    @bridge.bridge_command(
        name="history",
        description=config.HELP_HISTORY_LONG,
        help=config.HELP_HISTORY_SHORT,
    )
    async def _history(self, ctx: Context):
        if not await utils.play_check(ctx):
            return

        await ctx.send(ctx.bot.audio_controllers[ctx.guild].track_history())

    @bridge.bridge_command(
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
