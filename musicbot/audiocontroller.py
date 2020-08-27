import discord
import youtube_dl

from pyyoutube import Api

from musicbot import linkutils

from config import config
from musicbot.playlist import Playlist
from musicbot.songinfo import Songinfo, Localsonginfo, SoundCloudSonginfo

import soundcloud


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
        if config.YOUTUBE_TOKEN != "":
            self.api = Api(api_key=config.YOUTUBE_TOKEN)
        else:
            self.api = None

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

        host = linkutils.identify_url(next_song)

        if host is not linkutils.Sites.Unknown:
            if host == linkutils.Sites.YouTube:
                coro = self.play_youtube(next_song)
            if host == linkutils.Sites.Custom:
                coro = self.play_file(next_song)
            if host == linkutils.Sites.Twitter:
                coro = self.play_twitter(next_song)
            if host == linkutils.Sites.SoundCloud:
                coro = self.play_soundcloud(linkutils.clean_sclink(next_song))
            if host == linkutils.Sites.Bandcamp:
                coro = self.play_bandcamp(next_song)

            self.bot.loop.create_task(coro)

    async def add_youtube(self, link):
        """Processes a youtube link and passes elements of a playlist to the add_song function one by one"""

        # Pass it on if it is not a playlist
        if not ("list=" in link):
            await self.add_song(link)
            return

        if ("playlist?list=" in link):
            listid = link.split('=')[1]
        else:
            video = link.split('&')[0]
            await self.add_song(video)
            return

        if self.api is not None:

            try:
                playlist_item_by_playlist = self.api.get_playlist_items(
                    playlist_id=listid, count=None)

                for vid in playlist_item_by_playlist.items:

                    videocode = vid.snippet.resourceId.videoId

                    await self.add_song("https://www.youtube.com/watch?v={}".format(videocode))
                print("API used")
                return
            except:
                print("Error: API key is invalid! Falling back to API-less search.")
                pass

        options = {
            'format': 'bestaudio/best',
            'extract_flat': True
        }

        with youtube_dl.YoutubeDL(options) as ydl:
            r = ydl.extract_info(link, download=False)

            for entry in r['entries']:

                videocode = entry['id']

                await self.add_song("https://www.youtube.com/watch?v={}".format(videocode))

    async def add_song(self, track):
        """Adds the track to the playlist instance and plays it, if it is the first song"""

        host = linkutils.identify_url(track)

        if host == linkutils.Sites.Twitter:
            self.playlist.add(track)
            if len(self.playlist.playque) == 1:
                await self.play_twitter(track)
            return

        if host == linkutils.Sites.Bandcamp:
            self.playlist.add(track)
            if len(self.playlist.playque) == 1:
                await self.play_bandcamp(track)
            return

        if host == linkutils.Sites.Custom:
            self.playlist.add(track)
            if len(self.playlist.playque) == 1:
                await self.play_file(track)
            return

        if host == linkutils.Sites.SoundCloud:
            self.playlist.add(track)
            if len(self.playlist.playque) == 1:
                await self.play_soundcloud(track)
            return

        self.playlist.add(track)
        if len(self.playlist.playque) == 1:
            print("Playing {}".format(track))
            await self.play_youtube(track)

    async def search_youtube(self, title):
        """Searches youtube for the video title and returns the first results video link"""

        # if title is already a link
        if linkutils.get_url(title) is not None:
            return title

        if self.api is not None:

            try:
                r = self.api.search_by_keywords(q=title.replace(
                    '"', ''), search_type=["video"], count=4, limit=4)
                id = r.items[0].id.videoId

                print("API used")

                return "https://www.youtube.com/watch?v=" + id
            except:
                print("Error: API key is invalid! Falling back to API-less search.")
                pass

        options = {
            'format': 'bestaudio/best',
            'default_search': 'auto',
            'noplaylist': True
        }

        with youtube_dl.YoutubeDL(options) as ydl:
            r = ydl.extract_info(title, download=False)

        videocode = r['entries'][0]['id']

        return "https://www.youtube.com/watch?v={}".format(videocode)

    async def play_youtube(self, youtube_link):
        """Downloads and plays the audio of the youtube link passed"""

        youtube_link = youtube_link.split("&list=")[0]

        if self.voice_client is None:
            await self.register_voice_channel(self.guild.voice_channels[0])

        try:
            downloader = youtube_dl.YoutubeDL(
                {'format': 'bestaudio', 'title': True})
            extracted_info = downloader.extract_info(
                youtube_link, download=False)
        # "format" is not available for livestreams - redownload the page with no options
        except:
            try:
                downloader = youtube_dl.YoutubeDL({})
                extracted_info = downloader.extract_info(
                    youtube_link, download=False)
            except:
                self.next_song(None)

        self.voice_client.play(discord.FFmpegPCMAudio(extracted_info.get(
            'url'), before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'), after=lambda e: self.next_song(e))

        # Update the songinfo to reflect the current song
        self.current_songinfo = Songinfo(extracted_info.get('uploader'), extracted_info.get('creator'),
                                         extracted_info.get(
                                             'title'), extracted_info.get('duration'),
                                         extracted_info.get('like_count'), extracted_info.get(
                                             'dislike_count'),
                                         extracted_info.get('webpage_url'))

        self.playlist.add_name(extracted_info.get('title'))

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

    async def play_soundcloud(self, soundcloud_link):
        """Downloads and plays the audio of the soundcloud link passed"""
        # https://developers.soundcloud.com/docs/api/reference#tracks

        client = soundcloud.Client(client_id=config.SOUNDCLOUD_TOKEN)

        try:
            track = client.get('/resolve', url=soundcloud_link)
        except:
            return

        stream_url = client.get(track.stream_url, allow_redirects=False)

        # Update the songinfo to reflect the current song
        self.current_songinfo = SoundCloudSonginfo(
            track.user.get('username'),
            track.title,
            track.label_name,
            track.description,
            track.genre,
            track.favoritings_count,
            soundcloud_link
        )

        self.playlist.add_name(track.title)
        self.voice_client.play(discord.FFmpegPCMAudio(
            stream_url.location, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'), after=lambda e: self.next_song(e))
        return

    async def play_file(self, file_link):
        """Downloads and plays the audio of the custom file link passed"""

        # Custom files have no info
        self.current_songinfo = Songinfo("", "",
                                         "", "",
                                         "", "",
                                         file_link)

        self.voice_client.play(discord.FFmpegPCMAudio(
            file_link), after=lambda e: self.next_song(e))
        self.playlist.add_name("Custom file")

    async def play_bandcamp(self, bc_link):
        """Downloads and plays the audio of the custom file link passed"""

        # Custom files have no info
        self.current_songinfo = Songinfo("", "",
                                         "", "",
                                         "", "",
                                         bc_link)

        downloader = youtube_dl.YoutubeDL({})
        extracted_info = downloader.extract_info(bc_link, download=False)

        self.voice_client.play(discord.FFmpegPCMAudio(
            extracted_info.get('url')), after=lambda e: self.next_song(e))
        self.playlist.add_name("Bandcamp Song")

    async def play_twitter(self, tw_link):
        """Downloads and plays the audio of the custom file link passed"""

        # Custom files have no info
        self.current_songinfo = Songinfo("", "",
                                         "", "",
                                         "", "",
                                         tw_link)

        downloader = youtube_dl.YoutubeDL({})
        extracted_info = downloader.extract_info(tw_link, download=False)

        self.voice_client.play(discord.FFmpegPCMAudio(
            extracted_info.get('url')), after=lambda e: self.next_song(e))
        self.playlist.add_name("Twitter Video")

    async def getsonginfo(self, link):
        """Gets passed song info and sets Localsonginfo in songinfo.py"""

        host = linkutils.identify_url(link)

        if host == linkutils.Sites.SoundCloud:

            client = soundcloud.Client(
                client_id=config.SOUNDCLOUD_TOKEN)

            track = client.get('/resolve', url=link)

            self.soundcloud_songinfo = SoundCloudSonginfo(
                track.user.get('username'),
                track.title,
                track.label_name,
                track.description,
                track.genre,
                track.favoritings_count,
                link)
            return

        downloader = youtube_dl.YoutubeDL({})
        extracted_info = downloader.extract_info(link, download=False)
        self.local_songinfo = Localsonginfo(extracted_info.get('uploader'), extracted_info.get('creator'),
                                            extracted_info.get(
                                                'title'), extracted_info.get('duration'),
                                            extracted_info.get('like_count'), extracted_info.get(
                                                'dislike_count'),
                                            extracted_info.get('webpage_url'))

    def clear_queue(self):
        self.playlist.playque.clear()
