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
            "command_channel": 0,
            "start_voice_channel": 0,
            "user_must_be_in_vc": True,
            "button_emote": "",
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

    def format(self):
        embed = discord.Embed(
            title="Settings", color=config.EMBED_COLOR)

        for key in self.config.keys():
            if self.config.get(key) == "":
                embed.add_field(name=key, value="None", inline=False)
            else:
                embed.add_field(
                    name=key, value=self.config.get(key), inline=False)

        return embed

    async def process_setting(self, setting, value, ctx):

        switcher = {
            'default_nickname': lambda: self.default_nickname(setting, value, ctx),
            'command_channel': lambda: self.command_channel(setting, value, ctx),
            'start_voice_channel': lambda: self.start_voice_channel(setting, value, ctx),
            'user_must_be_in_vc': lambda: self.user_must_be_in_vc(setting, value, ctx),
            'button_emote': lambda: self.button_emote(setting, value, ctx),
        }
        func = switcher.get(setting)

        if func is None:
            return False
        else:
            return await func()

    # -----setting methods-----

    async def default_nickname(self, setting, value, ctx):
        if len(value) > 32:
            return "Error: Nickname is too long"
        else:
            self.config[setting] = value

    async def command_channel(self, setting, value, ctx):
        found = False
        for chan in self.guild.text_channels:
            if chan.name.lower() == value.lower():
                self.config[setting] = chan.id
                found = True
        if found == False:
            await ctx.send("Error: Channel name not found")

    async def start_voice_channel(self, setting, value, ctx):
        found = False
        for vc in self.guild.voice_channels:
            if vc.name.lower() == value.lower():
                self.config[setting] = vc.id
                found = True
        if found == False:
            await ctx.send("Error: Voice channel name not found")

    async def user_must_be_in_vc(self, setting, value, ctx):
        if value.lower() == "true":
            self.config[setting] = True
        elif value.lower() == "false":
            self.config[setting] = False
        else:
            await ctx.send("Error: Value must be True/False")

    async def button_emote(self, setting, value, ctx):
        emoji = discord.utils.get(self.guild.emojis, name=value)
        if emoji is None:
            await ctx.send("Error: Emote name not found on server")
        else:
            self.config[setting] = value
