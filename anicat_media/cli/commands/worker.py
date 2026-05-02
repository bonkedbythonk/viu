import click
from anicat_media.core.config import AppConfig


@click.command(help="Run the background worker for notifications and downloads.")
@click.pass_obj
def worker(config: AppConfig):
    """
    Starts the long-running background worker process.
    This process will periodically check for AniList notifications and
    process any queued downloads. It's recommended to run this in the
    background (e.g., 'anicat worker &') or as a system service.
    """
    from anicat_media.cli.service.auth import AuthService
    from anicat_media.cli.service.download.service import DownloadService
    from anicat_media.cli.service.feedback import FeedbackService
    from anicat_media.cli.service.notification.service import NotificationService
    from anicat_media.cli.service.registry.service import MediaRegistryService
    from anicat_media.cli.service.worker.service import BackgroundWorkerService
    from anicat_media.libs.media_api.api import create_api_client
    from anicat_media.libs.provider.anime.provider import create_provider

    feedback = FeedbackService(config)
    if not config.worker.enabled:
        feedback.warning("Worker is disabled in the configuration. Exiting.")
        return

    # Instantiate services
    media_api = create_api_client(config.general.media_api, config)
    # Authenticate if credentials exist (enables notifications)
    auth = AuthService(config.general.media_api)
    token = auth.resolve_token()
    if token:
        try:
            media_api.authenticate(token)
        except Exception:
            pass
    provider = create_provider(config.general.provider)
    registry = MediaRegistryService(config.general.media_api, config.media_registry)

    notification_service = NotificationService(config, media_api, registry)
    download_service = DownloadService(config, registry, media_api, provider)
    worker_service = BackgroundWorkerService(
        config.worker, notification_service, download_service
    )

    feedback.info("Starting background worker...", "Press Ctrl+C to stop.")
    worker_service.run()
