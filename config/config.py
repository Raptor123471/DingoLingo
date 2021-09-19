BOT_TOKEN: str = ""
SPOTIFY_ID: str = ""
SPOTIFY_SECRET: str = ""

BOT_PREFIX = "$"

EMBED_COLOR = 0x4dd4d0  #replace after'0x' with desired hex code ex. '#ff0188' >> '0xff0188'

SUPPORTED_EXTENSIONS = ('.webm', '.mp4', '.mp3', '.avi', '.wav', '.m4v', '.ogg', '.mov')

MAX_SONG_PRELOAD = 5  #maximum of 25

COOKIE_PATH = "/config/cookies/cookies.txt"

GLOBAL_DISABLE_AUTOJOIN_VC = False

VC_TIMEOUT = 600 #seconds
FORCE_VC_TIMEOUT = True

STARTUP_MESSAGE = "Starting Bot..."
STARTUP_COMPLETE_MESSAGE = "Startup Complete"

NO_GUILD_MESSAGE = 'Error: Please join a voice channel or enter the command in guild chat'
USER_NOT_IN_VC_MESSAGE = "Error: Please join the active voice channel to use commands"
WRONG_CHANNEL_MESSAGE = "Error: Please use configured command channel"
NOT_CONNECTED_MESSAGE = "Error: Bot not connected to any voice channel"
ALREADY_CONNECTED_MESSAGE = "Error: Already connected to a voice channel"
CHANNEL_NOT_FOUND_MESSAGE = "Error: Could not find channel"
DEFAULT_CHANNEL_JOIN_FAILED = "Error: Could not join the default voice channel"
INVALID_INVITE_MESSAGE = "Error: Invalid invitation link"

ADD_MESSAGE= "To add this bot to your own Server, click [here]" #brackets will be the link text

INFO_HISTORY_TITLE = "Songs Played:"
MAX_HISTORY_LENGTH = 10
MAX_TRACKNAME_HISTORY_LENGTH = 15

SONGINFO_UPLOADER = "Uploader: "
SONGINFO_DURATION = "Duration: "
SONGINFO_SECONDS = "s"
SONGINFO_LIKES = "Likes: "
SONGINFO_DISLIKES = "Dislikes: "
SONGINFO_NOW_PLAYING = "Now Playing"
SONGINFO_QUEUE_ADDED = "Added to queue"
SONGINFO_SONGINFO = "Song info"
SONGINFO_UNKNOWN_SITE = "Unknown site :question:"
SONGINFO_PLAYLIST_QUEUED = "Queued playlist :page_with_curl:"
SONGINFO_UNKNOWN_DURATION = "Unknown"

HELP_ADDBOT_SHORT = "Add Bot to another server"
HELP_ADDBOT_LONG = "Gives you the link for adding this bot to another server of yours."
HELP_CONNECT_SHORT = "Connect bot to voicechannel"
HELP_CONNECT_LONG = "Connects the bot to the voice channel you are currently in"
HELP_DISCONNECT_SHORT = "Disonnect bot from voicechannel"
HELP_DISCONNECT_LONG = "Disconnect the bot from the voice channel and stop audio."

HELP_SETTINGS_SHORT = "View and set bot settings"
HELP_SETTINGS_LONG = "View and set bot settings in the server. Usage: {}settings setting_name value".format(BOT_PREFIX)

HELP_HISTORY_SHORT = "Show history of songs"
HELP_HISTORY_LONG = "Shows the " + str(MAX_TRACKNAME_HISTORY_LENGTH) + " last played songs."
HELP_PAUSE_SHORT = "Pause Music"
HELP_PAUSE_LONG = "Pauses the AudioPlayer. Playback can be continued with the resume command."
HELP_VOL_SHORT = "Change volume %"
HELP_VOL_LONG = "Changes the volume of the AudioPlayer. Argument specifies the % to which the volume should be set."
HELP_PREV_SHORT = "Go back one Song"
HELP_PREV_LONG = "Plays the previous song again."
HELP_RESUME_SHORT = "Resume Music"
HELP_RESUME_LONG = "Resumes the AudioPlayer."
HELP_SKIP_SHORT = "Skip a song"
HELP_SKIP_LONG = "Skips the currently playing song and goes to the next item in the queue."
HELP_SONGINFO_SHORT = "Info about current Song"
HELP_SONGINFO_LONG = "Shows details about the song currently being played and posts a link to the song."
HELP_STOP_SHORT = "Stop Music"
HELP_STOP_LONG = "Stops the AudioPlayer and clears the songqueue"
HELP_YT_SHORT = "Play a supported link or search on youtube"
HELP_YT_LONG = ("$p [link/video title/key words/playlist-link/soundcloud link/spotify link/bandcamp link/twitter link]")
HELP_PING_SHORT = "Pong"
HELP_PING_LONG = "Test bot response status"
HELP_CLEAR_SHORT = "Clear the queue."
HELP_CLEAR_LONG = "Clears the queue and skips the current song."
HELP_LOOP_SHORT = "Loops the currently playing song, toggle on/off."
HELP_LOOP_LONG = "Loops the currently playing song and locks the queue. Use the command again to disable loop."
HELP_QUEUE_SHORT = "Shows the songs in queue."
HELP_QUEUE_LONG = "Shows the number of songs in queue, up to 10."
HELP_SHUFFLE_SHORT = "Shuffle the queue"
HELP_SHUFFLE_LONG = "Randomly sort the songs in the current queue"
HELP_CHANGECHANNEL_SHORT = "Change the bot channel"
HELP_CHANGECHANNEL_LONG = "Change the bot channel to the VC you are in"

ABSOLUTE_PATH = '' #do not modify