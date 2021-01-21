import os
import json
import discord
import asyncio
from config import config

dir_path = os.path.dirname(os.path.realpath(__file__))


class Settings():

    def __init__(self, guild):
        self.guild = guild
        self.json_data = None
        self.config = None
        self.path = '{}/generated/settings.json'.format(dir_path)

        self.settings_template = {
            "id": 0,
            "default_nickname": "",
            "command_channel": None,
            "start_voice_channel": None,
            "user_must_be_in_vc": True,
            "button_emote": "",
            "default_volume": 100
        }

        self.reload()
        self.upgrade()

    async def write(self, setting, value, ctx):
        response = await self.process_setting(setting, value, ctx)

        with open(self.path, 'w') as source:
            json.dump(self.json_data, source)
        self.reload()
        return response

    def reload(self):
        source = open(self.path, 'r')
        self.json_data = json.load(source)

        target = None

        for server in self.json_data:
            server = self.json_data[server]

            if server['id'] == self.guild.id:
                target = server

        if target == None:
            self.create()
            return

        self.config = target

    def upgrade(self):
        refresh = False
        for key in self.settings_template.keys():
            if not key in self.config:
                self.config[key] = self.settings_template.get(key)
                refresh = True
        if refresh:
            self.reload()

    def create(self):

        self.json_data[self.guild.id] = self.settings_template
        self.json_data[self.guild.id]['id'] = self.guild.id

        with open(self.path, 'w') as source:
            json.dump(self.json_data, source)
        self.reload()

    def get(self, setting):
        return self.config[setting]

    async def format(self):
        embed = discord.Embed(
            title="Settings", description=self.guild.name, color=config.EMBED_COLOR)

        embed.set_thumbnail(url=self.guild.icon_url)
        embed.set_footer(
            text="Usage: {}set setting_name value".format(config.BOT_PREFIX))

        exclusion_keys = ['id']

        for key in self.config.keys():
            if key in exclusion_keys:
                continue

            if self.config.get(key) == "" or self.config.get(key) == None:

                embed.add_field(name=key, value="Not Set", inline=False)
                continue

            elif key == "start_voice_channel":
                if self.config.get(key) != None:
                    found = False
                    for vc in self.guild.voice_channels:
                        if vc.id == self.config.get(key):
                            embed.add_field(
                                name=key, value=vc.name, inline=False)
                            found = True
                    if found == False:
                        embed.add_field(
                            name=key, value="Invalid VChannel", inline=False)

                    continue

            elif key == "command_channel":
                if self.config.get(key) != None:
                    found = False
                    for chan in self.guild.text_channels:
                        if chan.id == self.config.get(key):
                            embed.add_field(
                                name=key, value=chan.name, inline=False)
                            found = True
                    if found == False:
                        embed.add_field(
                            name=key, value="Invalid Channel", inline=False)
                    continue

            embed.add_field(name=key, value=self.config.get(key), inline=False)

        return embed

    async def process_setting(self, setting, value, ctx):

        switcher = {
            'default_nickname': lambda: self.default_nickname(setting, value, ctx),
            'command_channel': lambda: self.command_channel(setting, value, ctx),
            'start_voice_channel': lambda: self.start_voice_channel(setting, value, ctx),
            'user_must_be_in_vc': lambda: self.user_must_be_in_vc(setting, value, ctx),
            'button_emote': lambda: self.button_emote(setting, value, ctx),
            'default_volume': lambda: self.default_volume(setting, value, ctx),
        }
        func = switcher.get(setting)

        if func is None:
            return None
        else:
            answer = await func()
            if answer == None:
                return True
            else:
                return answer

    # -----setting methods-----

    async def default_nickname(self, setting, value, ctx):

        if value.lower() == "unset":
            self.config[setting] = ""
            return

        if len(value) > 32:
            await ctx.send("`Error: Nickname exceeds character limit`\nUsage: {}set {} nickname\nOther options: unset".format(config.BOT_PREFIX, setting))
            return False
        else:
            self.config[setting] = value
            await self.guild.me.edit(nick=value)

    async def command_channel(self, setting, value, ctx):

        if value.lower() == "unset":
            self.config[setting] = None
            return

        found = False
        for chan in self.guild.text_channels:
            if chan.name.lower() == value.lower():
                self.config[setting] = chan.id
                found = True
        if found == False:
            await ctx.send("`Error: Channel name not found`\nUsage: {}set {} channelname\nOther options: unset".format(config.BOT_PREFIX, setting))
            return False

    async def start_voice_channel(self, setting, value, ctx):

        if value.lower() == "unset":
            self.config[setting] = None
            return

        found = False
        for vc in self.guild.voice_channels:
            if vc.name.lower() == value.lower():
                self.config[setting] = vc.id
                found = True
        if found == False:
            await ctx.send("`Error: Voice channel name not found`\nUsage: {}set {} vchannelname\nOther options: unset".format(config.BOT_PREFIX, setting))
            return False

    async def user_must_be_in_vc(self, setting, value, ctx):
        if value.lower() == "true":
            self.config[setting] = True
        elif value.lower() == "false":
            self.config[setting] = False
        else:
            await ctx.send("`Error: Value must be True/False`\nUsage: {}set {} True/False".format(config.BOT_PREFIX, setting))
            return False

    async def button_emote(self, setting, value, ctx):

        if value.lower() == "unset":
            self.config[setting] = ""
            return

        emoji = discord.utils.get(self.guild.emojis, name=value)
        if emoji is None:
            await ctx.send("`Error: Emote name not found on server`\nUsage: {}set {} emotename\nOther options: unset".format(config.BOT_PREFIX, setting))
            return False
        else:
            self.config[setting] = value

    async def default_volume(self, setting, value, ctx):
        try:
            value = int(value)
        except:
            await ctx.send("`Error: Value must be a number`\nUsage: {}set {} 0-100".format(config.BOT_PREFIX, setting))
            return False

        if value > 100 or value < 0:
            await ctx.send("`Error: Value must be a number`\nUsage: {}set {} 0-100".format(config.BOT_PREFIX, setting))
            return False

        self.config[setting] = value
