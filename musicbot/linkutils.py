import requests
import re
from bs4 import BeautifulSoup
from enum import Enum
from config import config


def convert_shortlink(shortlink):
    """Converts shortlink like  https://youtu.be/SZa9bPia9YM?t=31 to full url"""
    if("?t=" in shortlink):
        timestamp = "&{}".format(shortlink.split('?')[1])
    else:
        timestamp = ""
    shortlink = shortlink.split('/')
    videocode = shortlink[3].split('?')[0]
    fullformat = "https://www.youtube.com/watch?v={}&feature=youtu.be{}".format(
        videocode, timestamp)
    return fullformat
    # https://www.youtube.com/watch?v=SZa9bPia9YM&feature=youtu.be&t=31
    # https://youtu.be/SZa9bPia9YM?t=31


def clean_sclink(track):
    if track.startswith("https://m."):
        track = track.replace("https://m.", "https://")
    if track.startswith("http://m."):
        track = track.replace("http://m.", "https://")
    return track


def convert_spotify(url):
    regex = re.compile(
        "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")

    if re.search(regex, url):
        result = regex.search(url)
        url = result.group(0)

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    title = soup.find('title')
    title = title.string
    title = title.replace(', a song by', '').replace(' on Spotify', '')

    return title


def get_url(content):

    regex = re.compile(
        "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")

    if re.search(regex, content):
        result = regex.search(content)
        url = result.group(0)
        return url
    else:
        return None


class Sites(Enum):
    Spotify = "Spotify"
    YouTube = "YouTube"
    Twitter = "Twitter"
    SoundCloud = "SoundCloud"
    Bandcamp = "Bandcamp"
    Custom = "Custom"
    Unknown = "Unknown"


def identify_url(url):
    if url is None:
        return Sites.Unknown

    if "https://www.youtu" in url or "https://youtu.be" in url:
        return Sites.YouTube

    if "https://open.spotify.com/track/" in url:
        return Sites.Spotify

    if "bandcamp.com/track/" in url:
        return Sites.Bandcamp

    if "https://twitter.com/" in url:
        return Sites.Twitter

    if url.lower().endswith(config.SUPPORTED_EXTENSIONS):
        return Sites.Custom

    if "soundcloud.com/" in url:
        return Sites.SoundCloud

    # If no match
    return Sites.Unknown
