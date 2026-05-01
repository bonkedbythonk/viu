import logging
import re
from typing import TYPE_CHECKING

import click

from ...core.config import AppConfig
from ...core.exceptions import ViuError

if TYPE_CHECKING:
    from ...libs.selectors.base import BaseSelector
    from ..service.feedback.service import FeedbackService

logger = logging.getLogger(__name__)


@click.command(
    help="Search and read manga from MangaKatana directly in your terminal.",
    short_help="Read manga",
    epilog="""
\\b
\\b\\bExamples:
  # Search for and read a manga
  viu manga

  # Search for a specific manga title
  viu manga --title "One Piece"

  # Use a specific manga provider
  viu manga --provider mangakatana
""",
)
@click.option(
    "--title",
    "-t",
    help="The manga title to search for.",
)
@click.option(
    "--provider",
    "-p",
    default="mangakatana",
    type=click.Choice(["mangakatana", "mangadex"]),
    help="The manga provider to use.",
)
@click.pass_obj
def manga(config: AppConfig, title: str, provider: str):
    from ..service.feedback.service import FeedbackService
    from ...libs.provider.manga.MangaProvider import MangaProvider as MangaProviderManager
    from ...libs.selectors.selector import create_selector

    feedback = FeedbackService(config)
    selector = create_selector(config)
    manga_provider = MangaProviderManager(provider=provider)

    if not title:
        title = selector.ask("Search for manga")
        if not title:
            raise ViuError("No title provided")

    # ---- search for manga ----
    feedback.info(f"[green bold]Searching for:[/] {title}")
    search_results = None
    with feedback.progress(f"Searching MangaKatana for '{title}'"):
        search_results = manga_provider.search_for_manga(title)

    if not search_results:
        raise ViuError("No results were found matching your query")

    # Build choice map
    result_map = {result["title"]: result for result in search_results}
    selected_title = selector.choose("Select Manga", list(result_map.keys()))
    if not selected_title:
        raise ViuError("No manga selected")

    selected_manga = result_map[selected_title]
    manga_url = selected_manga["url"]

    # ---- fetch manga details ----
    manga_info = None
    with feedback.progress(f"Fetching chapters for '{selected_title}'"):
        manga_info = manga_provider.get_manga(manga_url)

    if not manga_info or not manga_info.get("availableChapters"):
        raise ViuError(f"No chapters found for {selected_title}")

    chapters = manga_info["availableChapters"]
    feedback.info(
        f"[green bold]{selected_title}[/] — {len(chapters)} chapters available"
    )

    # ---- chapter selection loop ----
    _read_manga_loop(
        config, feedback, selector, manga_provider, manga_info, selected_title
    )


def _read_manga_loop(
    config: AppConfig,
    feedback: "FeedbackService",
    selector: "BaseSelector",
    manga_provider,
    manga_info: dict,
    manga_title: str,
):
    """Main reading loop: select chapter → read → optionally continue."""
    chapters = manga_info["availableChapters"]
    chapter_map = {ch["title"]: ch for ch in chapters}

    while True:
        selected_chapter_title = selector.choose(
            "Select Chapter", list(chapter_map.keys())
        )
        if not selected_chapter_title:
            break

        selected_chapter = chapter_map[selected_chapter_title]
        chapter_url = selected_chapter["url"]

        # ---- fetch chapter pages ----
        chapter_data = None
        with feedback.progress(f"Loading '{selected_chapter_title}'"):
            chapter_data = manga_provider.get_chapter_thumbnails(
                manga_info["id"], chapter_url
            )

        if not chapter_data or not chapter_data.get("thumbnails"):
            feedback.error(f"Failed to load pages for {selected_chapter_title}")
            continue

        thumbnails = chapter_data["thumbnails"]
        feedback.info(
            f"[green bold]Reading:[/] {manga_title} — {selected_chapter_title} "
            f"({len(thumbnails)} pages)"
        )

        # ---- display pages ----
        _display_manga_pages(config, thumbnails, f"{manga_title} — {selected_chapter_title}")

        # ---- AniList sync ----
        chapter_number = _extract_chapter_number(selected_chapter_title)
        if chapter_number is not None:
            _sync_anilist_progress(config, feedback, manga_title, chapter_number)

        # Ask to continue
        continue_reading = selector.choose(
            "What next?",
            ["Select another chapter", "Exit"],
        )
        if not continue_reading or continue_reading == "Exit":
            break


def _display_manga_pages(config: AppConfig, image_urls: list[str], window_title: str):
    """Display manga pages using the configured viewer."""
    viewer = config.general.manga_viewer

    if viewer == "icat":
        from ..utils.icat import icat_manga_viewer

        icat_manga_viewer(image_urls, window_title)
    elif viewer == "feh":
        from ..utils.feh import feh_manga_viewer

        feh_manga_viewer(image_urls, window_title)
    else:
        from ..utils.icat import icat_manga_viewer

        icat_manga_viewer(image_urls, window_title)


def _extract_chapter_number(chapter_title: str) -> int | None:
    """Extract the numeric chapter number from a chapter title string.

    Examples:
        "Chapter 103: v.3 c.Epilogue (end)" -> 103
        "Chapter 42: Fixed" -> 42
        "Chapter 31.5" -> 31
    """
    match = re.search(r"(?:chapter|ch\.?)\s*(\d+)", chapter_title, re.IGNORECASE)
    if match:
        return int(match.group(1))
    # Try plain number
    match = re.search(r"(\d+)", chapter_title)
    if match:
        return int(match.group(1))
    return None


def _sync_anilist_progress(
    config: AppConfig,
    feedback: "FeedbackService",
    manga_title: str,
    chapter_number: int,
):
    """Update AniList manga progress after reading a chapter."""
    try:
        import httpx

        from ...libs.media_api.api import create_api_client
        from ...libs.media_api.params import (
            MediaSearchParams,
            UpdateUserMediaListEntryParams,
        )
        from ...libs.media_api.types import MediaType, UserMediaListStatus
        from ..service.auth.service import AuthService

        media_api = create_api_client(config.general.media_api, config)

        # Authenticate
        auth = AuthService(config.general.media_api)
        token = auth.resolve_token()
        if not token:
            logger.debug("Not authenticated — skipping AniList sync")
            return

        try:
            profile = media_api.authenticate(token)
            if not profile:
                logger.debug("Auth failed — skipping AniList sync")
                return
        except httpx.ConnectError:
            logger.debug("Offline — skipping AniList sync")
            return

        # Search AniList for the manga
        search_params = MediaSearchParams(query=manga_title, type=MediaType.MANGA)
        result = media_api.search_media(search_params)

        if not result or not result.media:
            logger.debug(f"No AniList results for manga: {manga_title}")
            return

        # Use the first (best match) result
        anilist_manga = result.media[0]
        anilist_id = anilist_manga.id
        anilist_title = anilist_manga.title.english or anilist_manga.title.romaji or manga_title

        # Only update if the new chapter is ahead of current progress
        current_progress = 0
        if anilist_manga.user_status and anilist_manga.user_status.progress:
            current_progress = anilist_manga.user_status.progress

        if chapter_number <= current_progress:
            logger.debug(
                f"Chapter {chapter_number} <= current progress {current_progress}, skipping update"
            )
            return

        # Update progress
        success = media_api.update_list_entry(
            UpdateUserMediaListEntryParams(
                media_id=anilist_id,
                progress=str(chapter_number),
                status=UserMediaListStatus.WATCHING,
            )
        )

        if success:
            feedback.info(
                f"[cyan]AniList:[/] Updated [bold]{anilist_title}[/] progress to chapter {chapter_number}"
            )
        else:
            logger.warning(f"Failed to update AniList progress for {anilist_title}")

    except Exception as e:
        logger.warning(f"AniList sync error: {e}")
