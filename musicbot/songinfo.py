from discord.ext import commands
from config import config
from musicbot import utils


class Songinfo:
    """A wrapper for information about the song currently being played."""

    def __init__(self, uploader, creator, title, duration, like_count, dislike_count, webpage_url):
        self.uploader = uploader
        self.creator = creator
        self.title = title
        self.duration = duration
        self.like_count = like_count
        self.dislike_count = dislike_count
        self.webpage_url = webpage_url

        self._output = ""
        self.format_output()

    @property
    def output(self):
        return self._output

    def format_output(self):
        self._output = "```[" + self.title + "]\n"
        self._output += config.SONGINFO_UPLOADER + str(self.uploader) + "\n"
        self._output += config.SONGINFO_DURATION + \
            str(self.duration) + config.SONGINFO_SECONDS + "\n"
        self._output += config.SONGINFO_LIKES + str(self.like_count) + "\n"
        self._output += config.SONGINFO_DISLIKES + str(self.dislike_count)
        self._output += "```\n" + str(self.webpage_url)


class SoundCloudSonginfo:
    """A wrapper for information about the soundcloud song currently being played."""

    # https://developers.soundcloud.com/docs/api/reference#tracks

    def __init__(self, user, title, label, description, genre, favorites, webpage_url):

        self.user = user
        self.title = title
        self.label = label
        self.description = description
        self.genre = genre
        self.favorites = favorites
        self.webpage_url = webpage_url
        self._output = ""
        self.format_output()

    @property
    def output(self):
        return self._output

    def format_output(self):
        self._output = "> :musical_note: **" + "|playtype|" + \
            ": " + str(self.title) + "** :musical_note:\n```"
        self._output += "User: " + str(self.user) + "\n"
        self._output += "Label name: " + str(self.label) + "\n"
        self._output += "Genre: " + str(self.genre) + "\n"
        self._output += "Favorites: " + str(self.favorites) + "\n"
        self._output += "Description: " + str(self.description) + "\n"
        self._output += "```\n" + "<" + str(self.webpage_url) + ">"


class Localsonginfo:
    """A wrapper for information about the song queued"""

    def __init__(self, uploader, creator, title, duration, like_count, dislike_count, webpage_url):
        self.uploader = uploader
        self.creator = creator
        self.title = title
        self.duration = duration
        self.like_count = like_count
        self.dislike_count = dislike_count
        self.webpage_url = webpage_url

        self._output = ""
        self.format_output()

    @property
    def output(self):
        return self._output

    def format_output(self):

        self._output = "> :musical_note: **" + "|playtype|" + \
            ": " + self.title + "** :musical_note:\n```"
        self._output += config.SONGINFO_UPLOADER + str(self.uploader) + "\n"
        self._output += config.SONGINFO_DURATION + \
            str(self.duration) + config.SONGINFO_SECONDS + "\n"
        self._output += config.SONGINFO_LIKES + str(self.like_count) + "\n"
        self._output += config.SONGINFO_DISLIKES + str(self.dislike_count)
        self._output += "```\n" + "<" + str(self.webpage_url) + ">"
