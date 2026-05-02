import click
from anicat_media.core.config import AppConfig


@click.command(
    name="clear",
    help="Clear queued items from the registry (QUEUED -> NOT_DOWNLOADED).",
)
@click.option("--force", is_flag=True, help="Do not prompt for confirmation.")
@click.pass_obj
def clear_cmd(config: AppConfig, force: bool):
    from anicat_media.cli.service.feedback import FeedbackService
    from anicat_media.cli.service.registry import MediaRegistryService
    from anicat_media.cli.service.registry.models import DownloadStatus

    feedback = FeedbackService(config)
    registry = MediaRegistryService(config.general.media_api, config.media_registry)

    if not force and not click.confirm("This will clear all queued items. Continue?"):
        feedback.info("Aborted.")
        return

    cleared = 0
    queued = registry.get_episodes_by_download_status(DownloadStatus.QUEUED)
    for media_id, ep in queued:
        ok = registry.update_episode_download_status(
            media_id=media_id,
            episode_number=ep,
            status=DownloadStatus.NOT_DOWNLOADED,
        )
        if ok:
            cleared += 1
    feedback.success(f"Cleared {cleared} queued episode(s).")
