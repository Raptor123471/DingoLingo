import discord
from discord.ext import commands

from musicbot import utils
from musicbot import linkutils
from config import config

from musicbot.commands.general import General

import requests
import datetime


class Music(commands.Cog):
    """ A collection of the commands related to music playback.

        Attributes:
            bot: The instance of the bot that is executing the commands.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='play', description=config.HELP_YT_LONG, help=config.HELP_YT_SHORT, aliases=['p', 'yt', 'P', 'pl'])
    async def _play_song(self, ctx, *, track: str):

        if(await utils.is_connected(ctx) == None):
            await General.uconnect(self, ctx)
        if track.isspace() or not track:
            return

        current_guild = utils.get_guild(self.bot, ctx.message)
        audiocontroller = utils.guild_to_audiocontroller[current_guild]

        if audiocontroller.playlist.loop == True:
            await ctx.send("Loop is enabled! Use {}loop to disable".format(config.BOT_PREFIX))
            return

        host = linkutils.identify_url(track)

        if host == linkutils.Sites.Spotify:

            title = linkutils.convert_spotify(track)
            selfmess = await ctx.send("__Searching for: {}__ :mag_right:".format(title))
            track = await audiocontroller.search_youtube(title)
            await audiocontroller.add_song(track)
            messagecontent = await self.getytinfo(track, ctx, current_guild, audiocontroller)

        if host == linkutils.Sites.Spotify_Playlist:


            links = linkutils.get_spotify_playlist(track)

            selfmess = await ctx.send("Queued playlist :page_with_curl:")
            for link in links:
                await audiocontroller.add_song(link)
                print(link)
            messagecontent = None

        if host == linkutils.Sites.Twitter:

            await ctx.send("Twitter beta queued")
            await audiocontroller.add_song(track)
            return

        if host == linkutils.Sites.Bandcamp:

            await ctx.send("Bandcamp beta queued")
            await audiocontroller.add_song(track)
            return

        if host == linkutils.Sites.Custom:

            await ctx.send("File queued")
            await audiocontroller.add_song(track)
            return

        if host == linkutils.Sites.SoundCloud:

            if config.SOUNDCLOUD_TOKEN == "":
                await ctx.send("Error: No SoundCloud api token")
                return

            # clean mobile links
            track = linkutils.clean_sclink(track)

            try:
                messagecontent = await self.getscinfo(track, ctx, current_guild, audiocontroller)
                selfmess = None
            except:
                await ctx.send("Error: artist has disabled API playback for this song.")
                return
            await audiocontroller.add_song(track)

        if host == linkutils.Sites.YouTube:

            selfmess = await ctx.send("__Loading YouTube link...__ :mag_right:")

            if ("list=" in track):
                if "watch?v=" in track:
                    track = track.split('&')[0]
                    messagecontent = await self.getytinfo(track, ctx, current_guild, audiocontroller)
                else:
                    print("Skipping playlist contentinfo")
                    messagecontent = "Queued playlist :page_with_curl:"

            await audiocontroller.add_youtube(track)

        if host == linkutils.Sites.Unknown:
            if linkutils.get_url(track) is not None:
                await ctx.send(":question: Unknown website")
                return
            else:
                # search here
                selfmess = await ctx.send("__Searching for: {}__ :mag_right:".format(track))
                track = await audiocontroller.search_youtube(track)
                messagecontent = await self.getytinfo(track, ctx, current_guild, audiocontroller)
                await audiocontroller.add_youtube(track)


        if selfmess is not None:
            await selfmess.delete()
        if messagecontent is not None:
            await ctx.send(messagecontent)

    async def getytinfo(self, track, ctx, current_guild, audiocontroller):
        await audiocontroller.getsonginfo(track)
        localsonginfo = audiocontroller.local_songinfo

        playlist = audiocontroller.playlist

        playtype = "placeholder"
        if len(playlist.playque) > 1:

            playtype = "Added to queue"
        else:
            playtype = "Now Playing"
        return localsonginfo.output.replace("|playtype|", playtype)

    async def getscinfo(self, track, ctx, current_guild, audiocontroller):
        sclink = track
        await audiocontroller.getsonginfo(sclink)
        scsonginfo = audiocontroller.soundcloud_songinfo

        playlist = audiocontroller.playlist

        playtype = "placeholder"
        if len(playlist.playque) > 1:
            playtype = "Added to queue"
        else:
            playtype = "Now Playing"
        return scsonginfo.output.replace("|playtype|", playtype)

    @commands.command(name='loop', aliases=['l', 'L'])
    async def _loop(self, ctx):

        current_guild = utils.get_guild(self.bot, ctx.message)
        audiocontroller = utils.guild_to_audiocontroller[current_guild]

        if len(audiocontroller.playlist.playque) < 1:
            await ctx.send("No songs in queue!")
            return

        if audiocontroller.playlist.loop == False:
            audiocontroller.playlist.loop = True
            await ctx.send("Loop enabled :arrows_counterclockwise:")
        else:
            audiocontroller.playlist.loop = False
            await ctx.send("Loop disabled :x:")

    @commands.command(name='pause', description=config.HELP_PAUSE_LONG, help=config.HELP_PAUSE_SHORT)
    async def _pause(self, ctx):
        current_guild = utils.get_guild(self.bot, ctx.message)
        if current_guild is None:
            await utils.send_message(ctx, config.NO_GUILD_MESSAGE)
            return
        if current_guild.voice_client is None or not current_guild.voice_client.is_playing():
            return
        current_guild.voice_client.pause()
        await ctx.send("Playback Paused :pause_button:")

    @commands.command(name='queue', aliases=['playlist', 'q', 'Q'])
    async def _queue(self, ctx):
        current_guild = utils.get_guild(self.bot, ctx.message)
        if current_guild is None:
            await utils.send_message(ctx, config.NO_GUILD_MESSAGE)
            return
        if current_guild.voice_client is None or not current_guild.voice_client.is_playing():
            await ctx.send("Queue is empty :x:")
            return

        playlist = utils.guild_to_audiocontroller[current_guild].playlist

        songlist = []
        counter = 1

        for song in playlist.playque:
            entry = "{}. {}".format(str(counter), song)
            songlist.append(entry)
            counter = counter + 1

        try:
            await ctx.send("Queue[**{}**]:\n{}".format(len(songlist), '\n'.join(songlist[:10])))
        except:
            await ctx.send("Queue to long to post. Working on this feature.")

    @commands.command(name='stop', description=config.HELP_STOP_LONG, help=config. HELP_STOP_SHORT)
    async def _stop(self, ctx):
        current_guild = utils.get_guild(self.bot, ctx.message)
        audiocontroller = utils.guild_to_audiocontroller[current_guild]
        audiocontroller.playlist.loop = False
        if current_guild is None:
            await utils.send_message(ctx, config.NO_GUILD_MESSAGE)
            return
        await utils.guild_to_audiocontroller[current_guild].stop_player()
        await ctx.send("Stopped all sessions :stop:")

    @commands.command(name='skip', description=config.HELP_SKIP_LONG, help=config.HELP_SKIP_SHORT, aliases=['s', 'S'])
    async def _skip(self, ctx):
        current_guild = utils.get_guild(self.bot, ctx.message)
        audiocontroller = utils.guild_to_audiocontroller[current_guild]
        audiocontroller.playlist.loop = False
        if current_guild is None:
            await utils.send_message(ctx, config.NO_GUILD_MESSAGE)
            return
        if current_guild.voice_client is None or (
                not current_guild.voice_client.is_paused() and not current_guild.voice_client.is_playing()):
            return
        current_guild.voice_client.stop()
        await ctx.send("Skipped current song :fast_forward:")

    @commands.command(name='clear', aliases=['cl'])
    async def _clear(self, ctx):
        current_guild = utils.get_guild(self.bot, ctx.message)
        audiocontroller = utils.guild_to_audiocontroller[current_guild]
        audiocontroller.clear_queue()
        audiocontroller.playlist.loop = False
        await ctx.send("Cleared queue :no_entry_sign:")

    @commands.command(name='prev', description=config.HELP_PREV_LONG, help=config.HELP_PREV_SHORT, aliases=['back'])
    async def _prev(self, ctx):
        current_guild = utils.get_guild(self.bot, ctx.message)
        audiocontroller = utils.guild_to_audiocontroller[current_guild]
        audiocontroller.playlist.loop = False
        if current_guild is None:
            await utils.send_message(ctx, config.NO_GUILD_MESSAGE)
            return
        await utils.guild_to_audiocontroller[current_guild].prev_song()
        await ctx.send("Playing previous song :track_previous:")

    @commands.command(name='resume', description=config.HELP_RESUME_LONG, help=config.HELP_RESUME_SHORT)
    async def _resume(self, ctx):
        current_guild = utils.get_guild(self.bot, ctx.message)
        if current_guild is None:
            await utils.send_message(ctx, config.NO_GUILD_MESSAGE)
            return
        current_guild.voice_client.resume()
        await ctx.send("Resumed playback :arrow_forward:")

    @commands.command(name='songinfo', description=config.HELP_SONGINFO_LONG, help=config.HELP_SONGINFO_SHORT, aliases=["np"])
    async def _songinfo(self, ctx):
        current_guild = utils.get_guild(self.bot, ctx.message)
        if current_guild is None:
            await utils.send_message(ctx, config.NO_GUILD_MESSAGE)
            return
        songinfo = utils.guild_to_audiocontroller[current_guild].current_songinfo
        if songinfo is None:
            return
        await ctx.send(songinfo.output.replace("|playtype|", "SongInfo"))

    @commands.command(name='history', description=config.HELP_HISTORY_LONG, help=config.HELP_HISTORY_SHORT)
    async def _history(self, ctx):
        current_guild = utils.get_guild(self.bot, ctx.message)
        if current_guild is None:
            await utils.send_message(ctx, config.NO_GUILD_MESSAGE)
            return
        await utils.send_message(ctx, utils.guild_to_audiocontroller[current_guild].track_history())


def setup(bot):
    bot.add_cog(Music(bot))
