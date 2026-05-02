"""
The player package provides abstractions and implementations for media player integration in Anicat.

This package defines the base player interface, player parameter/result types, and concrete implementations for various media players (e.g., MPV, VLC, Syncplay).
"""

from .player import create_player

__all__ = ["create_player"]
