import discord
from discord.ext import commands
from config import config


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

            embed = discord.Embed(title=":musical_note:  __**{}**__  :musical_note:".format(
                self.title), description="***{}***".format(playtype), url=self.webpage_url, color=0x4dd4d0)

            if self.thumbnail is not None:
                embed.set_thumbnail(url=self.thumbnail)

            embed.add_field(name=config.SONGINFO_UPLOADER,
                            value=self.uploader, inline=False)
            embed.add_field(name=config.SONGINFO_DURATION,
                            value="{}{}".format(self.duration, config.SONGINFO_SECONDS), inline=False)

            return embed
