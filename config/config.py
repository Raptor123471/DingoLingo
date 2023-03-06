# fmt: off

import os
import json

from musicbot.utils import get_env_var, alchemize_url


DEFAULTS = {
    "BOT_TOKEN": "YOUR_TOKEN_GOES_HERE",
    "SPOTIFY_ID": "",
    "SPOTIFY_SECRET": "",

    "BOT_PREFIX": "d!",  # set to empty string to disable
    "ENABLE_SLASH_COMMANDS": False,

    "VC_TIMEOUT": 600,  # seconds
    "VC_TIMOUT_DEFAULT": True,  # default template setting for VC timeout true= yes, timeout false= no timeout

    "MAX_SONG_PRELOAD": 5,  # maximum of 25
    "MAX_HISTORY_LENGTH": 10,
    "MAX_TRACKNAME_HISTORY_LENGTH": 15,

    # if database is not one of sqlite, postgres or MySQL
    # you need to provide the url in SQL Alchemy-supported format.
    # Must be async-compatible
    # CHANGE ONLY IF YOU KNOW WHAT YOU'RE DOING
    "DATABASE_URL": os.getenv("HEROKU_DB") or "sqlite:///settings.db",
}


if os.path.isfile("config.json"):
    with open("config.json") as f:
        DEFAULTS.update(json.load(f))
elif not os.getenv("DANDELION_INSTALLING"):
    with open("config.json", "w") as f:
        json.dump(DEFAULTS, f, indent=2)


for key, default in DEFAULTS.items():
    globals()[key] = get_env_var(key, default)


MENTION_AS_PREFIX = True

ENABLE_BUTTON_PLUGIN = True

EMBED_COLOR = 0x4dd4d0  # replace after'0x' with desired hex code ex. '#ff0188' >> '0xff0188'

SUPPORTED_EXTENSIONS = (".webm", ".mp4", ".mp3", ".avi", ".wav", ".m4v", ".ogg", ".mov")


COOKIE_PATH = "/config/cookies/cookies.txt"

GLOBAL_DISABLE_AUTOJOIN_VC = False

ALLOW_VC_TIMEOUT_EDIT = True  # allow or disallow editing the vc_timeout guild setting


actual_prefix = (  # for internal use
    BOT_PREFIX
    if BOT_PREFIX
    else ("/" if ENABLE_SLASH_COMMANDS else "@bot ")
)

# set db url during install even if it's overriden by env
if os.getenv("DANDELION_INSTALLING") and not DATABASE_URL:
    DATABASE_URL = DEFAULTS["DATABASE_URL"]
DATABASE = alchemize_url(DATABASE_URL)
DATABASE_LIBRARY = DATABASE.partition("+")[2].partition(":")[0]


STARTUP_MESSAGE = "Starting Bot..."
STARTUP_COMPLETE_MESSAGE = "Startup Complete"

NO_GUILD_MESSAGE = "Error: Please join a voice channel or enter the command in guild chat"
USER_NOT_IN_VC_MESSAGE = "Error: Please join the active voice channel to use commands and buttons"
WRONG_CHANNEL_MESSAGE = "Error: Please use configured command channel"
NOT_CONNECTED_MESSAGE = "Error: Bot not connected to any voice channel"
ALREADY_CONNECTED_MESSAGE = "Error: Already connected to a voice channel"
CHANNEL_NOT_FOUND_MESSAGE = "Error: Could not find channel"
DEFAULT_CHANNEL_JOIN_FAILED = "Error: Could not join the default voice channel"
INVALID_INVITE_MESSAGE = "Error: Invalid invitation link"

ADD_MESSAGE = "To add this bot to your own Server, click [here]"  # brackets will be the link text

INFO_HISTORY_TITLE = "Songs Played:"

SONGINFO_UPLOADER = "Uploader: "
SONGINFO_DURATION = "Duration: "
SONGINFO_SECONDS = "s"
SONGINFO_LIKES = "Likes: "
SONGINFO_DISLIKES = "Dislikes: "
SONGINFO_NOW_PLAYING = "Now Playing"
SONGINFO_QUEUE_ADDED = "Added to queue"
SONGINFO_SONGINFO = "Song info"
SONGINFO_ERROR = "Error: Unsupported site or age restricted content. To enable age restricted content check the documentation/wiki."
SONGINFO_PLAYLIST_QUEUED = "Queued playlist :page_with_curl:"
SONGINFO_UNKNOWN_DURATION = "Unknown"
QUEUE_EMPTY = "Queue is empty :x:"

HELP_ADDBOT_SHORT = "Add Bot to another server"
HELP_ADDBOT_LONG = "Gives you the link for adding this bot to another server of yours."
HELP_CONNECT_SHORT = "Connect bot to voicechannel"
HELP_CONNECT_LONG = "Connects the bot to the voice channel you are currently in"
HELP_DISCONNECT_SHORT = "Disonnect bot from voicechannel"
HELP_DISCONNECT_LONG = "Disconnect the bot from the voice channel and stop audio."

HELP_SETTINGS_SHORT = "View and set bot settings"
HELP_SETTINGS_LONG = "View and set bot settings in the server. Usage: {}settings setting_name value".format(actual_prefix)

HELP_HISTORY_SHORT = "Show history of songs"
HELP_HISTORY_LONG = "Shows the " + str(MAX_TRACKNAME_HISTORY_LENGTH) + " last played songs."
HELP_PAUSE_SHORT = "Pause Music"
HELP_PAUSE_LONG = "Pauses the AudioPlayer. Use it again to resume playback."
HELP_VOL_SHORT = "Change volume %"
HELP_VOL_LONG = "Changes the volume of the AudioPlayer. Argument specifies the % to which the volume should be set."
HELP_PREV_SHORT = "Go back one Song"
HELP_PREV_LONG = "Plays the previous song again."
HELP_SKIP_SHORT = "Skip a song"
HELP_SKIP_LONG = "Skips the currently playing song and goes to the next item in the queue."
HELP_SONGINFO_SHORT = "Info about current Song"
HELP_SONGINFO_LONG = "Shows details about the song currently being played and posts a link to the song."
HELP_STOP_SHORT = "Stop Music"
HELP_STOP_LONG = "Stops the AudioPlayer and clears the songqueue"
HELP_MOVE_LONG = f"{actual_prefix}move [position] [new position]"
HELP_MOVE_SHORT = "Moves a track in the queue"
HELP_YT_SHORT = "Play a supported link or search on youtube"
HELP_YT_LONG = f"{actual_prefix}p [link/video title/keywords/playlist/soundcloud link/spotify link/bandcamp link/twitter link]"
HELP_PING_SHORT = "Pong"
HELP_PING_LONG = "Test bot response status"
HELP_CLEAR_SHORT = "Clear the queue."
HELP_CLEAR_LONG = "Clears the queue and skips the current song."
HELP_LOOP_SHORT = "Loops the currently playing song or queue."
HELP_LOOP_LONG = "Loops the currently playing song or queue. Modes are all/single/off."
HELP_QUEUE_SHORT = "Shows the songs in queue."
HELP_QUEUE_LONG = "Shows the number of songs in queue, up to 10."
HELP_SHUFFLE_SHORT = "Shuffle the queue"
HELP_SHUFFLE_LONG = "Randomly sort the songs in the current queue"
HELP_RESET_SHORT = "Disconnect and reconnect"
HELP_RESET_LONG = "Stop player, disconnect and reconnect to the channel you are in"
HELP_REMOVE_SHORT = "Remove a song"
HELP_REMOVE_LONG = "Allows to remove a song from the queue by typing it's position (defaults to the last song)."

ABSOLUTE_PATH = ""  # do not modify
