from config import config

# A dictionary that remembers which guild belongs to which audiocontroller
guild_to_audiocontroller = {}

# A dictionary that remembers which settings belongs to which guild
guild_to_settings = {}


def get_guild(bot, command):
    """Gets the guild a command belongs to. Useful, if the command was sent via pm."""
    if command.guild is not None:
        return command.guild
    for guild in bot.guilds:
        for channel in guild.voice_channels:
            if command.author in channel.members:
                return guild
    return None


async def connect_to_channel(guild, dest_channel_name, ctx, switch=False, default=True):
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
                except:
                    await ctx.send(config.NOT_CONNECTED_MESSAGE)

            await channel.connect()
            return

    if default:
        try:
            await guild.voice_channels[0].connect()
        except:
            await ctx.send(config.DEFAULT_CHANNEL_JOIN_FAILED)
    else:
        await ctx.send(config.CHANNEL_NOT_FOUND_MESSAGE + str(dest_channel_name))


async def is_connected(ctx):
    try:
        voice_channel = ctx.guild.voice_client.channel
        return voice_channel
    except:
        return None


async def play_check(ctx):

    sett = guild_to_settings[ctx.guild]

    cm_channel = sett.get('command_channel')
    vc_rule = sett.get('user_must_be_in_vc')

    if cm_channel != None:
        if cm_channel != ctx.message.channel.id:
            await ctx.send(config.WRONG_CHANNEL_MESSAGE)
            return False

    if vc_rule == True:
        author_voice = ctx.message.author.voice
        bot_vc = ctx.guild.voice_client.channel
        if author_voice == None:
            await ctx.send(config.USER_NOT_IN_VC_MESSAGE)
            return False
        elif ctx.message.author.voice.channel != bot_vc:
            await ctx.send(config.USER_NOT_IN_VC_MESSAGE)
            return False
