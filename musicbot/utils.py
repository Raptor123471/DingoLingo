from __future__ import annotations
import re
import os
import sys
import ast
import asyncio
from subprocess import DEVNULL, check_call
from typing import TYPE_CHECKING, Callable, Awaitable, Optional, Union, TypeVar

try:
    from discord import opus, utils, Guild, Message, VoiceChannel, Emoji
    from emoji import is_emoji
except ImportError:
    if not os.getenv("DANDELION_INSTALLING"):
        raise

from config import config

# avoiding circular import
if TYPE_CHECKING:
    from musicbot.bot import MusicBot, Context


def check_dependencies():
    try:
        check_call("ffmpeg --help", stdout=DEVNULL, stderr=DEVNULL, shell=True)
    except Exception as e:
        if sys.platform == "win32":
            download_ffmpeg()
        else:
            raise RuntimeError("ffmpeg was not found") from e
    try:
        opus.Encoder.get_opus_version()
    except opus.OpusNotLoaded as e:
        raise RuntimeError("opus was not found") from e


def download_ffmpeg():
    from io import BytesIO
    from ssl import SSLContext
    from zipfile import ZipFile
    from urllib.request import urlopen

    print("Downloading ffmpeg automatically...")
    stream = urlopen(
        "https://github.com/Krutyi-4el/FFmpeg/releases/download/v5.1.git/ffmpeg.zip",
        context=SSLContext(),
    )
    total_size = int(stream.getheader("content-length") or 0)
    file = BytesIO()
    if total_size:
        BLOCK_SIZE = 1024 * 1024

        data = stream.read(BLOCK_SIZE)
        received_size = BLOCK_SIZE
        percentage = -1
        while data:
            file.write(data)
            data = stream.read(BLOCK_SIZE)
            received_size += len(data)
            new_percentage = int(received_size / total_size * 100)
            if new_percentage != percentage:
                print("\r", new_percentage, "%", sep="", end="")
                percentage = new_percentage
    else:
        file.write(stream.read())
    zipf = ZipFile(file)
    filename = [name for name in zipf.namelist() if name.endswith("ffmpeg.exe")][0]
    with open("ffmpeg.exe", "wb") as f:
        f.write(zipf.read(filename))
    print("\nSuccess!")


def get_guild(bot: MusicBot, command: Message) -> Optional[Guild]:
    """Gets the guild a command belongs to. Useful, if the command was sent via pm.
    DOES NOT WORK WITHOUT MEMBERS INTENT"""
    if command.guild is not None:
        return command.guild
    for guild in bot.guilds:
        for channel in guild.voice_channels:
            if command.author in channel.members:
                return guild
    return None


async def connect_to_channel(
    guild: Guild, dest_channel_name, ctx, switch: bool = False, default: bool = True
):
    """Connects the bot to the specified voice channel.

    Args:
        guild: The guild for witch the operation should be performed.
        switch: Determines if the bot should disconnect from his current channel to switch channels.
        default: Determines if the bot should default to the first channel, if the name was not found.
    """
    for channel in guild.voice_channels:
        if str(channel.name).strip() == str(dest_channel_name).strip():
            if switch:
                try:
                    await guild.voice_client.disconnect()
                except Exception:
                    await ctx.send(config.NOT_CONNECTED_MESSAGE)

            await channel.connect()
            return

    if default:
        try:
            await guild.voice_channels[0].connect()
        except Exception:
            await ctx.send(config.DEFAULT_CHANNEL_JOIN_FAILED)
    else:
        await ctx.send(config.CHANNEL_NOT_FOUND_MESSAGE + str(dest_channel_name))


async def is_connected(ctx: Context) -> Optional[VoiceChannel]:
    try:
        return ctx.guild.voice_client.channel
    except AttributeError:
        return None


async def play_check(ctx: Context):

    sett = ctx.bot.settings[ctx.guild]

    cm_channel = sett.command_channel
    vc_rule = sett.user_must_be_in_vc

    if cm_channel is not None:
        if int(cm_channel) != ctx.channel.id:
            await ctx.send(config.WRONG_CHANNEL_MESSAGE)
            return False

    if vc_rule:
        author_voice = ctx.author.voice
        bot_vc = ctx.guild.voice_client
        if not bot_vc:
            return await ctx.bot.audio_controllers[ctx.guild].uconnect(ctx)
        if not author_voice or author_voice.channel != bot_vc.channel:
            await ctx.send(config.USER_NOT_IN_VC_MESSAGE)
            return False
    return True


def get_emoji(guild: Guild, string: str) -> Optional[Union[str, Emoji]]:
    if is_emoji(string):
        return string
    ids = re.findall(r"\d{15,20}", string)
    if ids:
        emoji = utils.get(guild.emojis, id=int(ids[-1]))
        if emoji:
            return emoji
    return utils.get(guild.emojis, name=string)


def compare_components(obj1, obj2):
    "compare two objects recursively but ignore custom_id in dicts"
    if isinstance(obj1, (list, tuple)) and isinstance(obj2, (list, tuple)):
        if len(obj1) != len(obj2):
            return False
        return all(compare_components(x1, x2) for x1, x2 in zip(obj1, obj2))
    elif isinstance(obj1, dict) and isinstance(obj2, dict):
        obj1.pop("custom_id", None)
        obj2.pop("custom_id", None)
        if obj1.keys() != obj2.keys():
            return False
        return all(compare_components(obj1[k], obj2[k]) for k in obj1)
    return obj1 == obj2


T = TypeVar("T")


def get_env_var(key: str, default: T) -> T:
    value = os.getenv(key)
    if value is None:
        return default
    try:
        value = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        pass
    assert type(value) == type(default), f"invalid value for {key}: {value!r}"
    return value


def alchemize_url(url: str) -> str:
    SCHEMES = (
        ("sqlite", "sqlite+aiosqlite"),
        ("postgres", "postgresql+asyncpg"),
        ("mysql", "mysql+aiomysql"),
    )

    for name, scheme in SCHEMES:
        if url.startswith(name):
            return url.replace(name, scheme, 1)
    return url


class Timer:
    def __init__(self, callback: Callable[[], Awaitable]):
        self._callback = callback
        self._task = asyncio.create_task(self._job())

    async def _job(self):
        await asyncio.sleep(config.VC_TIMEOUT)
        await self._callback()

    def cancel(self):
        self._task.cancel()


class OutputWrapper:
    log_file = None

    def __init__(self, stream):
        self.using_log_file = False
        self.stream = stream

    def write(self, text, /):
        try:
            ret = self.stream.write(text)
            if not self.using_log_file:
                self.stream.flush()
        except Exception:
            self.using_log_file = True
            self.stream = self.get_log_file()
            ret = self.stream.write(text)
        return ret

    def __getattr__(self, key):
        return getattr(self.stream, key)

    @classmethod
    def get_log_file(cls):
        if cls.log_file:
            return cls.log_file
        cls.log_file = open("log.txt", "w", encoding="utf-8")
        return cls.log_file
