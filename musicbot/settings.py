import json
import os
from typing import TYPE_CHECKING, Dict, List, Optional, Union

import discord
from discord import Option, TextChannel, VoiceChannel
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
    "command_channel": None,
    "start_voice_channel": None,
    "user_must_be_in_vc": True,
    "button_emote": None,
    "default_volume": 100,
    "vc_timeout": config.VC_TIMOUT_DEFAULT,
    "announce_songs": sqlalchemy.false(),
}
ID_LENGTH = 25  # more than enough to be sure :)
Base = declarative_base()


class ConversionError(Exception):
    pass


def convert_emoji(ctx: "Context", value: Optional[str]) -> Optional[str]:
    if not config.ENABLE_BUTTON_PLUGIN:
        raise ConversionError("Button plugin is disabled")

    if value is None:
        return None

    emoji = utils.get_emoji(ctx.guild, value)
    if emoji is None:
        raise ConversionError("Invalid emote")
    elif isinstance(emoji, discord.Emoji):
        emoji = str(emoji.id)
    return emoji


def convert_channel(
    ctx: "Context", value: Union[TextChannel, VoiceChannel]
) -> Optional[str]:
    if value is None:
        return None

    return str(value.id)


def convert_bool(ctx: "Context", value: bool) -> bool:
    return value


def convert_volume(ctx: "Context", value: int) -> int:
    if value > 100 or value < 0:
        raise ConversionError("Value must be a number in range 0-100")
    return value


CONFIG_CONVERTERS = {
    "command_channel": convert_channel,
    "start_voice_channel": convert_channel,
    "user_must_be_in_vc": convert_bool,
    "button_emote": convert_emoji,
    "default_volume": convert_volume,
    "vc_timeout": convert_bool,
    "announce_songs": convert_bool,
}
CONFIG_OPTIONS = {
    "command_channel": Option(Union[TextChannel, VoiceChannel], required=False),
    "start_voice_channel": Option(VoiceChannel, required=False),
    "user_must_be_in_vc": Option(bool),
    "button_emote": Option(str, required=False),
    "default_volume": Option(int, min_value=0, max_value=100),
    "vc_timeout": Option(bool),
    "announce_songs": Option(bool),
}


class GuildSettings(Base):
    __tablename__ = "settings"

    # use String for ids to be sure we won't hit overflow
    guild_id: str = Column(String(ID_LENGTH), primary_key=True)
    command_channel: Optional[str] = Column(String(ID_LENGTH))
    start_voice_channel: Optional[str] = Column(String(ID_LENGTH))
    user_must_be_in_vc: bool = Column(Boolean, nullable=False)
    button_emote: Optional[str] = Column(String(ID_LENGTH))
    default_volume: int = Column(Integer, nullable=False)
    vc_timeout: bool = Column(Boolean, nullable=False)
    announce_songs: bool = Column(
        Boolean, nullable=False, server_default=DEFAULT_CONFIG["announce_songs"]
    )

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
            session.add(GuildSettings(guild_id=guild_id, **DEFAULT_CONFIG))
            # avoiding incomplete detached object
            sett = (
                await session.execute(
                    select(GuildSettings).where(GuildSettings.guild_id == guild_id)
                )
            ).scalar_one()
            await session.commit()
            return sett

    @classmethod
    async def load_many(
        cls, bot: "MusicBot", guilds: List[discord.Guild]
    ) -> Dict[discord.Guild, "GuildSettings"]:
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
            missing = set(ids) - {sett.guild_id for sett in settings}
            for new_id in missing:
                session.add(GuildSettings(guild_id=new_id, **DEFAULT_CONFIG))
            settings.extend(
                (
                    await session.execute(
                        select(GuildSettings).where(GuildSettings.guild_id.in_(missing))
                    )
                )
                .scalars()
                .fetchall()
            )
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

    def process_setting(self, setting: str, value: str, ctx: "Context") -> bool:

        if setting not in DEFAULT_CONFIG:
            return False

        value = CONFIG_CONVERTERS[setting](ctx, value)
        setattr(self, setting, value)
        return True


def run_migrations(connection):
    "Automatically creates or deletes tables and columns, reflecting code changes"
    ctx = MigrationContext.configure(connection)
    code = render_python_code(
        produce_migrations(ctx, Base.metadata).upgrade_ops, migration_context=ctx
    )
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
    os.rename(LEGACY_SETTINGS, LEGACY_SETTINGS + ".back")
