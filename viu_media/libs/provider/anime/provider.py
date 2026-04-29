"""
Provider factory — creates anime provider instances by name.

This module acts as the entry point for instantiating concrete provider
backends. The actual provider implementations (e.g., AllAnime) should be
registered here.
"""

from __future__ import annotations

import logging

from .base import BaseAnimeProvider
from .types import ProviderName

logger = logging.getLogger(__name__)


def create_provider(provider_name: str | ProviderName) -> BaseAnimeProvider:
    """
    Factory function to create an anime provider instance by name.

    Args:
        provider_name: The name of the provider to instantiate (e.g., "allanime").

    Returns:
        An instance of the requested provider.

    Raises:
        ValueError: If the provider name is not recognized.
    """
    if isinstance(provider_name, ProviderName):
        name = provider_name.value
    else:
        name = provider_name

    if name == "allanime":
        try:
            from importlib import import_module

            mod = import_module(".allanime", package=__package__)
            return mod.AllAnimeProvider()  # type: ignore[attr-defined]
        except ImportError:
            raise ImportError(
                f"The '{name}' provider backend is not installed. "
                "This is a separate package — please check the project documentation."
            )

    raise ValueError(
        f"Unknown provider: '{name}'. Available providers: {[p.value for p in ProviderName]}"
    )
