"""
Defines the abstract base class for all media player integrations in Anicat.

All concrete player implementations must inherit from BasePlayer and implement its methods.
"""

import subprocess
from abc import ABC, abstractmethod

from ...core.config import StreamConfig
from .params import PlayerParams
from .types import PlayerResult


class BasePlayer(ABC):
    """
    Abstract base class for all media player integrations.

    Subclasses must implement the play and play_with_ipc methods to provide playback functionality.
    """

    def __init__(self, config: StreamConfig):
        """
        Initialize the player with the given stream configuration.

        Args:
            config: StreamConfig object containing player configuration.
        """
        self.stream_config = config

    @abstractmethod
    def play(self, params: PlayerParams) -> PlayerResult:
        """
        Play the given media URL using the player.

        Args:
            params: PlayerParams object containing playback parameters.

        Returns:
            PlayerResult: Information about the playback session.
        """
        pass

    @abstractmethod
    def play_with_ipc(self, params: PlayerParams, socket_path: str) -> subprocess.Popen:
        """
        Play media using IPC (Inter-Process Communication) for enhanced control.

        Args:
            params: PlayerParams object containing playback parameters.
            socket_path: Path to the IPC socket for player control.

        Returns:
            subprocess.Popen: The running player process.
        """
        pass
