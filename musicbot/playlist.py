import random
from typing import Optional
from collections import deque

from config import config
from musicbot.songinfo import Song


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

    def next(self, song_played: Optional[Song]) -> Optional[Song]:

        if self.loop == "single":
            self.playque.appendleft(self.playhistory[-1])
        elif self.loop == "all":
            self.playque.append(self.playhistory[-1])

        if len(self.playque) == 0:
            return None

        if song_played != "Dummy":
            if len(self.playhistory) > config.MAX_HISTORY_LENGTH:
                self.playhistory.popleft()

        return self.playque[0]

    def prev(self, current_song: Optional[Song]) -> Song:

        if current_song is None:
            self.playque.appendleft(self.playhistory[-1])
            return self.playque[0]

        ind = self.playhistory.index(current_song)
        prev = self.playhistory[ind - 1]
        self.playque.appendleft(prev)
        if current_song is not None:
            self.playque.insert(1, current_song)
        return prev

    def shuffle(self):
        random.shuffle(self.playque)

    def move(self, oldindex: int, newindex: int):
        temp = self.playque[oldindex]
        del self.playque[oldindex]
        self.playque.insert(newindex, temp)

    def empty(self):
        self.playque.clear()
        self.playhistory.clear()
