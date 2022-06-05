import discord
from discord.ext import commands
from musicbot import linkutils
from musicbot.bot import MusicBot


class Button(commands.Cog):

    def __init__(self, bot: MusicBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author == self.bot.user:
            return

        sett = self.bot.settings[message.guild]
        button_name = sett.get('button_emote')

        if button_name == "":
            return

        host = linkutils.identify_url(message.content)

        guild = message.guild
        emoji = discord.utils.get(guild.emojis, name=button_name)

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
    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):

        serv = self.bot.get_guild(reaction.guild_id)

        if not serv or reaction.member == self.bot.user or not reaction.member.voice:
            return

        sett = self.bot.settings[serv]
        button_name = sett.get('button_emote')

        if button_name == "":
            return

        if reaction.emoji.name == button_name:
            chan = serv.get_channel(reaction.channel_id)
            message = await chan.fetch_message(reaction.message_id)

            if chan.permissions_for(serv.me).manage_messages:
                await message.remove_reaction(reaction.emoji, reaction.member)

            audiocontroller = self.bot.audio_controllers[serv]

            url = linkutils.get_url(message.content)

            host = linkutils.identify_url(url)

            if host in (linkutils.Sites.Spotify, linkutils.Sites.Spotify_Playlist, linkutils.Sites.YouTube):
                await audiocontroller.process_song(url)


def setup(bot: MusicBot):
    bot.add_cog(Button(bot))
