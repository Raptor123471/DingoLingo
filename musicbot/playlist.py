import random
from collections import deque

from config import config


class Playlist:
    """Stores the youtube links of songs to be played and already played and offers basic operation on the queues"""

    def __init__(self):
        # Stores the links os the songs in queue and the ones already played
        self.playque = deque()
        self.playhistory = deque()

        # A seperate history that remembers the names of the tracks that were played
        self.trackname_history = deque()

        self.loop = False

    def __len__(self):
        return len(self.playque)

    def add_name(self, trackname):
        self.trackname_history.append(trackname)
        if len(self.trackname_history) > config.MAX_TRACKNAME_HISTORY_LENGTH:
            self.trackname_history.popleft()

    def add(self, track):
        self.playque.append(track)

    def remove(self, queue_number):
        if queue_number > len(self.playque):
            return
        del self.playque[queue_number-1]

    def next(self, song_played):

        if self.loop == True:
            self.playque.appendleft(self.playhistory[-1])

        if len(self.playque) == 0:
            return None

        if len(self.playque) == 0:
            return None

        if song_played != "Dummy":
            if len(self.playhistory) > config.MAX_HISTORY_LENGTH:
                self.playhistory.popleft()

        return self.playque[0]

    def prev(self, current_song):

        if current_song is None:
            self.playque.appendleft(self.playhistory[-1])
            return self.playque[0]

        ind = self.playhistory.index(current_song)
        self.playque.appendleft(self.playhistory[ind - 1])
        if current_song != None:
            self.playque.insert(1, current_song)

    def shuffle(self):
        random.shuffle(self.playque)

    def empty(self):
        self.playque.clear()
        self.playhistory.clear()

    def get_title(self, queue_number):
        if queue_number > len(self.playque):
            return None
        return self.playque[queue_number-1].info.title
