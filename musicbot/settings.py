import json
import os
from typing import TYPE_CHECKING, Optional

import discord
import sqlalchemy
from sqlalchemy import Column, String, Integer, Boolean, select
from sqlalchemy.orm import declarative_base
from alembic.migration import MigrationContext
from alembic.autogenerate import produce_migrations, render_python_code
from alembic.operations import Operations

from musicbot import utils
from config import config

# avoiding circular import
if TYPE_CHECKING:
    from musicbot.bot import MusicBot, Context

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
LEGACY_SETTINGS = DIR_PATH + "/generated/settings.json"
DEFAULT_CONFIG = {
    "default_nickname": None,
    "command_channel": None,
    "start_voice_channel": None,
    "user_must_be_in_vc": True,
    "button_emote": None,
    "default_volume": 100,
    "vc_timeout": config.VC_TIMOUT_DEFAULT,
}
Base = declarative_base()


class GuildSettings(Base):
    __tablename__ = "settings"

    if TYPE_CHECKING:
        # type hints
        guild_id: str
        default_nickname: Optional[str]
        command_channel: Optional[str]
        start_voice_channel: Optional[str]
        user_must_be_in_vc: bool
        button_emote: Optional[str]
        default_volume: int
        vc_timeout: bool

    # use String for ids to be sure we won't hit overflow
    guild_id = Column(String, primary_key=True)
    default_nickname = Column(String)
    command_channel = Column(String)
    start_voice_channel = Column(String)
    user_must_be_in_vc = Column(Boolean, nullable=False)
    button_emote = Column(String)
    default_volume = Column(Integer, nullable=False)
    vc_timeout = Column(Boolean, nullable=False)

    @classmethod
    async def load(cls, bot: "MusicBot", guild: discord.Guild) -> "GuildSettings":
        "Load object from database or create a new one and commit it"
        guild_id = str(guild.id)
        async with bot.DbSession() as session:
            sett = (
                await session.execute(
                    select(GuildSettings).where(GuildSettings.guild_id == guild_id)
                )
            ).scalar_one_or_none()
            if sett:
                return sett
            sett = GuildSettings(guild_id=guild_id, **DEFAULT_CONFIG)
            session.add(sett)
            await session.commit()
            return sett

    @classmethod
    async def load_many(
        cls, bot: "MusicBot", guilds: list[discord.Guild]
    ) -> dict[discord.Guild, "GuildSettings"]:
        """Load list of objects from database and create new ones when not found.
        Returns dict with guilds as keys and their settings as values"""
        ids = [str(g.id) for g in guilds]
        async with bot.DbSession() as session:
            settings = (
                (
                    await session.execute(
                        select(GuildSettings).where(GuildSettings.guild_id.in_(ids))
                    )
                )
                .scalars()
                .fetchall()
            )
            for new_id in set(ids) - {sett.guild_id for sett in settings}:
                new_settings = GuildSettings(guild_id=new_id, **DEFAULT_CONFIG)
                session.add(new_settings)
                settings.append(new_settings)
            await session.commit()
        # ensure the correct order
        settings.sort(key=lambda x: ids.index(x.guild_id))
        return {g: sett for g, sett in zip(guilds, settings)}

    def format(self, ctx: "Context"):
        embed = discord.Embed(
            title="Settings", description=ctx.guild.name, color=config.EMBED_COLOR
        )

        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(
            text="Usage: {}set setting_name value".format(config.BOT_PREFIX)
        )

        # exclusion_keys = ['id']

        for key in DEFAULT_CONFIG.keys():
            # if key in exclusion_keys:
            #     continue

            if not getattr(self, key):
                embed.add_field(name=key, value="Not Set", inline=False)
                continue

            elif key == "start_voice_channel":
                vc = ctx.guild.get_channel(int(self.start_voice_channel))
                embed.add_field(
                    name=key, value=vc.name if vc else "Invalid VChannel", inline=False
                )
                continue

            elif key == "command_channel":
                chan = ctx.guild.get_channel(int(self.command_channel))
                embed.add_field(
                    name=key,
                    value=chan.name if chan else "Invalid Channel",
                    inline=False,
                )
                continue

            elif key == "button_emote":
                emote = utils.get_emoji(ctx.guild, self.button_emote)
                embed.add_field(name=key, value=emote, inline=False)
                continue

            embed.add_field(name=key, value=getattr(self, key), inline=False)

        return embed

    async def process_setting(
        self, setting: str, value: str, ctx: "Context"
    ) -> Optional[bool]:

        if setting not in DEFAULT_CONFIG:
            return None

        return await getattr(self, "set_" + setting)(setting, value, ctx)

    # -----setting methods-----

    async def set_default_nickname(self, setting, value, ctx):

        if value.lower() == "unset":
            self.default_nickname = None
            return True

        if len(value) > 32:
            await ctx.send(
                "`Error: Nickname exceeds character limit`\nUsage: {}set {} nickname\nOther options: unset".format(
                    config.BOT_PREFIX, setting
                )
            )
            return False
        else:
            self.default_nickname = value
            try:
                await ctx.guild.me.edit(nick=value)
            except discord.Forbidden:
                await ctx.send(
                    "`Error: Cannot set nickname. Please check bot permissions."
                )
                return False
            return True

    async def set_command_channel(self, setting, value, ctx):

        if value.lower() == "unset":
            self.command_channel = None
            return True

        chan = discord.utils.find(
            lambda c: c.name.lower() == value.lower(), ctx.guild.text_channels
        )
        if not chan:
            await ctx.send(
                "`Error: Channel name not found`\nUsage: {}set {} channelname\nOther options: unset".format(
                    config.BOT_PREFIX, setting
                )
            )
            return False
        self.command_channel = str(chan.id)
        return True

    async def set_start_voice_channel(self, setting, value, ctx):

        if value.lower() == "unset":
            self.start_voice_channel = None
            return True

        vc = discord.utils.find(
            lambda c: c.name.lower() == value.lower(), ctx.guild.voice_channels
        )
        if not vc:
            await ctx.send(
                "`Error: Voice channel name not found`\nUsage: {}set {} vchannelname\nOther options: unset".format(
                    config.BOT_PREFIX, setting
                )
            )
            return False
        self.start_voice_channel = str(vc.id)
        return True

    async def set_user_must_be_in_vc(self, setting, value, ctx):
        if value.lower() == "true":
            self.user_must_be_in_vc = True
        elif value.lower() == "false":
            self.user_must_be_in_vc = False
        else:
            await ctx.send(
                "`Error: Value must be True/False`\nUsage: {}set {} True/False".format(
                    config.BOT_PREFIX, setting
                )
            )
            return False
        return True

    async def set_button_emote(self, setting, value, ctx):
        if value.lower() == "unset":
            self.button_emote = None
            return True

        emoji = utils.get_emoji(ctx.guild, value)
        if emoji is None:
            await ctx.send(
                "`Error: Invalid emote`\nUsage: {}set {} emote\nOther options: unset".format(
                    config.BOT_PREFIX, setting
                )
            )
            return False
        elif isinstance(emoji, discord.Emoji):
            emoji = str(emoji.id)
        self.button_emote = emoji
        return True

    async def set_default_volume(self, setting, value, ctx):
        try:
            value = int(value)
        except ValueError:
            await ctx.send(
                "`Error: Value must be a number`\nUsage: {}set {} 0-100".format(
                    config.BOT_PREFIX, setting
                )
            )
            return False

        if value > 100 or value < 0:
            await ctx.send(
                "`Error: Value must be a number`\nUsage: {}set {} 0-100".format(
                    config.BOT_PREFIX, setting
                )
            )
            return False

        self.default_volume = value
        return True

    async def set_vc_timeout(self, setting, value, ctx):

        if not config.ALLOW_VC_TIMEOUT_EDIT:
            await ctx.send("`Error: This value cannot be modified")

        if value.lower() == "true":
            self.vc_timeout = True
            self.start_voice_channel = None
        elif value.lower() == "false":
            self.vc_timeout = False
        else:
            await ctx.send(
                "`Error: Value must be True/False`\nUsage: {}set {} True/False".format(
                    config.BOT_PREFIX, setting
                )
            )
            return False
        return True


def run_migrations(connection):
    "Automatically creates or deletes tables and columns, reflecting code changes"
    ctx = MigrationContext.configure(connection)
    code = render_python_code(produce_migrations(ctx, Base.metadata).upgrade_ops)
    if connection.engine.echo:
        # debug mode
        print(code)
    with Operations.context(ctx) as op:
        variables = {"op": op, "sa": sqlalchemy}
        exec("def run():\n" + code, variables)
        variables["run"]()
    connection.commit()


async def extract_legacy_settings(bot: "MusicBot"):
    "Load settings from deprecated json file to DB"
    if not os.path.isfile(LEGACY_SETTINGS):
        return
    with open(LEGACY_SETTINGS) as file:
        json_data = json.load(file)
    async with bot.DbSession() as session:
        existing = (
            (
                await session.execute(
                    select(GuildSettings.guild_id).where(
                        GuildSettings.guild_id.in_(list(json_data))
                    )
                )
            )
            .scalars()
            .fetchall()
        )
        for guild_id, data in json_data.items():
            if guild_id in existing:
                continue
            new_settings = DEFAULT_CONFIG.copy()
            new_settings.update({k: v for k, v in data.items() if k in new_settings})
            session.add(GuildSettings(guild_id=guild_id, **new_settings))
        await session.commit()
    os.remove(LEGACY_SETTINGS)
