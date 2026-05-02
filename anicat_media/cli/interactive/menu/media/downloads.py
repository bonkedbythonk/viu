import logging
import random
from typing import Callable, Dict

from .....libs.media_api.params import MediaSearchParams
from .....libs.media_api.types import (
    MediaSort,
    MediaStatus,
    UserMediaListStatus,
)
from ...session import Context, session
from ...state import InternalDirective, MediaApiState, MenuName, State

logger = logging.getLogger(__name__)
MenuAction = Callable[[], State | InternalDirective]


@session.menu
def downloads(ctx: Context, state: State) -> State | InternalDirective:
    """Downloads menu showing locally stored media from registry."""
    icons = ctx.config.general.icons
    feedback = ctx.feedback
    feedback.clear_console()

    options: Dict[str, MenuAction] = {
        f"{'🔥 ' if icons else ''}Trending (Local)": _create_local_media_list_action(
            ctx, state, MediaSort.TRENDING_DESC
        ),
        f"{'🎞️ ' if icons else ''}Recent (Local)": _create_local_recent_media_action(
            ctx, state
        ),
        f"{'📺 ' if icons else ''}Watching (Local)": _create_local_status_action(
            ctx, state, UserMediaListStatus.WATCHING
        ),
        f"{'🔁 ' if icons else ''}Rewatching (Local)": _create_local_status_action(
            ctx, state, UserMediaListStatus.REPEATING
        ),
        f"{'⏸️ ' if icons else ''}Paused (Local)": _create_local_status_action(
            ctx, state, UserMediaListStatus.PAUSED
        ),
        f"{'📑 ' if icons else ''}Planned (Local)": _create_local_status_action(
            ctx, state, UserMediaListStatus.PLANNING
        ),
        f"{'🔎 ' if icons else ''}Search (Local)": _create_local_search_media_list(
            ctx, state
        ),
        f"{'🔔 ' if icons else ''}Recently Updated (Local)": _create_local_media_list_action(
            ctx, state, MediaSort.UPDATED_AT_DESC
        ),
        f"{'✨ ' if icons else ''}Popular (Local)": _create_local_media_list_action(
            ctx, state, MediaSort.POPULARITY_DESC
        ),
        f"{'💯 ' if icons else ''}Top Scored (Local)": _create_local_media_list_action(
            ctx, state, MediaSort.SCORE_DESC
        ),
        f"{'💖 ' if icons else ''}Favourites (Local)": _create_local_media_list_action(
            ctx, state, MediaSort.FAVOURITES_DESC
        ),
        f"{'🎲 ' if icons else ''}Random (Local)": _create_local_random_media_list(
            ctx, state
        ),
        f"{'🎬 ' if icons else ''}Upcoming (Local)": _create_local_media_list_action(
            ctx, state, MediaSort.POPULARITY_DESC, MediaStatus.NOT_YET_RELEASED
        ),
        f"{'✅ ' if icons else ''}Completed (Local)": _create_local_status_action(
            ctx, state, UserMediaListStatus.COMPLETED
        ),
        f"{'🚮 ' if icons else ''}Dropped (Local)": _create_local_status_action(
            ctx, state, UserMediaListStatus.DROPPED
        ),
        f"{'↩️ ' if icons else ''}Back to Main": lambda: InternalDirective.BACK,
        f"{'❌ ' if icons else ''}Exit": lambda: InternalDirective.EXIT,
    }

    choice = ctx.selector.choose(
        prompt="Select Downloads Category",
        choices=list(options.keys()),
    )
    if not choice:
        return InternalDirective.RELOAD

    selected_action = options[choice]
    next_step = selected_action()
    return next_step


def _create_local_media_list_action(
    ctx: Context, state: State, sort: MediaSort, status: MediaStatus | None = None
) -> MenuAction:
    """Create action for searching local media with sorting and optional status filter."""

    def action():
        feedback = ctx.feedback
        search_params = MediaSearchParams(sort=sort, status=status)

        loading_message = "Searching local media registry"
        result = None
        with feedback.progress(loading_message):
            result = ctx.media_registry.search_for_media(search_params)

        if result and result.media:
            return State(
                menu_name=MenuName.RESULTS,
                media_api=MediaApiState(
                    search_result={
                        media_item.id: media_item for media_item in result.media
                    },
                    search_params=search_params,
                    page_info=result.page_info,
                ),
            )
        else:
            feedback.info("No media found in local registry")
            return InternalDirective.RELOAD

    return action


def _create_local_random_media_list(ctx: Context, state: State) -> MenuAction:
    """Create action for getting random local media."""

    def action():
        feedback = ctx.feedback

        loading_message = "Getting random local media"
        with feedback.progress(loading_message):
            # Get all records and pick random ones
            all_records = list(ctx.media_registry.get_all_media_records())

        if not all_records:
            feedback.info("No media found in local registry")
            return InternalDirective.BACK

        # Get up to 50 random records
        random_records = random.sample(all_records, min(50, len(all_records)))
        random_ids = [record.media_item.id for record in random_records]

        search_params = MediaSearchParams(id_in=random_ids)
        result = ctx.media_registry.search_for_media(search_params)

        if result and result.media:
            return State(
                menu_name=MenuName.RESULTS,
                media_api=MediaApiState(
                    search_result={
                        media_item.id: media_item for media_item in result.media
                    },
                    search_params=search_params,
                    page_info=result.page_info,
                ),
            )
        else:
            feedback.info("No media found in local registry")
            return InternalDirective.RELOAD

    return action


def _create_local_search_media_list(ctx: Context, state: State) -> MenuAction:
    """Create action for searching local media by query."""

    def action():
        feedback = ctx.feedback

        query = ctx.selector.ask("Search Local Anime")
        if not query:
            return InternalDirective.BACK

        search_params = MediaSearchParams(query=query)

        loading_message = "Searching local media registry"
        result = None
        with feedback.progress(loading_message):
            result = ctx.media_registry.search_for_media(search_params)

        if result and result.media:
            return State(
                menu_name=MenuName.RESULTS,
                media_api=MediaApiState(
                    search_result={
                        media_item.id: media_item for media_item in result.media
                    },
                    search_params=search_params,
                    page_info=result.page_info,
                ),
            )
        else:
            feedback.info("No media found in local registry")
            return InternalDirective.RELOAD

    return action


def _create_local_status_action(
    ctx: Context, state: State, status: UserMediaListStatus
) -> MenuAction:
    """Create action for getting local media by user status."""

    def action():
        feedback = ctx.feedback

        loading_message = f"Getting {status.value} media from local registry"
        result = None
        with feedback.progress(loading_message):
            result = ctx.media_registry.get_media_by_status(status)

        if result and result.media:
            return State(
                menu_name=MenuName.RESULTS,
                media_api=MediaApiState(
                    search_result={
                        media_item.id: media_item for media_item in result.media
                    },
                    page_info=result.page_info,
                ),
            )
        else:
            feedback.info(f"No {status.value} media found in local registry")
            return InternalDirective.RELOAD

    return action


def _create_local_recent_media_action(ctx: Context, state: State) -> MenuAction:
    """Create action for getting recently watched local media."""

    def action():
        result = ctx.media_registry.get_recently_watched()
        if result and result.media:
            return State(
                menu_name=MenuName.RESULTS,
                media_api=MediaApiState(
                    search_result={
                        media_item.id: media_item for media_item in result.media
                    },
                    page_info=result.page_info,
                ),
            )
        else:
            ctx.feedback.info("No recently watched media found in local registry")
            return InternalDirective.RELOAD

    return action
