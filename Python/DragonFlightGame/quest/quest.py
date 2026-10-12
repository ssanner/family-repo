"""Shared lifecycle for playable quests."""

from abc import ABC, abstractmethod


class Quest(ABC):
    """Base class for a game quest and its retry lifecycle."""

    def __init__(self, game):
        self.game = game
        self.finished = False

    @abstractmethod
    def start(self):
        """Prepare the quest for a new attempt."""

    @abstractmethod
    def update(self, dt):
        """Advance this quest by one frame."""

    @abstractmethod
    def restart(self):
        """Restart this quest without changing to another quest."""
