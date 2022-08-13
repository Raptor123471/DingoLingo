import re
import sys
import asyncio
from subprocess import DEVNULL, check_call
from typing import TYPE_CHECKING, Callable, Awaitable, Optional, Union

from discord import opus, utils, Guild, Message, VoiceChannel, Emoji
from emoji import is_emoji

from config import config

# avoiding circular import
if TYPE_CHECKING:
    from musicbot.bot import MusicBot, Context


def check_dependencies():
    try:
        check_call(["ffmpeg", "--help"], stdout=DEVNULL, stderr=DEVNULL)
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
        "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
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


def get_guild(bot: "MusicBot", command: Message) -> Optional[Guild]:
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


async def is_connected(ctx: "Context") -> Optional[VoiceChannel]:
    try:
        return ctx.guild.voice_client.channel
    except AttributeError:
        return None


async def play_check(ctx: "Context"):

    sett = ctx.bot.settings[ctx.guild]

    cm_channel = sett.command_channel
    vc_rule = sett.user_must_be_in_vc

    if cm_channel is not None:
        if int(cm_channel) != ctx.message.channel.id:
            await ctx.send(config.WRONG_CHANNEL_MESSAGE)
            return False

    if vc_rule:
        author_voice = ctx.message.author.voice
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


class Timer:
    def __init__(self, callback: Callable[[], Awaitable]):
        self._callback = callback
        self._task = asyncio.create_task(self._job())

    async def _job(self):
        await asyncio.sleep(config.VC_TIMEOUT)
        await self._callback()

    def cancel(self):
        self._task.cancel()
