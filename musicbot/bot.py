import discord
from discord.ext import commands
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import config
from musicbot.audiocontroller import AudioController
from musicbot.settings import GuildSettings, run_migrations, extract_legacy_settings


class MusicBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # A dictionary that remembers which guild belongs to which audiocontroller
        self.audio_controllers: dict[discord.Guild, AudioController] = {}

        # A dictionary that remembers which settings belongs to which guild
        self.settings: dict[discord.Guild, GuildSettings] = {}

        self.db_engine = create_async_engine(config.DATABASE)
        self.DbSession = sessionmaker(
            self.db_engine, expire_on_commit=False, class_=AsyncSession
        )

    async def start(self, *args, **kwargs):
        async with self.db_engine.connect() as connection:
            await connection.run_sync(run_migrations)
        await extract_legacy_settings(self)
        return await super().start(*args, **kwargs)

    async def on_ready(self):
        print(config.STARTUP_MESSAGE)

        self.settings.update(await GuildSettings.load_many(self, self.guilds))

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
        if guild in self.audio_controllers:
            return

        if guild not in self.settings:
            self.settings[guild] = await GuildSettings.load(self, guild)

        sett = self.settings[guild]
        controller = self.audio_controllers[guild] = AudioController(self, guild)

        if config.GLOBAL_DISABLE_AUTOJOIN_VC:
            return

        if not sett.vc_timeout:
            try:
                await controller.register_voice_channel(
                    guild.get_channel(int(sett.start_voice_channel or 0))
                    or guild.voice_channels[0]
                )
            except Exception as e:
                print(e)


class Context(commands.Context):
    bot: MusicBot
    guild: discord.Guild
