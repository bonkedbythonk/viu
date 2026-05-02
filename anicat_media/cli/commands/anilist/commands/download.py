from typing import TYPE_CHECKING, Dict, List

import click
from anicat_media.cli.utils.completion import anime_titles_shell_complete
from anicat_media.core.config import AppConfig
from anicat_media.core.exceptions import AnicatError
from anicat_media.libs.media_api.types import (
    MediaFormat,
    MediaGenre,
    MediaItem,
    MediaSeason,
    MediaSort,
    MediaStatus,
    MediaTag,
    MediaType,
    MediaYear,
)

from .. import examples

if TYPE_CHECKING:
    from typing import TypedDict

    from typing_extensions import Unpack

    class DownloadOptions(TypedDict, total=False):
        title: str | None
        episode_range: str | None
        page: int
        per_page: int | None
        season: str | None
        status: tuple[str, ...]
        status_not: tuple[str, ...]
        sort: str | None
        genres: tuple[str, ...]
        genres_not: tuple[str, ...]
        tags: tuple[str, ...]
        tags_not: tuple[str, ...]
        media_format: tuple[str, ...]
        media_type: str | None
        year: str | None
        popularity_greater: int | None
        popularity_lesser: int | None
        score_greater: int | None
        score_lesser: int | None
        start_date_greater: int | None
        start_date_lesser: int | None
        end_date_greater: int | None
        end_date_lesser: int | None
        on_list: bool | None
        yes: bool


@click.command(
    help="Search for anime on AniList and download episodes.",
    short_help="Search and download anime.",
    epilog=examples.download,
)
# --- Re-using all search options ---
@click.option("--title", "-t", shell_complete=anime_titles_shell_complete)
@click.option("--page", "-p", type=click.IntRange(min=1), default=1)
@click.option("--per-page", type=click.IntRange(min=1, max=50))
@click.option("--season", type=click.Choice([s.value for s in MediaSeason]))
@click.option(
    "--status", "-S", multiple=True, type=click.Choice([s.value for s in MediaStatus])
)
@click.option(
    "--status-not", multiple=True, type=click.Choice([s.value for s in MediaStatus])
)
@click.option("--sort", "-s", type=click.Choice([s.value for s in MediaSort]))
@click.option(
    "--genres", "-g", multiple=True, type=click.Choice([g.value for g in MediaGenre])
)
@click.option(
    "--genres-not", multiple=True, type=click.Choice([g.value for g in MediaGenre])
)
@click.option(
    "--tags", "-T", multiple=True, type=click.Choice([t.value for t in MediaTag])
)
@click.option(
    "--tags-not", multiple=True, type=click.Choice([t.value for t in MediaTag])
)
@click.option(
    "--media-format",
    "-f",
    multiple=True,
    type=click.Choice([f.value for f in MediaFormat]),
)
@click.option("--media-type", type=click.Choice([t.value for t in MediaType]))
@click.option("--year", "-y", type=click.Choice([y.value for y in MediaYear]))
@click.option("--popularity-greater", type=click.IntRange(min=0))
@click.option("--popularity-lesser", type=click.IntRange(min=0))
@click.option("--score-greater", type=click.IntRange(min=0, max=100))
@click.option("--score-lesser", type=click.IntRange(min=0, max=100))
@click.option("--start-date-greater", type=int)
@click.option("--start-date-lesser", type=int)
@click.option("--end-date-greater", type=int)
@click.option("--end-date-lesser", type=int)
@click.option("--on-list/--not-on-list", "-L/-no-L", type=bool, default=None)
# --- Download specific options ---
@click.option(
    "--episode-range",
    "-r",
    help="Range of episodes to download (e.g., '1-10', '5', '8:12'). Required.",
    required=True,
)
@click.option(
    "--yes",
    "-Y",
    is_flag=True,
    help="Automatically download from all found anime without prompting for selection.",
)
@click.pass_obj
def download(config: AppConfig, **options: "Unpack[DownloadOptions]"):
    from anicat_media.cli.service.download.service import DownloadService
    from anicat_media.cli.service.feedback import FeedbackService
    from anicat_media.cli.service.registry import MediaRegistryService
    from anicat_media.cli.service.watch_history import WatchHistoryService
    from anicat_media.cli.utils.parser import parse_episode_range
    from anicat_media.libs.media_api.api import create_api_client
    from anicat_media.libs.media_api.params import MediaSearchParams
    from anicat_media.libs.provider.anime.provider import create_provider
    from anicat_media.libs.selectors import create_selector
    from rich.progress import Progress

    feedback = FeedbackService(config)
    selector = create_selector(config)
    media_api = create_api_client(config.general.media_api, config)
    provider = create_provider(config.general.provider)
    registry = MediaRegistryService(config.general.media_api, config.media_registry)
    watch_history = WatchHistoryService(config, registry, media_api)
    download_service = DownloadService(config, registry, media_api, provider)

    try:
        sort_val = options.get("sort")
        status_val = options.get("status")
        status_not_val = options.get("status_not")
        genres_val = options.get("genres")
        genres_not_val = options.get("genres_not")
        tags_val = options.get("tags")
        tags_not_val = options.get("tags_not")
        media_format_val = options.get("media_format")
        media_type_val = options.get("media_type")
        season_val = options.get("season")
        year_val = options.get("year")

        search_params = MediaSearchParams(
            query=options.get("title"),
            page=options.get("page", 1),
            per_page=options.get("per_page"),
            sort=MediaSort(sort_val) if sort_val else None,
            status_in=[MediaStatus(s) for s in status_val] if status_val else None,
            status_not_in=[MediaStatus(s) for s in status_not_val]
            if status_not_val
            else None,
            genre_in=[MediaGenre(g) for g in genres_val] if genres_val else None,
            genre_not_in=[MediaGenre(g) for g in genres_not_val]
            if genres_not_val
            else None,
            tag_in=[MediaTag(t) for t in tags_val] if tags_val else None,
            tag_not_in=[MediaTag(t) for t in tags_not_val] if tags_not_val else None,
            format_in=[MediaFormat(f) for f in media_format_val]
            if media_format_val
            else None,
            type=MediaType(media_type_val) if media_type_val else None,
            season=MediaSeason(season_val) if season_val else None,
            seasonYear=int(year_val) if year_val else None,
            popularity_greater=options.get("popularity_greater"),
            popularity_lesser=options.get("popularity_lesser"),
            averageScore_greater=options.get("score_greater"),
            averageScore_lesser=options.get("score_lesser"),
            startDate_greater=options.get("start_date_greater"),
            startDate_lesser=options.get("start_date_lesser"),
            endDate_greater=options.get("end_date_greater"),
            endDate_lesser=options.get("end_date_lesser"),
            on_list=options.get("on_list"),
        )

        with Progress() as progress:
            progress.add_task("Searching AniList...", total=None)
            search_result = media_api.search_media(search_params)

        if not search_result or not search_result.media:
            raise AnicatError("No anime found matching your search criteria.")

        anime_to_download: List[MediaItem]
        if options.get("yes"):
            anime_to_download = search_result.media
        else:
            choice_map: Dict[str, MediaItem] = {
                (item.title.english or item.title.romaji or f"ID: {item.id}"): item
                for item in search_result.media
            }
            preview_command = None
            if config.general.preview != "none":
                from ....utils.preview import create_preview_context

                with create_preview_context() as preview_ctx:
                    preview_command = preview_ctx.get_anime_preview(
                        list(choice_map.values()),
                        list(choice_map.keys()),
                        config,
                    )
                    selected_titles = selector.choose_multiple(
                        "Select anime to download",
                        list(choice_map.keys()),
                        preview=preview_command,
                    )
            else:
                selected_titles = selector.choose_multiple(
                    "Select anime to download",
                    list(choice_map.keys()),
                )
            if not selected_titles:
                feedback.warning("No anime selected. Aborting download.")
                return
            anime_to_download = [choice_map[title] for title in selected_titles]

        total_downloaded = 0
        episode_range_str = options.get("episode_range")
        if not episode_range_str:
            raise AnicatError("--episode-range is required.")

        for media_item in anime_to_download:
            watch_history.add_media_to_list_if_not_present(media_item)

            available_episodes = [str(i + 1) for i in range(media_item.episodes or 0)]
            if not available_episodes:
                feedback.warning(
                    f"No episode information for '{media_item.title.english}', skipping."
                )
                continue

            try:
                episodes_to_download = list(
                    parse_episode_range(episode_range_str, available_episodes)
                )
                if not episodes_to_download:
                    feedback.warning(
                        f"Episode range '{episode_range_str}' resulted in no episodes for '{media_item.title.english}'."
                    )
                    continue

                feedback.info(
                    f"Preparing to download {len(episodes_to_download)} episodes for '{media_item.title.english}'."
                )
                download_service.download_episodes_sync(
                    media_item, episodes_to_download
                )
                total_downloaded += len(episodes_to_download)

            except (ValueError, IndexError) as e:
                feedback.error(
                    f"Invalid episode range for '{media_item.title.english}': {e}"
                )
                continue

        feedback.success(
            f"Finished. Successfully downloaded a total of {total_downloaded} episodes."
        )

    except AnicatError as e:
        feedback.error("Download command failed", str(e))
    except Exception as e:
        feedback.error("An unexpected error occurred", str(e))
