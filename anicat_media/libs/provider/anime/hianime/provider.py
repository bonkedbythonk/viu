import logging
from typing import Iterator, Optional

from ....provider.anime.base import BaseAnimeProvider
from ....provider.anime.params import AnimeParams, EpisodeStreamsParams, SearchParams
from ....provider.anime.types import Anime, SearchResults, Server
from ....provider.scraping.html_parser import get_elements_by_class
from . import constants, mappers
from .extractors import extract_server

logger = logging.getLogger(__name__)


class HiAnime(BaseAnimeProvider):
    """
    Provider for scraping anime data from HiAnime.

    This provider implements the search, get, and episode_streams methods
    to fetch anime information and video stream URLs from HiAnime's website
    and internal AJAX APIs.
    """

    HEADERS = {"Referer": constants.HIANIME_BASE_URL}

    def search(self, params: SearchParams) -> Optional[SearchResults]:
        """
        Searches HiAnime for a given query.

        Args:
            params: The search parameters containing the query.

        Returns:
            A SearchResults object containing the found anime, or None.
        """
        search_url = f"{constants.SEARCH_URL}?keyword={params.query}"
        try:
            response = self.client.get(search_url, follow_redirects=True)
            response.raise_for_status()

            # The search results are rendered in the HTML. We use our HTML parser
            # to find all elements with the class '.flw-item', which represent
            # individual anime search results.
            anime_elements = get_elements_by_class("flw-item", response.text)
            if not anime_elements:
                return None

            # The mapper will convert the raw HTML elements into our generic SearchResults model.
            return mappers.map_to_search_results(anime_elements, response.text)
        except Exception as e:
            logger.error(
                f"Failed to perform search on HiAnime for query '{params.query}': {e}"
            )
            return None

    def get(self, params: AnimeParams) -> Optional[Anime]:
        """
        Retrieves detailed information and a list of episodes for a specific anime.

        Args:
            params: The parameters containing the anime ID (slug).

        Returns:
            An Anime object with a full episode list, or None.
        """
        try:
            # The numeric ID is the last part of the slug.
            clean_id_slug = params.id.split("?")[0]
            anime_id_numeric = clean_id_slug.split("-")[-1]
            if not anime_id_numeric.isdigit():
                raise ValueError("Could not extract numeric ID from anime slug.")

            # HiAnime loads episodes via an AJAX request.
            episodes_url = (
                f"{constants.HIANIME_AJAX_URL}/v2/episode/list/{anime_id_numeric}"
            )
            response = self.client.get(
                episodes_url,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": constants.AJAX_REFERER_HEADER,
                },
            )
            response.raise_for_status()

            # The response is JSON containing an 'html' key with the episode list.
            html_snippet = response.json().get("html", "")
            if not html_snippet:
                return None

            # We pass the original anime ID (slug) and the HTML snippet to the mapper.
            return mappers.map_to_anime_result(params.id, html_snippet)
        except Exception as e:
            logger.error(f"Failed to get anime details for '{params.id}': {e}")
            return None

    def episode_streams(
        self, params: EpisodeStreamsParams
    ) -> Optional[Iterator[Server]]:
        """
        Fetches the actual video stream URLs for a given episode.

        This is a multi-step process:
        1. Get the list of available servers (e.g., MegaCloud, StreamSB).
        2. For each server, get the embed URL.
        3. Pass the embed URL to an extractor to get the final stream URL.

        Args:
            params: The parameters containing the episode ID.

        Yields:
            A Server object for each available video source.
        """
        try:
            # The episode ID is in the format 'anime-slug?ep=12345'
            episode_id_numeric = params.episode.split("?ep=")[-1]
            if not episode_id_numeric.isdigit():
                raise ValueError("Could not extract numeric episode ID.")

            # 1. Get available servers for the episode.
            servers_url = f"{constants.HIANIME_AJAX_URL}/v2/episode/servers?episodeId={episode_id_numeric}"
            servers_response = self.client.get(
                servers_url,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": constants.AJAX_REFERER_HEADER,
                },
            )
            servers_response.raise_for_status()

            server_elements = get_elements_by_class(
                "server-item", servers_response.json().get("html", "")
            )

            for server_element in server_elements:
                try:
                    # 2. Extract the server's unique ID.
                    server_id = mappers.map_to_server_id(server_element)
                    if not server_id:
                        continue

                    # 3. Get the embed URL for this server.
                    sources_url = f"{constants.HIANIME_AJAX_URL}/v2/episode/sources?id={server_id}"
                    sources_response = self.client.get(
                        sources_url,
                        headers={
                            "X-Requested-With": "XMLHttpRequest",
                            "Referer": constants.AJAX_REFERER_HEADER,
                        },
                    )
                    sources_response.raise_for_status()

                    embed_url = sources_response.json().get("link")
                    if not embed_url:
                        continue

                    # 4. Use an extractor to get the final stream URLs from the embed page.
                    # The extractor handles the complex, host-specific logic.
                    server = extract_server(embed_url)
                    if server:
                        yield server
                except Exception as e:
                    logger.warning(
                        f"Failed to process a server for episode '{params.episode}': {e}"
                    )
                    continue
        except Exception as e:
            logger.error(f"Failed to get episode streams for '{params.episode}': {e}")
            return None
