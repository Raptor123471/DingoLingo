from typing import Dict

import discord
from discord.ext import commands

from config import config
from musicbot.audiocontroller import AudioController
from musicbot.settings import Settings


class MusicBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # A dictionary that remembers which guild belongs to which audiocontroller
        self.audio_controllers: Dict[discord.Guild, AudioController] = {}

        # A dictionary that remembers which settings belongs to which guild
        self.settings: Dict[discord.Guild, Settings] = {}

    async def on_ready(self):
        print(config.STARTUP_MESSAGE)

        for guild in self.guilds:
            await self.register(guild)
            print("Joined {}".format(guild.name))

        print(config.STARTUP_COMPLETE_MESSAGE)

    async def on_guild_join(self, guild):
        print(guild.name)
        await self.register(guild)

    async def process_commands(self, message: discord.Message):
        if message.author.bot:
            return

        ctx = await self.get_context(message, cls=Context)

        if ctx.valid and not message.guild:
            await message.channel.send(config.NO_GUILD_MESSAGE)
            return

        await self.invoke(ctx)

    async def register(self, guild: discord.Guild):
        if guild in self.settings:
            return

        sett = self.settings[guild] = Settings(guild)
        controller = self.audio_controllers[guild] = AudioController(self, guild)

        try:
            await guild.me.edit(nick=sett.get('default_nickname'))
        except discord.Forbidden:
            pass

        if config.GLOBAL_DISABLE_AUTOJOIN_VC:
            return

        if not sett.get("vc_timeout"):
            try:
                await controller.register_voice_channel(
                    guild.get_channel(sett.get("start_voice_channel"))
                    or guild.voice_channels[0]
                )
            except Exception as e:
                print(e)


class Context(commands.Context):
    bot: MusicBot
    guild: discord.Guild
