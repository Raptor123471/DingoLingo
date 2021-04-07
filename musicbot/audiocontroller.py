import discord
import asyncio

from concurrent.futures import ThreadPoolExecutor
from youtube_dl import YoutubeDL

from musicbot import linkutils
from musicbot import utils

from config import config
from musicbot.playlist import Playlist
from musicbot.songinfo import Song

from musicbot.utils import guild_to_settings


class AudioController(object):
    """ Controls the playback of audio and the sequential playing of the songs.

            Attributes:
                bot: The instance of the bot that will be playing the music.
                playlist: A Playlist object that stores the history and queue of songs.
                current_song: A Song object that stores details of the current song.
                guild: The guild in which the Audiocontroller operates.
        """

    def __init__(self, bot, guild):
        self.bot = bot
        self.playlist = Playlist()
        self.current_song = None
        self.guild = guild
        self.voice_client = None

        sett = utils.guild_to_settings[guild]
        self._volume = sett.get('default_volume')

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = value
        try:
            self.voice_client.source.volume = float(value) / 100.0
        except Exception as e:
            pass

    async def register_voice_channel(self, channel):
        self.voice_client = await channel.connect(reconnect=True, timeout=None)

    def track_history(self):
        history_string = config.INFO_HISTORY_TITLE
        for trackname in self.playlist.trackname_history:
            history_string += "\n" + trackname
        return history_string

    def next_song(self, error):
        """Invoked after a song is finished. Plays the next song if there is one."""

        self.current_song = None
        next_song = self.playlist.next()

        if next_song is None:
            return

        coro = self.play_song(next_song)
        self.bot.loop.create_task(coro)

    async def play_song(self, song):
        """Plays a song object"""

        if song.info.title == None:
            if song.host == linkutils.Sites.Spotify:
                conversion = self.search_youtube(await linkutils.convert_spotify(song.info.webpage_url))
                song.info.webpage_url = conversion

            downloader = YoutubeDL(
                {'format': 'bestaudio', 'title': True, "cookiefile": config.COOKIE_PATH})
            r = downloader.extract_info(
                song.info.webpage_url, download=False)

            song.base_url = r.get('url')
            song.info.uploader = r.get('uploader')
            song.info.title = r.get('title')
            song.info.duration = r.get('duration')
            song.info.webpage_url = r.get('webpage_url')
            song.info.thumbnail = r.get('thumbnails')[0]['url']

        self.playlist.add_name(song.info.title)
        self.current_song = song

        self.voice_client.play(discord.FFmpegPCMAudio(
            song.base_url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'), after=lambda e: self.next_song(e))

        self.voice_client.source = discord.PCMVolumeTransformer(
            self.guild.voice_client.source)
        self.voice_client.source.volume = float(self.volume) / 100.0

        self.playlist.playque.popleft()

        for song in list(self.playlist.playque)[:config.MAX_SONG_PRELOAD]:
            asyncio.ensure_future(self.preload(song))

    async def process_song(self, track):
        """Adds the track to the playlist instance and plays it, if it is the first song"""

        host = linkutils.identify_url(track)
        is_playlist = linkutils.identify_playlist(track)

        if is_playlist != linkutils.Playlist_Types.Unknown:

            await self.process_playlist(is_playlist, track)

            if self.current_song == None:
                await self.play_song(self.playlist.playque[0])
                print("Playing {}".format(track))

            song = Song(linkutils.Origins.Playlist,
                        linkutils.Sites.Unknown)
            return song

        if host == linkutils.Sites.Unknown:
            if linkutils.get_url(track) is not None:
                return None

            track = self.search_youtube(track)

        if host == linkutils.Sites.Spotify:
            title = await linkutils.convert_spotify(track)
            track = self.search_youtube(title)

        if host == linkutils.Sites.YouTube:
            track = track.split("&list=")[0]

        try:
            downloader = YoutubeDL(
                {'format': 'bestaudio', 'title': True, "cookiefile": config.COOKIE_PATH})
            r = downloader.extract_info(
                track, download=False)
        except:
            downloader = YoutubeDL(
                {'title': True, "cookiefile": config.COOKIE_PATH})
            r = downloader.extract_info(
                track, download=False)

        if r.get('thumbnails') is not None:
            thumbnail = r.get('thumbnails')[len(
                r.get('thumbnails')) - 1]['url']
        else:
            thumbnail = None

        song = Song(linkutils.Origins.Default, host, base_url=r.get('url'), uploader=r.get('uploader'), title=r.get(
            'title'), duration=r.get('duration'), webpage_url=r.get('webpage_url'), thumbnail=thumbnail)

        self.playlist.add(song)
        if self.current_song == None:
            print("Playing {}".format(track))
            await self.play_song(song)

        return song

    async def process_playlist(self, playlist_type, url):

        if playlist_type == linkutils.Playlist_Types.YouTube_Playlist:

            if ("playlist?list=" in url):
                listid = url.split('=')[1]
            else:
                video = url.split('&')[0]
                await self.process_song(video)
                return

            options = {
                'format': 'bestaudio/best',
                'extract_flat': True,
                "cookiefile": config.COOKIE_PATH
            }

            with YoutubeDL(options) as ydl:
                r = ydl.extract_info(url, download=False)

                for entry in r['entries']:

                    link = "https://www.youtube.com/watch?v={}".format(
                        entry['id'])

                    song = Song(linkutils.Origins.Playlist,
                                linkutils.Sites.YouTube, webpage_url=link)

                    self.playlist.add(song)

        if playlist_type == linkutils.Playlist_Types.Spotify_Playlist:
            links = await linkutils.get_spotify_playlist(url)
            for link in links:
                song = Song(linkutils.Origins.Playlist,
                            linkutils.Sites.Spotify, webpage_url=link)
                self.playlist.add(song)

        if playlist_type == linkutils.Playlist_Types.BandCamp_Playlist:
            options = {
                'format': 'bestaudio/best',
                'extract_flat': True
            }
            with YoutubeDL(options) as ydl:
                r = ydl.extract_info(url, download=False)

                for entry in r['entries']:

                    link = entry.get('url')

                    song = Song(linkutils.Origins.Playlist,
                                linkutils.Sites.Bandcamp, webpage_url=link)

                    self.playlist.add(song)

        for song in list(self.playlist.playque)[:config.MAX_SONG_PRELOAD]:
            asyncio.ensure_future(self.preload(song))

    async def preload(self, song):

        if song.info.title != None:
            return

        def down(song):

            if song.host == linkutils.Sites.Spotify:
                song.info.webpage_url = self.search_youtube(song.info.title)

            downloader = YoutubeDL(
                {'format': 'bestaudio', 'title': True, "cookiefile": config.COOKIE_PATH})
            r = downloader.extract_info(
                song.info.webpage_url, download=False)
            song.base_url = r.get('url')
            song.info.uploader = r.get('uploader')
            song.info.title = r.get('title')
            song.info.duration = r.get('duration')
            song.info.webpage_url = r.get('webpage_url')
            song.info.thumbnail = r.get('thumbnails')[0]['url']

        if song.host == linkutils.Sites.Spotify:
            song.info.title = await linkutils.convert_spotify(song.info.webpage_url)

        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=config.MAX_SONG_PRELOAD)
        await asyncio.wait(fs={loop.run_in_executor(executor, down, song)}, return_when=asyncio.ALL_COMPLETED)

    def search_youtube(self, title):
        """Searches youtube for the video title and returns the first results video link"""

        # if title is already a link
        if linkutils.get_url(title) is not None:
            return title

        options = {
            'format': 'bestaudio/best',
            'default_search': 'auto',
            'noplaylist': True,
            "cookiefile": config.COOKIE_PATH
        }

        with YoutubeDL(options) as ydl:
            r = ydl.extract_info(title, download=False)

        videocode = r['entries'][0]['id']

        return "https://www.youtube.com/watch?v={}".format(videocode)

    async def stop_player(self):
        """Stops the player and removes all songs from the queue"""
        if self.guild.voice_client is None or (
                not self.guild.voice_client.is_paused() and not self.guild.voice_client.is_playing()):
            return
        self.playlist.next()
        self.playlist.playque.clear()
        self.guild.voice_client.stop()

    async def prev_song(self):
        """Loads the last song from the history into the queue and starts it"""
        if len(self.playlist.playhistory) == 0:
            return None
        if self.guild.voice_client is None or (
                not self.guild.voice_client.is_paused() and not self.guild.voice_client.is_playing()):
            prev_song = self.playlist.prev()
            # The Dummy is used if there is no song in the history
            if prev_song == "Dummy":
                self.playlist.next()
                return None
            await self.play_youtube(prev_song)
        else:
            self.playlist.prev()
            self.playlist.prev()
            self.guild.voice_client.stop()

    def clear_queue(self):
        self.playlist.playque.clear()
