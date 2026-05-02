from abc import ABC, abstractmethod

import httpx

from ..config.model import DownloadsConfig
from .model import DownloadResult
from .params import DownloadParams


class BaseDownloader(ABC):
    client: httpx.Client

    def __init__(self, config: DownloadsConfig):
        self.config = config

        # Increase timeouts and add retries for robustness
        transport = httpx.HTTPTransport(retries=3)
        self.client = httpx.Client(
            transport=transport,
            timeout=httpx.Timeout(15.0, connect=60.0),
            follow_redirects=True,
        )

    @abstractmethod
    def download(self, params: DownloadParams) -> DownloadResult:
        pass
