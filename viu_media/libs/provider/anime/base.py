"""
Abstract base class for anime providers.

All provider backends (e.g., AllAnime) must implement this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator, Optional

from .params import AnimeParams, EpisodeStreamsParams, SearchParams
from .types import Anime, SearchResults, Server


class BaseAnimeProvider(ABC):
    """Abstract base class that all anime provider implementations must extend."""

    @abstractmethod
    def search(self, params: SearchParams) -> Optional[SearchResults]:
        """Search for anime by query string."""
        ...

    @abstractmethod
    def get(self, params: AnimeParams) -> Optional[Anime]:
        """Get full details for a specific anime by provider ID."""
        ...

    @abstractmethod
    def episode_streams(self, params: EpisodeStreamsParams) -> Optional[Iterator[Server]]:
        """Get an iterator of streaming servers for a specific episode."""
        ...
