"""Search functionality."""

from anicat_media.core.utils.fuzzy import fuzz
from anicat_media.core.utils.normalizer import normalize_title
from anicat_media.libs.provider.anime.types import SearchResult, ProviderName
from anicat_media.libs.media_api.types import MediaItem


def find_best_match_title(
    provider_results_map: dict[str, SearchResult],
    provider: ProviderName,
    media_item: MediaItem,
) -> str:
    """Find the best match title using fuzzy matching for both the english AND romaji title.

    Parameters:
        provider_results_map (dict[str, SearchResult]): The map of provider results.
        provider (ProviderName): The provider name from the config.
        media_item (MediaItem): The media item to match.

    Returns:
        str: The best match title.
    """
    return max(
        provider_results_map.keys(),
        key=lambda p_title: max(
            fuzz.ratio(
                normalize_title(p_title, provider.value).lower(),
                (media_item.title.romaji or "").lower(),
            ),
            fuzz.ratio(
                normalize_title(p_title, provider.value).lower(),
                (media_item.title.english or "").lower(),
            ),
        ),
    )
