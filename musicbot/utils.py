from config import config

# A dictionary that remembers which guild belongs to which audiocontroller
guild_to_audiocontroller = {}


def get_guild(bot, command):
    """Gets the guild a command belongs to. Useful, if the command was sent via pm."""
    if command.guild is not None:
        return command.guild
    for guild in bot.guilds:
        for channel in guild.voice_channels:
            if command.author in channel.members:
                return guild
    return None


async def send_message(ctx, message):
    await ctx.send("```\n" + message + "\n```")


async def is_connected(ctx):
    try:
        voice_channel = ctx.guild.voice_client.channel
        print(voice_channel)
        return voice_channel
    except:
        return None
