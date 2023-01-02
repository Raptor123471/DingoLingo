from typing import Dict, Union

import discord
from discord.ext import bridge, tasks
from discord.ext.commands import DefaultHelpCommand
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import config
from musicbot.audiocontroller import AudioController
from musicbot.settings import GuildSettings, run_migrations, extract_legacy_settings


class MusicBot(bridge.Bot):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("help_command", UniversalHelpCommand())
        super().__init__(*args, **kwargs)

        # A dictionary that remembers which guild belongs to which audiocontroller
        self.audio_controllers: Dict[discord.Guild, AudioController] = {}

        # A dictionary that remembers which settings belongs to which guild
        self.settings: Dict[discord.Guild, GuildSettings] = {}

        self.db_engine = create_async_engine(config.DATABASE)
        self.DbSession = sessionmaker(
            self.db_engine, expire_on_commit=False, class_=AsyncSession
        )
        # replace default to register slash command
        self._default_help = self.remove_command("help")
        self.add_bridge_command(self._help)

    async def start(self, *args, **kwargs):
        print(config.STARTUP_MESSAGE)

        async with self.db_engine.connect() as connection:
            await connection.run_sync(run_migrations)
        await extract_legacy_settings(self)
        return await super().start(*args, **kwargs)

    async def on_ready(self):
        self.settings.update(await GuildSettings.load_many(self, self.guilds))

        for guild in self.guilds:
            await self.register(guild)
            print("Joined {}".format(guild.name))

        print(config.STARTUP_COMPLETE_MESSAGE)

        if not self.update_views.is_running():
            self.update_views.start()

    async def on_guild_join(self, guild):
        print(guild.name)
        await self.register(guild)

    @tasks.loop(seconds=1)
    async def update_views(self):
        for audiocontroller in self.audio_controllers.values():
            await audiocontroller.update_view()

    def add_command(self, command):
        # fix empty description
        # https://github.com/Pycord-Development/pycord/issues/1619
        if command.brief and not command.description:
            command.description = command.brief
        return super().add_command(command)

    def add_application_command(self, command):
        if not config.ENABLE_SLASH_COMMANDS:
            return
        return super().add_application_command(command)

    async def get_prefix(
        self, message: Union[discord.Message, bridge.BridgeApplicationContext]
    ):
        if isinstance(message, bridge.BridgeApplicationContext):
            # display this as prefix for slash commands
            return "/"
        return await super().get_prefix(message)

    async def get_application_context(self, interaction):
        return await super().get_application_context(interaction, ApplicationContext)

    async def process_application_commands(self, inter):
        if not inter.guild:
            await inter.response.send_message(config.NO_GUILD_MESSAGE)
            return

        await super().process_application_commands(inter)

    async def process_commands(self, message: discord.Message):
        if message.author.bot:
            return

        ctx = await self.get_context(message, cls=ExtContext)

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

    @bridge.bridge_command(name="help", description="Help command")
    async def _help(ctx, *, command=None):
        help_command = ctx.bot._default_help
        if ctx.is_app:
            # trick the command to run as slash
            ctx.content = "/help"
            ctx = await ctx.bot.get_context(ctx, ExtContext)
        await help_command.prepare(ctx)
        await help_command.callback(ctx, command=command)


class Context(bridge.BridgeContext):
    bot: MusicBot
    guild: discord.Guild

    async def send(self, *args, **kwargs):
        audiocontroller = self.bot.audio_controllers[self.guild]
        await audiocontroller.update_view(None)
        kwargs["view"] = audiocontroller.make_view()
        # use `respond` for compatibility
        res = await self.respond(*args, **kwargs)
        if isinstance(res, discord.Interaction):
            audiocontroller.last_message = await res.original_message()
        else:
            audiocontroller.last_message = res
        return res


class ExtContext(bridge.BridgeExtContext, Context):
    pass


class ApplicationContext(bridge.BridgeApplicationContext, Context):
    pass


class UniversalHelpCommand(DefaultHelpCommand):
    def get_destination(self):
        return self.context
