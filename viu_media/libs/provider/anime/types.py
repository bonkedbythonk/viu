"""
Core type definitions for anime providers.

These types define the data structures returned by anime provider backends
(e.g., AllAnime). They are used across the CLI, interactive menus, and
download/streaming services.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class ProviderName(str, Enum):
    """Supported anime provider backends."""

    ALLANIME = "allanime"


class ProviderServer(str, Enum):
    """Known streaming server names returned by providers."""

    TOP = "TOP"


class StreamLink(BaseModel):
    """A single streamable link with quality and optional headers."""

    link: str
    quality: str = ""
    headers: dict = {}


class Subtitle(BaseModel):
    """A subtitle track associated with a stream."""

    url: str
    lang: str = "eng"


class Server(BaseModel):
    """A streaming server containing one or more stream links."""

    name: str
    links: List[StreamLink] = []
    headers: dict = {}
    subtitles: List[Subtitle] = []


class SearchResult(BaseModel):
    """A single search result from a provider."""

    id: str
    title: str
    url: str = ""
    available_episodes: Optional[Dict[str, List[str]]] = None


class SearchResults(BaseModel):
    """Container for provider search results."""

    results: List[SearchResult] = []


class Anime(BaseModel):
    """Full anime details from a provider, including episode information."""

    id: str
    title: str
    url: str = ""
    available_episodes: Optional[Dict[str, List[str]]] = None
