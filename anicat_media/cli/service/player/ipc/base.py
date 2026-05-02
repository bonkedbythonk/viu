from abc import ABC, abstractmethod
from typing import Optional

from .....core.config import StreamConfig
from .....libs.media_api.types import MediaItem
from .....libs.player.base import BasePlayer
from .....libs.player.params import PlayerParams
from .....libs.player.types import PlayerResult
from .....libs.provider.anime.base import BaseAnimeProvider
from .....libs.provider.anime.types import Anime
from ....service.registry import MediaRegistryService


class BaseIPCPlayer(ABC):
    """
    Abstract Base Class defining the contract for all media players with ipc control.
    """

    def __init__(self, stream_config: StreamConfig):
        self.stream_config = stream_config

    @abstractmethod
    def play(
        self,
        player: BasePlayer,
        player_params: PlayerParams,
        provider: Optional[BaseAnimeProvider] = None,
        anime: Optional[Anime] = None,
        registry: Optional[MediaRegistryService] = None,
        media_item: Optional[MediaItem] = None,
    ) -> PlayerResult:
        """
        Plays the given media URL.
        """
        pass
