import discord
from discord.ext import commands
from musicbot import linkutils, utils
from musicbot.bot import MusicBot

SUPPORTED_SITES = (
    linkutils.Sites.Spotify,
    linkutils.Sites.Spotify_Playlist,
    linkutils.Sites.YouTube,
)


class Button(commands.Cog):
    def __init__(self, bot: MusicBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author == self.bot.user:
            return

        sett = self.bot.settings[message.guild]
        button = sett.button_emote

        if not button:
            return

        emoji = utils.get_emoji(message.guild, button)
        if not emoji:
            return

        host = linkutils.identify_url(message.content)

        if host in SUPPORTED_SITES:
            await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):

        serv = self.bot.get_guild(reaction.guild_id)

        user_vc = reaction.member.voice

        if not serv or reaction.member == self.bot.user or not user_vc:
            return

        sett = self.bot.settings[serv]
        button = sett.button_emote

        if not button:
            return

        if reaction.emoji.name == button or str(reaction.emoji.id or "") == button:
            chan = serv.get_channel(reaction.channel_id)
            message = await chan.fetch_message(reaction.message_id)
            url = linkutils.get_url(message.content)

            host = linkutils.identify_url(url)

            if host not in SUPPORTED_SITES:
                return

            if chan.permissions_for(serv.me).manage_messages:
                await message.remove_reaction(reaction.emoji, reaction.member)

            audiocontroller = self.bot.audio_controllers[serv]

            if serv.voice_client is None:
                await audiocontroller.register_voice_channel(user_vc.channel)
            elif serv.voice_client.channel != user_vc.channel:
                return
            if not audiocontroller.command_channel and sett.command_channel:
                audiocontroller.command_channel = serv.get_channel(int(sett.command_channel))
            await audiocontroller.process_song(url)


def setup(bot: MusicBot):
    bot.add_cog(Button(bot))
