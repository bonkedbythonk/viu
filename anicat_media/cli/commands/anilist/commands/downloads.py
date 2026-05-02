import json

import click

from .....core.config import AppConfig
from .....libs.media_api.params import MediaSearchParams
from .....libs.media_api.types import (
    MediaFormat,
    MediaGenre,
    MediaSort,
    UserMediaListStatus,
)
from ....service.feedback import FeedbackService
from ....service.registry.service import MediaRegistryService


@click.command(help="Search through the local media registry")
@click.argument("query", required=False)
@click.option(
    "--status",
    type=click.Choice(
        [s.value for s in UserMediaListStatus],
        case_sensitive=False,
    ),
    help="Filter by watch status",
)
@click.option(
    "--genre", multiple=True, help="Filter by genre (can be used multiple times)"
)
@click.option(
    "--format",
    type=click.Choice(
        [
            f.value
            for f in MediaFormat
            if f not in [MediaFormat.MANGA, MediaFormat.NOVEL, MediaFormat.ONE_SHOT]
        ],
        case_sensitive=False,
    ),
    help="Filter by format",
)
@click.option("--year", type=int, help="Filter by release year")
@click.option("--min-score", type=float, help="Minimum average score (0.0 - 10.0)")
@click.option("--max-score", type=float, help="Maximum average score (0.0 - 10.0)")
@click.option(
    "--sort",
    type=click.Choice(
        ["title", "score", "popularity", "year", "episodes", "updated"],
        case_sensitive=False,
    ),
    default="title",
    help="Sort results by field",
)
@click.option("--limit", type=int, default=20, help="Maximum number of results to show")
@click.option(
    "--json", "output_json", is_flag=True, help="Output results in JSON format"
)
@click.option(
    "--api",
    default="anilist",
    type=click.Choice(["anilist"], case_sensitive=False),
    help="Media API registry to search",
)
@click.pass_obj
def downloads(
    config: AppConfig,
    query: str | None,
    status: str | None,
    genre: tuple[str, ...],
    format: str | None,
    year: int | None,
    min_score: float | None,
    max_score: float | None,
    sort: str,
    limit: int,
    output_json: bool,
    api: str,
):
    """
    Search through your local media registry.

    You can search by title and filter by various criteria like status,
    genre, format, year, and score range.
    """
    feedback = FeedbackService(config)
    if not has_user_input(click.get_current_context()):
        from ....interactive.session import session
        from ....interactive.state import MediaApiState, MenuName, State

        # Create initial state with search results
        initial_state = [State(menu_name=MenuName.DOWNLOADS)]

        session.load_menus_from_folder("media")
        session.run(config, history=initial_state)

    registry_service = MediaRegistryService(api, config.media_registry)

    search_params = _build_search_params(
        query, status, genre, format, year, min_score, max_score, sort, limit
    )

    with feedback.progress("Searching local registry..."):
        result = registry_service.search_for_media(search_params)

    if not result or not result.media:
        feedback.info("No Results", "No media found matching your criteria")
        return

    if output_json:
        print(json.dumps(result.model_dump(mode="json"), indent=2))
        return

    from ....interactive.session import session
    from ....interactive.state import MediaApiState, MenuName, State

    feedback.info(
        f"Found {len(result.media)} anime matching your search. Launching interactive mode..."
    )

    # Create initial state with search results
    initial_state = [
        State(menu_name=MenuName.DOWNLOADS),
        State(
            menu_name=MenuName.RESULTS,
            media_api=MediaApiState(
                search_result={
                    media_item.id: media_item for media_item in result.media
                },
                search_params=search_params,
                page_info=result.page_info,
            ),
        ),
    ]

    session.load_menus_from_folder("media")
    session.run(config, history=initial_state)


def _build_search_params(
    query: str | None,
    status: str | None,
    genre: tuple[str, ...],
    format_str: str | None,
    year: int | None,
    min_score: float | None,
    max_score: float | None,
    sort: str,
    limit: int,
) -> MediaSearchParams:
    """Build MediaSearchParams from command options for local filtering."""
    sort_map = {
        "title": MediaSort.TITLE_ROMAJI,
        "score": MediaSort.SCORE_DESC,
        "popularity": MediaSort.POPULARITY_DESC,
        "year": MediaSort.START_DATE_DESC,
        "episodes": MediaSort.EPISODES_DESC,
        "updated": MediaSort.UPDATED_AT_DESC,
    }

    # Safely convert strings to enums
    format_enum = next(
        (f for f in MediaFormat if f.value.lower() == (format_str or "").lower()), None
    )
    genre_enums = [
        g for g_str in genre for g in MediaGenre if g.value.lower() == g_str.lower()
    ]

    # Note: Local search handles status separately as it's part of the index, not MediaItem

    return MediaSearchParams(
        query=query,
        per_page=limit,
        sort=[sort_map.get(sort.lower(), MediaSort.TITLE_ROMAJI)],
        averageScore_greater=int(min_score * 10) if min_score is not None else None,
        averageScore_lesser=int(max_score * 10) if max_score is not None else None,
        genre_in=genre_enums or None,
        format_in=[format_enum] if format_enum else None,
        seasonYear=year,
    )


def has_user_input(ctx: click.Context) -> bool:
    """
    Checks if any command-line options or arguments were provided by the user
    by comparing the given values to their default values.

    This handles all parameter types including flags, multiple options,
    and arguments with no default.
    """
    import sys

    if len(sys.argv) > 3:
        return True
    else:
        return False
    for param in ctx.command.params:
        # Get the value for the parameter from the context.
        # This will be the user-provided value or the default.
        value = ctx.params.get(param.name)

        # We need to explicitly check if a value was provided by the user.
        # The simplest way to do this is to compare it to its default.
        if value != param.default:
            # If the value is different from the default, the user
            # must have provided it.
            return True

    # If the loop completes without finding any non-default values,
    # then no user input was given.
    return False
