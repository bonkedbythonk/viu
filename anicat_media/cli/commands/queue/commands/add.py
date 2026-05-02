import click
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


@click.command(name="add", help="Add episodes to the background download queue.")
@click.option("--title", "-t")
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
# Queue-specific options
@click.option(
    "--episode-range",
    "-r",
    required=True,
    help="Range of episodes to queue (e.g., '1-10', '5', '8:12').",
)
@click.option(
    "--yes",
    "-Y",
    is_flag=True,
    help="Queue for all found anime without prompting for selection.",
)
@click.pass_obj
def add(config: AppConfig, **options):
    from anicat_media.cli.service.download import DownloadService
    from anicat_media.cli.service.feedback import FeedbackService
    from anicat_media.cli.service.registry import MediaRegistryService
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
    download_service = DownloadService(config, registry, media_api, provider)

    try:
        # Build search params mirroring anilist download
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

        if options.get("yes"):
            anime_to_queue = search_result.media
        else:
            choice_map: dict[str, MediaItem] = {
                (item.title.english or item.title.romaji or f"ID: {item.id}"): item
                for item in search_result.media
            }
            preview_command = None
            if config.general.preview != "none":
                from anicat_media.cli.utils.preview import create_preview_context

                with create_preview_context() as preview_ctx:
                    preview_command = preview_ctx.get_anime_preview(
                        list(choice_map.values()),
                        list(choice_map.keys()),
                        config,
                    )
                    selected_titles = selector.choose_multiple(
                        "Select anime to queue",
                        list(choice_map.keys()),
                        preview=preview_command,
                    )
            else:
                selected_titles = selector.choose_multiple(
                    "Select anime to queue", list(choice_map.keys())
                )

            if not selected_titles:
                feedback.warning("No anime selected. Nothing queued.")
                return
            anime_to_queue = [choice_map[title] for title in selected_titles]

        episode_range_str = options.get("episode_range")
        total_queued = 0
        for media_item in anime_to_queue:
            # TODO: do a provider search here to determine episodes available maybe, or allow pasing of an episode list probably just change the format for parsing episodes
            available_episodes = [str(i + 1) for i in range(media_item.episodes or 0)]
            if not available_episodes:
                feedback.warning(
                    f"No episode information for '{media_item.title.english}', skipping."
                )
                continue

            try:
                episodes_to_queue = list(
                    parse_episode_range(episode_range_str, available_episodes)
                )
                if not episodes_to_queue:
                    feedback.warning(
                        f"Episode range '{episode_range_str}' resulted in no episodes for '{media_item.title.english}'."
                    )
                    continue

                queued_count = 0
                for ep in episodes_to_queue:
                    if download_service.add_to_queue(media_item, ep):
                        queued_count += 1

                total_queued += queued_count
                feedback.success(
                    f"Queued {queued_count} episodes for '{media_item.title.english}'."
                )
            except (ValueError, IndexError) as e:
                feedback.error(
                    f"Invalid episode range for '{media_item.title.english}': {e}"
                )

        feedback.success(
            f"Done. Total of {total_queued} episode(s) queued across all selections."
        )

    except AnicatError as e:
        feedback.error("Queue add failed", str(e))
    except Exception as e:
        feedback.error("An unexpected error occurred", str(e))
