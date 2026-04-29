import logging
from typing import Optional

from ....anime.types import Server
from .megacloud import MegaCloudExtractor

logger = logging.getLogger(__name__)


def extract_server(embed_url: str) -> Optional[Server]:
    """
    Acts as a router to select the correct extractor based on the embed URL.

    Args:
        embed_url: The URL of the video host's embed page.

    Returns:
        A Server object containing the stream links, or None if extraction fails.
    """
    hostname = embed_url.split("/")[2]

    if "megacloud" in hostname or "megaplay" in hostname:
        return MegaCloudExtractor().extract(embed_url)

    # In the future, you could add other extractors here:
    # if "streamsb" in hostname:
    #     return StreamSbExtractor().extract(embed_url)

    logger.warning(f"No extractor found for hostname: {hostname}")
    return None
