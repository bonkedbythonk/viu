"""
Defines the PlayerResult dataclass, which encapsulates the result of a player session.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlayerResult:
    """
    Result of a player session.

    Attributes:
        episode: The episode identifier or label.
        stop_time: The time at which playback stopped.
        total_time: The total duration of the media.
    """

    episode: str
    stop_time: str | None = None
    total_time: str | None = None
