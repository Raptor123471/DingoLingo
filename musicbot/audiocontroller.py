import discord
import youtube_dl

from musicbot import linkutils
from musicbot import utils

from config import config
from musicbot.playlist import Playlist
from musicbot.songinfo import Song


class AudioController(object):
    """ Controls the playback of audio and the sequential playing of the songs.

            Attributes:
                bot: The instance of the bot that will be playing the music.
                playlist: A Playlist object that stores the history and queue of songs.
                current_songinfo: A Songinfo object that stores details of the current song.
                guild: The guild in which the Audiocontroller operates.
        """

    def __init__(self, bot, guild):
        self.bot = bot
        self.playlist = Playlist()
        self.current_songinfo = None
        self.guild = guild
        self.voice_client = None

    async def register_voice_channel(self, channel):
        self.voice_client = await channel.connect(reconnect=True, timeout=None)

    def track_history(self):
        history_string = config.INFO_HISTORY_TITLE
        for trackname in self.playlist.trackname_history:
            history_string += "\n" + trackname
        return history_string

    def next_song(self, error):
        """Invoked after a song is finished. Plays the next song if there is one."""

        self.current_songinfo = None
        next_song = self.playlist.next()

        if next_song is None:
            return

        coro = self.play_song(next_song)
        self.bot.loop.create_task(coro)

    async def play_song(self, song):
        """Plays a song object"""

        if song.origin == linkutils.Origins.Playlist:
            if song.host == linkutils.Sites.Spotify:
                conversion = await self.search_youtube(linkutils.convert_spotify(song.Info.webpage_url))
                song.Info.webpage_url = conversion

            downloader = youtube_dl.YoutubeDL(
                {'format': 'bestaudio', 'title': True})
            r = downloader.extract_info(
                song.Info.webpage_url, download=False)

            song.base_url = r.get('url')
            song.Info.uploader = r.get('uploader')
            song.Info.title = r.get('title')
            song.Info.duration = r.get('duration')
            song.Info.webpage_url = r.get('webpage_url')

        self.playlist.add_name(song.Info.title)

        self.voice_client.play(discord.FFmpegPCMAudio(
            song.base_url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'), after=lambda e: self.next_song(e))

    async def process_song(self, track):
        """Adds the track to the playlist instance and plays it, if it is the first song"""

        host = linkutils.identify_url(track)
        is_playlist = linkutils.identify_playlist(track)

        if is_playlist != linkutils.Playlist_Types.Unknown:

            if len(self.playlist.playque) == 0:
                start = True
            else:
                start = False

            await self.process_playlist(is_playlist, track)

            if is_playlist == linkutils.Playlist_Types.Spotify_Playlist:
                song = Song(linkutils.Origins.Playlist,
                            linkutils.Sites.Spotify, "", "", "", "", "")

            if is_playlist == linkutils.Playlist_Types.YouTube_Playlist:
                song = Song(linkutils.Origins.Playlist,
                            linkutils.Sites.YouTube, "", "", "", "", "")

            if start == True:
                await self.play_song(self.playlist.next())
                print("Playing {}".format(track))
            return song

        if host == linkutils.Sites.Unknown:
            if linkutils.get_url(track) is not None:
                return None

            track = await self.search_youtube(track)

        if host == linkutils.Sites.Spotify:
            title = linkutils.convert_spotify(track)
            track = await self.search_youtube(title)

        try:
            downloader = youtube_dl.YoutubeDL(
                {'format': 'bestaudio', 'title': True})
            r = downloader.extract_info(
                track, download=False)
        except:
            downloader = youtube_dl.YoutubeDL({'title': True})
            r = downloader.extract_info(
                track, download=False)

        song = Song(linkutils.Origins.Default, host, r.get('url'), r.get('uploader'), r.get(
            'title'), r.get('duration'), r.get('webpage_url'))

        self.playlist.add(song)
        if len(self.playlist.playque) == 1:
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
                'extract_flat': True
            }

            with youtube_dl.YoutubeDL(options) as ydl:
                r = ydl.extract_info(url, download=False)

                for entry in r['entries']:

                    link = "https://www.youtube.com/watch?v={}".format(
                        entry['id'])

                    song = Song(linkutils.Origins.Playlist,
                                linkutils.Sites.YouTube, "", "", "", "", link)

                    self.playlist.add(song)

        if playlist_type == linkutils.Playlist_Types.Spotify_Playlist:
            links = linkutils.get_spotify_playlist(url)
            for link in links:
                song = Song(linkutils.Origins.Playlist,
                            linkutils.Sites.Spotify, "", "", "", "", link)
                self.playlist.add(song)

    async def search_youtube(self, title):
        """Searches youtube for the video title and returns the first results video link"""

        # if title is already a link
        if linkutils.get_url(title) is not None:
            return title

        options = {
            'format': 'bestaudio/best',
            'default_search': 'auto',
            'noplaylist': True
        }

        with youtube_dl.YoutubeDL(options) as ydl:
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
