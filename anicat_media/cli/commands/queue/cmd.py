import click

from ...utils.lazyloader import LazyGroup

commands = {
    "add": "add.add",
    "list": "list.list_cmd",
    "resume": "resume.resume",
    "clear": "clear.clear_cmd",
}


@click.group(
    cls=LazyGroup,
    name="queue",
    root="anicat_media.cli.commands.queue.commands",
    invoke_without_command=False,
    help="Manage the download queue (add, list, resume, clear).",
    short_help="Manage the download queue.",
    lazy_subcommands=commands,
)
@click.pass_context
def queue(ctx: click.Context):
    """Queue management root command."""
    # No-op root; subcommands are lazy-loaded
    pass
