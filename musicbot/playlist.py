import random
from typing import Optional
from collections import deque

from discord import Embed

from config import config
from musicbot.songinfo import Song


class PlaylistError(Exception):
    pass


class Playlist:
    """Stores the youtube links of songs to be played and already played and offers basic operation on the queues"""

    def __init__(self):
        # Stores the links os the songs in queue and the ones already played
        self.playque: deque[Song] = deque()
        self.playhistory: deque[Song] = deque()

        # A seperate history that remembers the names of the tracks that were played
        self.trackname_history: deque[str] = deque()

        self.loop = "off"

    def __len__(self):
        return len(self.playque)

    def add_name(self, trackname: str):
        self.trackname_history.append(trackname)
        if len(self.trackname_history) > config.MAX_TRACKNAME_HISTORY_LENGTH:
            self.trackname_history.popleft()

    def add(self, track: Song):
        self.playque.append(track)

    def has_next(self) -> bool:
        return len(self.playque) >= (2 if self.loop == "off" else 1)

    def has_prev(self) -> bool:
        return len(self.playhistory if self.loop == "off" else self.playque) != 0

    def next(self) -> Optional[Song]:
        if len(self.playque) == 0:
            return None

        if self.loop == "off":
            self.playhistory.append(self.playque.popleft())
            if len(self.playhistory) > config.MAX_HISTORY_LENGTH:
                self.playhistory.popleft()
            if len(self.playque) != 0:
                return self.playque[0]
            else:
                return None

        if self.loop == "all":
            self.playque.rotate(-1)

        return self.playque[0]

    def prev(self) -> Optional[Song]:
        if self.loop == "off":
            if len(self.playhistory) != 0:
                song = self.playhistory.pop()
                self.playque.appendleft(song)
                return song
            else:
                return None

        if len(self.playque) == 0:
            return None

        if self.loop == "all":
            self.playque.rotate()

        return self.playque[0]

    def shuffle(self):
        first = self.playque.popleft()
        random.shuffle(self.playque)
        self.playque.appendleft(first)

    def remove(self, index: int) -> Song:
        if index < 0:
            raise PlaylistError("Negative indexes are not supported.")
        if index == 0:
            raise PlaylistError(
                "Cannot remove the first song since it's already playing."
            )
        try:
            song = self.playque[index]
        except IndexError as e:
            raise PlaylistError("Invalid position.") from e
        del self.playque[index]
        return song

    def move(self, oldindex: int, newindex: int):
        if oldindex < 0 or newindex < 0:
            raise PlaylistError("Negative indexes are not supported.")
        if oldindex == 0 or newindex == 0:
            raise PlaylistError(
                "Cannot move the first song since it's already playing."
            )
        try:
            temp = self.playque[oldindex]
        except IndexError as e:
            raise PlaylistError("Invalid position.") from e
        del self.playque[oldindex]
        self.playque.insert(newindex, temp)

    def empty(self):
        self.playque.clear()
        self.playhistory.clear()

    def queue_embed(self) -> Embed:
        embed = Embed(
            title=":scroll: Queue [{}]".format(len(self.playque)),
            color=config.EMBED_COLOR,
        )

        for counter, song in enumerate(
            list(self.playque)[: config.MAX_SONG_PRELOAD], start=1
        ):
            embed.add_field(
                name="{}.".format(str(counter)),
                value="[{}]({})".format(
                    song.info.title or song.info.webpage_url, song.info.webpage_url
                ),
                inline=False,
            )

        return embed
