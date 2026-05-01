import re
from typing import Dict, Optional, Union

from .....libs.media_api.types import Character, CharacterSearchResult
from ...session import Context, session
from ...state import InternalDirective, State


@session.menu
def media_characters(ctx: Context, state: State) -> Union[State, InternalDirective]:
    """
    Fetches and displays a list of characters for the user to select from.
    Shows character details upon selection or in the preview pane.
    """
    from rich.console import Console

    feedback = ctx.feedback
    selector = ctx.selector
    console = Console()
    config = ctx.config
    media_item = state.media_api.media_item

    if not media_item:
        feedback.error("Media item is not in state.")
        return InternalDirective.BACK

    from .....libs.media_api.params import MediaCharactersParams

    loading_message = f"Fetching characters for {media_item.title.english or media_item.title.romaji}..."
    characters_result: Optional[CharacterSearchResult] = None

    with feedback.progress(loading_message):
        characters_result = ctx.media_api.get_characters_of(
            MediaCharactersParams(id=media_item.id, type=media_item.type)
        )

    if not characters_result or not characters_result.characters:
        feedback.error("No characters found for this anime.")
        return InternalDirective.BACK

    characters = characters_result.characters
    choice_map: Dict[str, Character] = {}

    # Create display names for characters
    for character in characters:
        display_name = character.name.full or character.name.first or "Unknown"
        if character.gender:
            display_name += f" ({character.gender})"
        if character.age:
            display_name += f" - Age {character.age}"

        choice_map[display_name] = character

    choices = list(choice_map.keys()) + ["Back"]

    preview_command = None
    if config.general.preview != "none":
        from ....utils.preview import create_preview_context

        with create_preview_context() as preview_ctx:
            preview_command = preview_ctx.get_character_preview(choice_map, ctx.config)

    while True:
        chosen_title = selector.choose(
            prompt="Select a character to view details",
            choices=choices,
            preview=preview_command,
        )

        if not chosen_title or chosen_title == "Back":
            return InternalDirective.BACK

        selected_character = choice_map[chosen_title]
        console.clear()

        # Display character details
        anime_title = media_item.title.english or media_item.title.romaji or "Unknown"
        _display_character_details(console, selected_character, anime_title)

        selector.ask("\nPress Enter to return to the character list...")


def _display_character_details(console, character: Character, anime_title: str):
    """Display detailed character information in a formatted panel."""
    from rich.columns import Columns
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    # Character name panel
    name_text = Text()
    if character.name.full:
        name_text.append(character.name.full, style="bold cyan")
    elif character.name.first:
        full_name = character.name.first
        if character.name.last:
            full_name += f" {character.name.last}"
        name_text.append(full_name, style="bold cyan")
    else:
        name_text.append("Unknown Character", style="bold dim")

    if character.name.native:
        name_text.append(f"\n{character.name.native}", style="green")

    name_panel = Panel(
        name_text,
        title=f"[bold]Character from {anime_title}[/bold]",
        border_style="cyan",
        expand=False,
    )

    # Basic info table
    info_table = Table(show_header=False, box=None, padding=(0, 1))
    info_table.add_column("Field", style="bold yellow", min_width=12)
    info_table.add_column("Value", style="white")

    if character.gender:
        info_table.add_row("Gender", character.gender)
    if character.age:
        info_table.add_row("Age", str(character.age))
    if character.blood_type:
        info_table.add_row("Blood Type", character.blood_type)
    if character.favourites:
        info_table.add_row("Favorites", f"{character.favourites:,}")
    if character.date_of_birth:
        birth_date = character.date_of_birth.strftime("%B %d, %Y")
        info_table.add_row("Birthday", birth_date)

    info_panel = Panel(
        info_table,
        title="[bold]Basic Information[/bold]",
        border_style="blue",
    )

    # Description panel
    description = character.description or "No description available"
    # Clean HTML tags from description
    clean_description = re.sub(r"<[^>]+>", "", description)
    # Replace common HTML entities
    clean_description = (
        clean_description.replace("&quot;", '"')
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#039;", "'")
        .replace("&nbsp;", " ")
    )
    # Limit length for display
    if len(clean_description) > 500:
        clean_description = clean_description[:497] + "..."

    description_panel = Panel(
        Text(clean_description, style="white"),
        title="[bold]Description[/bold]",
        border_style="green",
    )

    # Display everything
    console.print(name_panel)
    console.print()

    # Show panels side by side if there's basic info
    if info_table.rows:
        console.print(Columns([info_panel, description_panel], equal=True, expand=True))
    else:
        console.print(description_panel)
