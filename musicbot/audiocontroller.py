import asyncio
from typing import TYPE_CHECKING, Optional

import discord
import yt_dlp
from config import config

from musicbot import linkutils, utils
from musicbot.playlist import Playlist
from musicbot.songinfo import Song

# avoiding circular import
if TYPE_CHECKING:
    from musicbot.bot import MusicBot


_cached_downloaders: list[tuple[dict, yt_dlp.YoutubeDL]] = []


class AudioController(object):
    """Controls the playback of audio and the sequential playing of the songs.

    Attributes:
        bot: The instance of the bot that will be playing the music.
        playlist: A Playlist object that stores the history and queue of songs.
        current_song: A Song object that stores details of the current song.
        guild: The guild in which the Audiocontroller operates.
    """

    def __init__(self, bot: "MusicBot", guild: discord.Guild):
        self.bot = bot
        self.playlist = Playlist()
        self.current_song = None
        self.guild = guild

        sett = bot.settings[guild]
        self._volume: int = sett.get("default_volume")

        self.timer = utils.Timer(self.timeout_handler)

    @property
    def volume(self) -> int:
        return self._volume

    @volume.setter
    def volume(self, value: int):
        self._volume = value
        try:
            self.guild.voice_client.source.volume = float(value) / 100.0
        except Exception:
            pass

    async def register_voice_channel(self, channel: discord.VoiceChannel):
        await channel.connect(reconnect=True, timeout=None)

    async def extract_info(self, url: str, options: dict) -> dict:
        downloader = None
        for o, d in _cached_downloaders:
            if o == options:
                downloader = d
                break
        else:
            # we need to copy options because downloader modifies the given dict
            downloader = yt_dlp.YoutubeDL(options.copy())
            _cached_downloaders.append((options, downloader))
        # if options in _cached_downloaders:
        #     downloader = _cached_downloaders[options]
        # else:
        #     downloader = _cached_downloaders[options] = yt_dlp.YoutubeDL(options)
        return await self.bot.loop.run_in_executor(
            None, downloader.extract_info, url, False
        )

    async def fetch_song_info(self, song: Song):
        try:
            info = await self.extract_info(
                song.info.webpage_url,
                {
                    "format": "bestaudio",
                    "title": True,
                    "cookiefile": config.COOKIE_PATH,
                },
            )
        except Exception as e:
            if "ERROR: Sign in to confirm your age" in str(e):
                return
            info = await self.extract_info(
                song, {"title": True, "cookiefile": config.COOKIE_PATH}
            )
        song.update(info)

    def is_active(self) -> bool:
        client = self.guild.voice_client
        return client is not None and (client.is_playing() or client.is_paused())

    def track_history(self):
        history_string = config.INFO_HISTORY_TITLE
        for trackname in self.playlist.trackname_history:
            history_string += "\n" + trackname
        return history_string

    def next_song(self, error=None):
        """Invoked after a song is finished. Plays the next song if there is one."""

        next_song = self.playlist.next(self.current_song)

        self.current_song = None

        if next_song is None:
            return

        coro = self.play_song(next_song)
        self.bot.loop.create_task(coro)

    async def play_song(self, song: Song):
        """Plays a song object"""

        if self.playlist.loop == "off":  # let timer run thouh if looping
            self.timer.cancel()
            self.timer = utils.Timer(self.timeout_handler)

        if song.info.title is None:
            if song.host == linkutils.Sites.Spotify:
                conversion = await self.search_youtube(
                    await linkutils.convert_spotify(song.info.webpage_url)
                )
                if conversion:
                    song.update(conversion)
            else:
                await self.fetch_song_info(song)

        self.playlist.add_name(song.info.title)
        self.current_song = song

        self.playlist.playhistory.append(self.current_song)

        self.guild.voice_client.play(
            discord.FFmpegPCMAudio(
                song.base_url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            ),
            after=self.next_song,
        )

        self.guild.voice_client.source = discord.PCMVolumeTransformer(
            self.guild.voice_client.source
        )
        self.guild.voice_client.source.volume = float(self.volume) / 100.0

        self.playlist.playque.popleft()

        for song in list(self.playlist.playque)[: config.MAX_SONG_PRELOAD]:
            asyncio.ensure_future(self.preload(song))

    async def process_song(self, track: str) -> Optional[Song]:
        """Adds the track to the playlist instance and plays it, if it is the first song"""

        host = linkutils.identify_url(track)
        is_playlist = linkutils.identify_playlist(track)

        if is_playlist != linkutils.Playlist_Types.Unknown:

            await self.process_playlist(is_playlist, track)

            if self.current_song is None:
                await self.play_song(self.playlist.playque[0])
                print("Playing {}".format(track))

            song = Song(linkutils.Origins.Playlist, linkutils.Sites.Unknown)
            return song

        data = None

        if host == linkutils.Sites.Unknown:
            if linkutils.get_url(track) is not None:
                return None

            data = await self.search_youtube(track)

        elif host == linkutils.Sites.Spotify:
            title = await linkutils.convert_spotify(track)
            data = await self.search_youtube(title)

        elif host == linkutils.Sites.YouTube:
            track = track.split("&list=")[0]

        song = Song(linkutils.Origins.Default, host, webpage_url=track)
        if data:
            song.update(data)
        else:
            await self.fetch_song_info(song)

        self.playlist.add(song)
        if self.current_song is None:
            print("Playing {}".format(track))
            await self.play_song(song)

        return song

    async def process_playlist(self, playlist_type: linkutils.Playlist_Types, url: str):

        if playlist_type == linkutils.Playlist_Types.YouTube_Playlist:

            if "playlist?list=" in url:
                # listid = url.split("=")[1]
                pass
            else:
                video = url.split("&")[0]
                await self.process_song(video)
                return

            options = {
                "format": "bestaudio/best",
                "extract_flat": True,
                "cookiefile": config.COOKIE_PATH,
            }

            r = await self.extract_info(url, options)

            for entry in r["entries"]:

                link = "https://www.youtube.com/watch?v={}".format(entry["id"])

                song = Song(
                    linkutils.Origins.Playlist,
                    linkutils.Sites.YouTube,
                    webpage_url=link,
                )

                self.playlist.add(song)

        if playlist_type == linkutils.Playlist_Types.Spotify_Playlist:
            links = await linkutils.get_spotify_playlist(url)
            for link in links:
                song = Song(
                    linkutils.Origins.Playlist,
                    linkutils.Sites.Spotify,
                    webpage_url=link,
                )
                self.playlist.add(song)

        if playlist_type == linkutils.Playlist_Types.BandCamp_Playlist:
            options = {"format": "bestaudio/best", "extract_flat": True}
            r = await self.extract_info(url, options)

            for entry in r["entries"]:

                link = entry.get("url")

                song = Song(
                    linkutils.Origins.Playlist,
                    linkutils.Sites.Bandcamp,
                    webpage_url=link,
                )

                self.playlist.add(song)

        for song in list(self.playlist.playque)[: config.MAX_SONG_PRELOAD]:
            asyncio.ensure_future(self.preload(song))

    async def preload(self, song: Song):

        if song.info.title is not None:
            return

        if song.host == linkutils.Sites.Spotify:
            title = await linkutils.convert_spotify(song.info.webpage_url)
            data = await self.search_youtube(title)
            if data:
                song.update(data)
            return

        if song.info.webpage_url is None:
            return None

        await self.fetch_song_info(song)

    async def search_youtube(self, title: str) -> Optional[dict]:
        """Searches youtube for the video title and returns the first results video link"""

        # if title is already a link
        if linkutils.get_url(title) is not None:
            return title

        options = {
            "format": "bestaudio/best",
            "default_search": "auto",
            "noplaylist": True,
            "cookiefile": config.COOKIE_PATH,
        }

        r = await self.extract_info("ytsearch:" + title, options)

        if not r:
            return None

        return r["entries"][0]

    async def stop_player(self):
        """Stops the player and removes all songs from the queue"""
        if not self.is_active():
            return

        self.playlist.loop = "off"
        self.playlist.next(self.current_song)
        self.clear_queue()
        self.guild.voice_client.stop()

    async def prev_song(self) -> bool:
        """Loads the last song from the history into the queue and starts it"""

        self.timer.cancel()
        self.timer = utils.Timer(self.timeout_handler)

        if len(self.playlist.playhistory) == 0:
            return False

        prev_song = self.playlist.prev(self.current_song)

        if not self.is_active():

            if prev_song == "Dummy":
                self.playlist.next(self.current_song)
                return False
            await self.play_song(prev_song)
        else:
            self.guild.voice_client.stop()
        return True

    async def timeout_handler(self):
        if not self.guild.voice_client:
            return

        if len(self.guild.voice_client.channel.voice_states) == 1:
            await self.udisconnect()
            return

        self.timer = utils.Timer(self.timeout_handler)  # restart timer

        sett = self.bot.settings[self.guild]

        if not sett.get("vc_timeout") or self.guild.voice_client.is_playing():
            return

        await self.udisconnect()

    async def uconnect(self, ctx):

        if not ctx.author.voice:
            await ctx.send(config.NO_GUILD_MESSAGE)
            return False

        if self.guild.voice_client is None:
            await self.register_voice_channel(ctx.author.voice.channel)
        else:
            await ctx.send(config.ALREADY_CONNECTED_MESSAGE)
        return True

    async def udisconnect(self):
        await self.stop_player()
        await self.guild.voice_client.disconnect(force=True)

    def clear_queue(self):
        self.playlist.playque.clear()
