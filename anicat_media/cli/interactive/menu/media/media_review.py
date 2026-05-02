from typing import Dict, List, Optional, Union

from .....libs.media_api.types import MediaReview
from ...session import Context, session
from ...state import InternalDirective, State


@session.menu
def media_review(ctx: Context, state: State) -> Union[State, InternalDirective]:
    """
    Fetches and displays a list of reviews for the user to select from.
    Shows the full review body upon selection or in the preview pane.
    """
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel

    feedback = ctx.feedback
    selector = ctx.selector
    console = Console()
    config = ctx.config
    media_item = state.media_api.media_item

    if not media_item:
        feedback.error("Media item is not in state.")
        return InternalDirective.BACK

    from .....libs.media_api.params import MediaReviewsParams

    loading_message = (
        f"Fetching reviews for {media_item.title.english or media_item.title.romaji}..."
    )
    reviews: Optional[List[MediaReview]] = None

    with feedback.progress(loading_message):
        reviews = ctx.media_api.get_reviews_for(
            MediaReviewsParams(id=media_item.id, per_page=15)
        )

    if not reviews:
        feedback.error("No reviews found for this anime.")
        return InternalDirective.BACK

    choice_map: Dict[str, MediaReview] = {
        f"By {review.user.name}: {(review.summary or 'No summary')[:80]}": review
        for review in reviews
    }
    choices = list(choice_map.keys()) + ["Back"]

    preview_command = None
    if config.general.preview != "none":
        from ....utils.preview import create_preview_context

        with create_preview_context() as preview_ctx:
            preview_command = preview_ctx.get_review_preview(choice_map, ctx.config)

    while True:
        chosen_title = selector.choose(
            prompt="Select a review to read",
            choices=choices,
            preview=preview_command,
        )

        if not chosen_title or chosen_title == "Back":
            return InternalDirective.BACK

        selected_review = choice_map[chosen_title]
        console.clear()

        reviewer_name = f"[bold magenta]{selected_review.user.name}[/bold magenta]"
        review_summary = (
            f"[italic green]'{selected_review.summary}'[/italic green]"
            if selected_review.summary
            else ""
        )
        panel_title = f"Review by {reviewer_name} - {review_summary}"
        review_body = Markdown(selected_review.body)

        console.print(
            Panel(review_body, title=panel_title, border_style="blue", expand=True)
        )
        selector.ask("\nPress Enter to return to the review list...")
