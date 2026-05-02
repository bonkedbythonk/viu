import click

from ....core.config.model import AppConfig
from ...utils.lazyloader import LazyGroup
from . import examples

commands = {
    "sync": "sync.sync",
    "stats": "stats.stats",
    "search": "search.search",
    "export": "export.export",
    "import": "import_.import_",
    "clean": "clean.clean",
    "backup": "backup.backup",
    "restore": "restore.restore",
}


@click.group(
    cls=LazyGroup,
    name="registry",
    root="anicat_media.cli.commands.registry.commands",
    invoke_without_command=True,
    help="Manage your local media registry - sync, search, backup and maintain your anime database",
    short_help="Local media registry management",
    lazy_subcommands=commands,
    epilog=examples.main,
)
@click.option(
    "--api",
    default="anilist",
    help="Media API to use (default: anilist)",
    type=click.Choice(["anilist"], case_sensitive=False),
)
@click.pass_context
def registry(ctx: click.Context, api: str):
    """
    The entry point for the 'registry' command. If no subcommand is invoked,
    it shows registry information and statistics.
    """
    from ...service.feedback import FeedbackService
    from ...service.registry import MediaRegistryService

    config: AppConfig = ctx.obj
    feedback = FeedbackService(config)

    if ctx.invoked_subcommand is None:
        # Show registry overview and statistics
        try:
            registry_service = MediaRegistryService(api, config.media_registry)
            stats = registry_service.get_registry_stats()

            feedback.info("Registry Overview", f"API: {api}")
            feedback.info("Total Media", f"{stats.get('total_media', 0)} entries")
            feedback.info(
                "Recently Updated",
                f"{stats.get('recently_updated', 0)} entries in last 7 days",
            )
            feedback.info("Storage Path", str(config.media_registry.media_dir))

            # Show status breakdown if available
            status_breakdown = stats.get("status_breakdown", {})
            if status_breakdown:
                feedback.info("Status Breakdown:")
                for status, count in status_breakdown.items():
                    feedback.info(f"  {status}", f"{count} entries")

        except Exception as e:
            feedback.error("Registry Error", f"Failed to load registry: {e}")
