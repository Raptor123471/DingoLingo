import discord
from discord.ext import commands

from musicbot import utils
from musicbot import linkutils
from config import config

from musicbot.commands.general import General


class Button(commands.Cog):
    """ A collection of the commands related to music playback.

        Attributes:
            bot: The instance of the bot that is executing the commands.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):

        if config.BUTTON_NAME == "":
            return

        if message.author == self.bot.user:
            return

        host = linkutils.identify_url(message.content)

        guild = message.guild
        emoji = discord.utils.get(guild.emojis, name=config.BUTTON_NAME)

        if host == linkutils.Sites.YouTube:
            if emoji:
                await message.add_reaction(emoji)

        if host == linkutils.Sites.Spotify:
            if emoji:
                await message.add_reaction(emoji)

        if host == linkutils.Sites.Spotify_Playlist:
            if emoji:
                await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):

        if config.BUTTON_NAME == "":
            return

        if reaction.emoji.name == config.BUTTON_NAME:
            serv = self.bot.get_guild(reaction.guild_id)
            channels = serv.text_channels

            for chan in channels:
                if chan.id == reaction.channel_id:
                    if reaction.member == self.bot.user:
                        return

                    try:
                        if reaction.member.voice.channel == None:
                            return
                    except:
                        message = await chan.fetch_message(reaction.message_id)
                        await message.remove_reaction(reaction.emoji, reaction.member)
                        return
                    message = await chan.fetch_message(reaction.message_id)
                    await message.remove_reaction(reaction.emoji, reaction.member)

            current_guild = utils.get_guild(self.bot, message)
            audiocontroller = utils.guild_to_audiocontroller[current_guild]

            url = linkutils.get_url(message.content)

            host = linkutils.identify_url(url)

            if host == linkutils.Sites.Spotify:
                await audiocontroller.process_song(url)

            if host == linkutils.Sites.Spotify.Spotify_Playlist:
                await audiocontroller.process_song(url)

            if host == linkutils.Sites.YouTube:
                await audiocontroller.process_song(url)


def setup(bot):
    bot.add_cog(Button(bot))
