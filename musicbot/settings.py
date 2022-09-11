import json
import os
from typing import TYPE_CHECKING, Optional

import discord
from discord.ext import commands

from musicbot import utils
from config import config

# avoiding circular import
if TYPE_CHECKING:
    from musicbot.bot import Context

dir_path = os.path.dirname(os.path.realpath(__file__))


class Settings:
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.json_data: dict = None
        self.config: dict = None
        self.path = "{}/generated/settings.json".format(dir_path)

        self.settings_template = {
            # "id": 0,
            "default_nickname": "",
            "command_channel": None,
            "start_voice_channel": None,
            "user_must_be_in_vc": True,
            "button_emote": "",
            "default_volume": 100,
            "vc_timeout": config.VC_TIMOUT_DEFAULT,
        }

        self.reload()
        self.upgrade()

    async def write(self, setting: str, value: str, ctx: "Context") -> Optional[bool]:
        response = await self.process_setting(setting, value, ctx)

        with open(self.path, "w") as source:
            json.dump(self.json_data, source)
        self.reload()
        return response

    def reload(self):
        with open(self.path, "r") as source:
            self.json_data = json.load(source)

        target = None

        for guild_id in self.json_data:
            if guild_id == str(self.guild.id):
                target = self.json_data[guild_id]

        if target is None:
            self.create()
            return

        self.config = target

    def upgrade(self):
        refresh = False
        for key in self.settings_template.keys():
            if key not in self.config:
                self.config[key] = self.settings_template.get(key)
                refresh = True
        if refresh:
            with open(self.path, "w") as source:
                json.dump(self.json_data, source)
            self.reload()

    def create(self):

        self.json_data[str(self.guild.id)] = self.settings_template

        with open(self.path, "w") as source:
            json.dump(self.json_data, source)
        self.reload()

    def get(self, setting):
        return self.config[setting]

    async def format(self):
        embed = discord.Embed(
            title="Settings", description=self.guild.name, color=config.EMBED_COLOR
        )

        if self.guild.icon:
            embed.set_thumbnail(url=self.guild.icon.url)
        embed.set_footer(
            text="Usage: {}set setting_name value".format(config.BOT_PREFIX)
        )

        # exclusion_keys = ['id']

        for key in self.config.keys():
            # if key in exclusion_keys:
            #     continue

            if not self.config.get(key):

                embed.add_field(name=key, value="Not Set", inline=False)
                continue

            elif key == "start_voice_channel":
                vc = self.guild.get_channel(self.config.get(key))
                embed.add_field(
                    name=key, value=vc.name if vc else "Invalid VChannel", inline=False
                )

                continue

            elif key == "command_channel":
                chan = self.guild.get_channel(self.config.get(key))
                embed.add_field(
                    name=key,
                    value=chan.name if chan else "Invalid Channel",
                    inline=False,
                )

                continue

            elif key == "button_emote":
                emote = utils.get_emoji(self.guild, self.config.get(key))
                embed.add_field(name=key, value=emote, inline=False)

                continue

            embed.add_field(name=key, value=self.config.get(key), inline=False)

        return embed

    async def process_setting(
        self, setting: str, value: str, ctx: "Context"
    ) -> Optional[bool]:

        options = {
            "default_nickname",
            "command_channel",
            "start_voice_channel",
            "user_must_be_in_vc",
            "button_emote",
            "default_volume",
            "vc_timeout",
        }
        if setting not in options:
            return None

        answer = await getattr(self, setting)(setting, value, ctx)
        if answer is None:
            return True
        return answer

    # -----setting methods-----

    async def default_nickname(self, setting, value, ctx):

        if value.lower() == "unset":
            self.config[setting] = ""
            return

        if len(value) > 32:
            await ctx.send(
                "`Error: Nickname exceeds character limit`\nUsage: {}set {} nickname\nOther options: unset".format(
                    config.BOT_PREFIX, setting
                )
            )
            return False
        else:
            self.config[setting] = value
            try:
                await self.guild.me.edit(nick=value)
            except discord.Forbidden:
                await ctx.send(
                    "`Error: Cannot set nickname. Please check bot permissions."
                )

    async def command_channel(self, setting, value, ctx):

        if value.lower() == "unset":
            self.config[setting] = None
            return

        chan = None
        for converter in (
            commands.TextChannelConverter,
            commands.VoiceChannelConverter,
        ):
            try:
                chan = await converter().convert(ctx, value)
                break
            except commands.ChannelNotFound:
                pass

        if not chan:
            await ctx.send(
                "`Error: Channel not found`\nUsage: {}set {} channel\nOther options: unset".format(
                    config.BOT_PREFIX, setting
                )
            )
            return False
        self.config[setting] = chan.id

    async def start_voice_channel(self, setting, value, ctx):

        if value.lower() == "unset":
            self.config[setting] = None
            return

        try:
            vc = await commands.VoiceChannelConverter().convert(ctx, value)
        except commands.ChannelNotFound:
            await ctx.send(
                "`Error: Voice channel not found`\nUsage: {}set {} vchannel\nOther options: unset".format(
                    config.BOT_PREFIX, setting
                )
            )
            return False
        self.config[setting] = vc.id
        self.config["vc_timeout"] = False

    async def user_must_be_in_vc(self, setting, value, ctx):
        if value.lower() == "true":
            self.config[setting] = True
        elif value.lower() == "false":
            self.config[setting] = False
        else:
            await ctx.send(
                "`Error: Value must be True/False`\nUsage: {}set {} True/False".format(
                    config.BOT_PREFIX, setting
                )
            )
            return False

    async def button_emote(self, setting, value, ctx):

        if value.lower() == "unset":
            self.config[setting] = ""
            return

        emoji = utils.get_emoji(self.guild, value)
        if emoji is None:
            await ctx.send(
                "`Error: Invalid emote`\nUsage: {}set {} emote\nOther options: unset".format(
                    config.BOT_PREFIX, setting
                )
            )
            return False
        elif isinstance(emoji, discord.Emoji):
            emoji = str(emoji.id)
        self.config[setting] = emoji

    async def default_volume(self, setting, value, ctx):
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

        self.config[setting] = value

    async def vc_timeout(self, setting, value, ctx):

        if not config.ALLOW_VC_TIMEOUT_EDIT:
            await ctx.send("`Error: This value cannot be modified`")
            return False

        if value.lower() == "true":
            self.config[setting] = True
            self.config["start_voice_channel"] = None
        elif value.lower() == "false":
            self.config[setting] = False
        else:
            await ctx.send(
                "`Error: Value must be True/False`\nUsage: {}set {} True/False".format(
                    config.BOT_PREFIX, setting
                )
            )
            return False
