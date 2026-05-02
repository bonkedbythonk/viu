import click
from anicat_media.core.config import AppConfig


@click.command(name="list", help="List items in the download queue and their statuses.")
@click.option(
    "--status",
    type=click.Choice(["queued", "downloading", "completed", "failed", "paused"]),
)
@click.option("--detailed", is_flag=True)
@click.pass_obj
def list_cmd(config: AppConfig, status: str | None, detailed: bool | None):
    from anicat_media.cli.service.feedback import FeedbackService
    from anicat_media.cli.service.registry import MediaRegistryService
    from anicat_media.cli.service.registry.models import DownloadStatus

    feedback = FeedbackService(config)
    registry = MediaRegistryService(config.general.media_api, config.media_registry)

    status_map = {
        "queued": DownloadStatus.QUEUED,
        "downloading": DownloadStatus.DOWNLOADING,
        "completed": DownloadStatus.COMPLETED,
        "failed": DownloadStatus.FAILED,
        "paused": DownloadStatus.PAUSED,
    }

    # TODO: improve this by modifying the download_status function or create new function
    if detailed and status:
        target = status_map[status]
        episodes = registry.get_episodes_by_download_status(target)
        feedback.info(f"{len(episodes)} episode(s) with status {status}.")
        for media_id, ep in episodes:
            record = registry.get_media_record(media_id)
            if record:
                feedback.info(f"{record.media_item.title.english} episode {ep}")
        return

    if status:
        target = status_map[status]
        episodes = registry.get_episodes_by_download_status(target)
        feedback.info(f"{len(episodes)} episode(s) with status {status}.")
        for media_id, ep in episodes:
            feedback.info(f"- media:{media_id} episode:{ep}")
    else:
        from rich.console import Console
        from rich.table import Table

        stats = registry.get_download_statistics()
        table = Table(title="Queue Status")
        table.add_column("Metric")
        table.add_column("Value")
        table.add_row("Queued", str(stats.get("queued", 0)))
        table.add_row("Downloading", str(stats.get("downloading", 0)))
        table.add_row("Completed", str(stats.get("downloaded", 0)))
        table.add_row("Failed", str(stats.get("failed", 0)))
        table.add_row("Paused", str(stats.get("paused", 0)))

        console = Console()
        console.print(table)
