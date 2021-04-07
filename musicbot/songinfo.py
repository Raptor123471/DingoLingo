import discord
from discord.ext import commands
from config import config
import datetime


class Song():
    def __init__(self, origin, host, base_url=None, uploader=None, title=None, duration=None, webpage_url=None, thumbnail=None):
        self.host = host
        self.origin = origin
        self.base_url = base_url
        self.info = self.Sinfo(uploader, title, duration,
                               webpage_url, thumbnail)

    class Sinfo:
        def __init__(self, uploader, title, duration, webpage_url, thumbnail):
            self.uploader = uploader
            self.title = title
            self.duration = duration
            self.webpage_url = webpage_url
            self.thumbnail = thumbnail
            self.output = ""

        def format_output(self, playtype):

            embed = discord.Embed(title=playtype, description="[{}]({})".format(self.title, self.webpage_url), color=config.EMBED_COLOR)

            if self.thumbnail is not None:
                embed.set_thumbnail(url=self.thumbnail)

            embed.add_field(name=config.SONGINFO_UPLOADER,
                            value=self.uploader, inline=False)

            if self.duration is not None:
                embed.add_field(name=config.SONGINFO_DURATION,
                                value="{}".format(str(datetime.timedelta(seconds=self.duration))), inline=False)
            else:
                embed.add_field(name=config.SONGINFO_DURATION,
                                value=config.SONGINFO_UNKNOWN_DURATION , inline=False)

            return embed
