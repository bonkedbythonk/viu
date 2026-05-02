from typing import Dict, Optional, Union

from .....libs.media_api.types import AiringScheduleItem, AiringScheduleResult
from ...session import Context, session
from ...state import InternalDirective, State


@session.menu
def media_airing_schedule(
    ctx: Context, state: State
) -> Union[State, InternalDirective]:
    """
    Fetches and displays the airing schedule for an anime.
    Shows upcoming episodes with air dates and countdown timers.
    """
    from rich.console import Console
    from rich.panel import Panel

    feedback = ctx.feedback
    selector = ctx.selector
    console = Console()
    media_item = state.media_api.media_item

    if not media_item:
        feedback.error("Media item is not in state.")
        return InternalDirective.BACK

    from .....libs.media_api.params import MediaAiringScheduleParams

    loading_message = f"Fetching airing schedule for {media_item.title.english or media_item.title.romaji}..."
    schedule_result: Optional[AiringScheduleResult] = None

    with feedback.progress(loading_message):
        schedule_result = ctx.media_api.get_airing_schedule_for(
            MediaAiringScheduleParams(id=media_item.id)
        )

    if not schedule_result or not schedule_result.schedule_items:
        feedback.warning(
            "No airing schedule found",
            "This anime doesn't have upcoming episodes or airing data",
        )
        return InternalDirective.BACK

    # Create choices for each episode in the schedule
    choice_map: Dict[str, AiringScheduleItem] = {}
    for item in schedule_result.schedule_items:
        display_name = f"Episode {item.episode}"
        if item.airing_at:
            airing_time = item.airing_at
            display_name += f" - {airing_time.strftime('%Y-%m-%d %H:%M')}"
        if item.time_until_airing:
            display_name += f" (in {item.time_until_airing})"

        choice_map[display_name] = item

    choices = list(choice_map.keys()) + ["View Full Schedule", "Back"]

    preview_command = None
    if ctx.config.general.preview != "none":
        from ....utils.preview import create_preview_context

        anime_title = media_item.title.english or media_item.title.romaji or "Unknown"
        with create_preview_context() as preview_ctx:
            preview_command = preview_ctx.get_airing_schedule_preview(
                schedule_result, ctx.config, anime_title
            )

    while True:
        chosen_title = selector.choose(
            prompt="Select an episode or view full schedule",
            choices=choices,
            preview=preview_command,
        )

        if not chosen_title or chosen_title == "Back":
            return InternalDirective.BACK

        if chosen_title == "View Full Schedule":
            console.clear()
            # Display airing schedule
            anime_title = (
                media_item.title.english or media_item.title.romaji or "Unknown"
            )
            _display_airing_schedule(console, schedule_result, anime_title)
            selector.ask("\nPress Enter to return...")
            continue

        # Show individual episode details
        selected_item = choice_map[chosen_title]
        console.clear()

        episode_info = []
        episode_info.append(f"[bold cyan]Episode {selected_item.episode}[/bold cyan]")

        if selected_item.airing_at:
            airing_time = selected_item.airing_at
            episode_info.append(
                f"[green]Airs at:[/green] {airing_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        if selected_item.time_until_airing:
            episode_info.append(
                f"[yellow]Time until airing:[/yellow] {selected_item.time_until_airing}"
            )

        episode_content = "\n".join(episode_info)

        console.print(
            Panel(
                episode_content,
                title=f"Episode Details - {media_item.title.english or media_item.title.romaji}",
                border_style="blue",
                expand=True,
            )
        )

        selector.ask("\nPress Enter to return to the schedule list...")

    return InternalDirective.BACK


def _display_airing_schedule(
    console, schedule_result: AiringScheduleResult, anime_title: str
):
    """Display the airing schedule in a formatted table."""
    from datetime import datetime
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    # Create title
    title = Text(f"Airing Schedule for {anime_title}", style="bold cyan")

    # Create table for episodes
    table = Table(show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Episode", style="cyan", justify="center", min_width=8)
    table.add_column("Air Date", style="green", min_width=20)
    table.add_column("Time Until Airing", style="yellow", min_width=15)
    table.add_column("Status", style="white", min_width=10)

    # Sort episodes by episode number
    sorted_episodes = sorted(schedule_result.schedule_items, key=lambda x: x.episode)

    for episode in sorted_episodes[:15]:  # Show next 15 episodes
        ep_num = str(episode.episode)

        # Format air date
        if episode.airing_at:
            formatted_date = episode.airing_at.strftime("%Y-%m-%d %H:%M")

            # Check if episode has already aired
            now = datetime.now()
            if episode.airing_at < now:
                status = "[dim]Aired[/dim]"
            else:
                status = "[green]Upcoming[/green]"
        else:
            formatted_date = "[dim]Unknown[/dim]"
            status = "[dim]TBA[/dim]"

        # Format time until airing
        if episode.time_until_airing and episode.time_until_airing > 0:
            time_until = episode.time_until_airing
            days = time_until // 86400
            hours = (time_until % 86400) // 3600
            minutes = (time_until % 3600) // 60

            if days > 0:
                time_str = f"{days}d {hours}h"
            elif hours > 0:
                time_str = f"{hours}h {minutes}m"
            else:
                time_str = f"{minutes}m"
        elif episode.airing_at and episode.airing_at < datetime.now():
            time_str = "[dim]Aired[/dim]"
        else:
            time_str = "[dim]Unknown[/dim]"

        table.add_row(ep_num, formatted_date, time_str, status)

    # Display in a panel
    panel = Panel(table, title=title, border_style="blue", expand=True)
    console.print(panel)

    # Add summary information
    total_episodes = len(schedule_result.schedule_items)
    upcoming_episodes = sum(
        1
        for ep in schedule_result.schedule_items
        if ep.airing_at and ep.airing_at > datetime.now()
    )

    summary_text = Text()
    summary_text.append("Total episodes in schedule: ", style="bold")
    summary_text.append(f"{total_episodes}", style="cyan")
    summary_text.append("\nUpcoming episodes: ", style="bold")
    summary_text.append(f"{upcoming_episodes}", style="green")

    summary_panel = Panel(
        summary_text,
        title="[bold]Summary[/bold]",
        border_style="yellow",
        expand=False,
    )
    console.print()
    console.print(summary_panel)
