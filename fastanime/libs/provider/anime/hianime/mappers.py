import re
from typing import List, Optional

from ....provider.anime.types import (
    Anime,
    AnimeEpisodes,
    PageInfo,
    SearchResult,
    SearchResults,
)
from ....provider.scraping.html_parser import (
    extract_attributes,
    get_element_by_class,
    get_elements_by_class,
)


def _parse_episodes(element_html: str) -> AnimeEpisodes:
    """Helper function to parse sub/dub episode counts from an anime item."""
    sub_text = get_element_by_class("tick-sub", element_html)
    dub_text = get_element_by_class("tick-dub", element_html)

    sub_count = 0
    dub_count = 0

    if sub_text:
        match = re.search(r"\d+", sub_text)
        if match:
            sub_count = int(match.group(0))

    if dub_text:
        match = re.search(r"\d+", dub_text)
        if match:
            dub_count = int(match.group(0))

    # Generate a list of episode numbers as strings
    sub_list = [str(i) for i in range(1, sub_count + 1)]
    dub_list = [str(i) for i in range(1, dub_count + 1)]

    return AnimeEpisodes(sub=sub_list, dub=dub_list, raw=[])


def map_to_search_results(
    anime_elements: List[str], full_html: str
) -> Optional[SearchResults]:
    """
    Maps a list of HTML elements from a HiAnime search page to a generic SearchResults object.

    Args:
        anime_elements: A list of raw HTML strings, each representing an anime (.flw-item).
        full_html: The full HTML content of the search page for parsing pagination.

    Returns:
        A SearchResults object or None if parsing fails.
    """
    results = []
    for element in anime_elements:
        title_element = get_element_by_class("dynamic-name", element)
        if not title_element:
            continue

        attrs = extract_attributes(title_element)
        title = title_element.split(">")[1].split("<")[0].strip()
        anime_id = attrs.get("href", "").lstrip("/")

        poster_element = get_element_by_class("film-poster-img", element)
        poster_attrs = extract_attributes(poster_element or "")

        results.append(
            SearchResult(
                id=anime_id,
                title=title,
                poster=poster_attrs.get("data-src"),
                episodes=_parse_episodes(element),
            )
        )

    # Parse pagination to determine total pages
    total_pages = 1
    # Use a simpler selector that is less prone to parsing issues.
    pagination_elements = get_elements_by_class("page-item", full_html)
    if pagination_elements:
        # Find the last page number from all pagination links
        last_page_num = 0
        for el in pagination_elements:
            attrs = extract_attributes(el)
            href = attrs.get("href", "")
            if "?page=" in href:
                try:
                    num = int(href.split("?page=")[-1])
                    if num > last_page_num:
                        last_page_num = num
                except (ValueError, IndexError):
                    continue
        if last_page_num > 0:
            total_pages = last_page_num
    page_info = PageInfo(total=total_pages)
    return SearchResults(page_info=page_info, results=results)


def map_to_anime_result(anime_id_slug: str, episode_list_html: str) -> Optional[Anime]:
    """
    Maps the AJAX response for an episode list to a generic Anime object.

    Args:
        anime_id_slug: The anime's unique ID string (e.g., "steinsgate-3").
        episode_list_html: The raw HTML snippet containing the list of episodes.

    Returns:
        An Anime object containing the episode list, or None.
    """
    episodes = get_elements_by_class("ssl-item", episode_list_html)

    episode_numbers_sub = []
    # Note: HiAnime's episode list doesn't differentiate sub/dub, so we assume all are sub for now.
    # The user selects sub/dub when choosing a server later.
    for ep_element in episodes:
        attrs = extract_attributes(ep_element)
        ep_num = attrs.get("data-number")
        if ep_num:
            episode_numbers_sub.append(ep_num)

    # The title isn't in this AJAX response, so we derive a placeholder from the slug.
    # The application's state usually carries the real title from the search/list step.
    placeholder_title = anime_id_slug.replace("-", " ").title()

    return Anime(
        id=anime_id_slug,
        title=placeholder_title,
        episodes=AnimeEpisodes(
            sub=episode_numbers_sub,
            dub=[],  # We don't know dub count from this endpoint
            raw=[],
        ),
    )


def map_to_server_id(server_element_html: str) -> Optional[str]:
    """
    Extracts the server's unique data-id from its HTML element.

    Args:
        server_element_html: The raw HTML of a server-item.

    Returns:
        The server ID string, or None.
    """
    attrs = extract_attributes(server_element_html)
    return attrs.get("data-id")
