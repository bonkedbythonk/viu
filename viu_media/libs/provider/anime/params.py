"""
Parameter types for anime provider operations.

These dataclasses define the inputs for search, episode lookup, and
stream retrieval operations on anime providers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SearchParams:
    """Parameters for searching anime on a provider."""

    query: str
    translation_type: str = "sub"


@dataclass
class AnimeParams:
    """Parameters for fetching full anime details from a provider."""

    id: str
    query: str = ""


@dataclass
class EpisodeStreamsParams:
    """Parameters for fetching stream links for a specific episode."""

    anime_id: str
    query: str = ""
    episode: str = ""
    translation_type: str = "sub"
