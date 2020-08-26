# DingoLingo
A Discord music bot written in Python with support for Youtube, SoundCloud, Spotify, Bandcamp, Twitter, and custom files.


<h3>What's Coming?</h1>

  - See TODO in Projects tab

## Prerequisites:

#### API Keys
* Discord - https://discord.com/developers
* SoundCloud - No official method, must search/ask for key
* YouTube (optional) - https://console.developers.google.com/apis/api/youtube/overview

Obtained keys must be entered into ```config/config.py```

#### Requirements

* Installation of Python 3.7+

Install dependancies:
```
pip install -r requirements.txt
```
* Located in ```/config```

For Linux:
* ffmpeg
* libffi-dev 
* libnacl-dev 

### Installing - Self hosting

1. Download release if available, alternatively download repository zip
2. Complete Prerequisites
3. Start ```run.py``` in project root

## Commands:

### Music

After the bot has joined your server, use ```$help``` to display help and command information.


```
$p [link/video title/key words/playlist-link/soundcloud link/spotify link/bandcamp link/twitter link]
```

* Plays the audio of supported website
    - A link to the video (https://ww...)
    - The title of a video ex. (Gennifer Flowers - Fever Dolls)
    - A link to a YouTube playlist
* If a song is playing, it will be added to queue

```
$q
```

* Show the list of songs in queue

```
$l
```

* Loop the current playing song

```
$pause
```

* Pauses the current song.

```
$resume
```

* Resumes the paused song.

```
$stop
```

* Stops the current song and clears the playqueue.

```
$prev
```

* Goes back one song and plays the last song again.

```
$np
```

* Shows more details about the current song.

### General

```
$c
```

* Connects the bot to the user's voice channel

```
$dc
```

* Disconnects the bot from the current voice channel

```
$history
```
* Shows you the titles of the X last played songs. Configurable in config.config.py


### Utility

```
$version
```

* Show verison information

```
$reset
```

* Disconnect and reconnect to the voice channel

```
$ping
```

* Test bot connectivity

```
$addbot
```

* Displays information on how to add the bot to another server of yours.

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the [GNU General Public License](LICENSE.txt) as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.


## Acknowledgments

https://github.com/adriansteffan/DiscordJockey
