import logging
import signal
import threading
import time
from typing import Optional

from anicat_media.cli.service.download.service import DownloadService
from anicat_media.cli.service.notification.service import NotificationService
from anicat_media.core.config.model import WorkerConfig

logger = logging.getLogger(__name__)


class BackgroundWorkerService:
    def __init__(
        self,
        config: WorkerConfig,
        notification_service: NotificationService,
        download_service: DownloadService,
    ):
        self.config = config
        self.notification_service = notification_service
        self.download_service = download_service
        self._stop_event = threading.Event()
        self._signals_installed = False

    def _install_signal_handlers(self):
        """Install SIGINT/SIGTERM handlers to allow graceful shutdown when run in foreground."""
        if self._signals_installed:
            return

        def _handler(signum, frame):  # noqa: ARG001 (signature fixed by signal)
            logger.info(
                "Received signal %s, shutting down background worker...", signum
            )
            self.stop()

        try:
            signal.signal(signal.SIGINT, _handler)
            signal.signal(signal.SIGTERM, _handler)
            self._signals_installed = True
        except Exception:
            # Signal handling may fail in non-main threads or certain environments
            logger.debug(
                "Signal handlers not installed (non-main thread or unsupported environment)."
            )

    def run(self):
        """Run the background loop until stopped.

        Responsibilities:
        - Periodically check AniList notifications (if authenticated & plyer available)
        - Periodically resume/process unfinished downloads
        - Keep CPU usage low using an event-based wait
        - Gracefully terminate on KeyboardInterrupt/SIGTERM
        """
        logger.info("Background worker starting...")

        # Convert configured minutes to seconds
        notification_interval_sec = max(
            60, self.config.notification_check_interval * 60
        )
        download_interval_sec = max(60, self.config.download_check_interval * 60)
        download_retry_interval_sec = max(
            60, self.config.download_check_failed_interval * 60
        )

        # Start download worker and attempt resuming pending jobs once at startup
        self.download_service.start()

        # Schedule the very first execution immediately
        next_notification_ts: Optional[float] = 0.0
        next_download_ts: Optional[float] = 0.0
        next_retry_download_ts: Optional[float] = 0.0

        # Install signal handlers if possible
        self._install_signal_handlers()

        try:
            while not self._stop_event.is_set():
                now = time.time()

                # Check for notifications
                if next_notification_ts is not None and now >= next_notification_ts:
                    try:
                        logger.info("Checking for notifications...")
                        self.notification_service.check_and_display_notifications()
                    except Exception:
                        logger.exception("Error during notification check")
                    finally:
                        next_notification_ts = now + notification_interval_sec

                # Process download queue
                if next_download_ts is not None and now >= next_download_ts:
                    try:
                        self.download_service.resume_unfinished_downloads()
                    except Exception:
                        logger.exception("Error during download queue processing")
                    finally:
                        next_download_ts = now + download_interval_sec

                if next_retry_download_ts is not None and now >= next_retry_download_ts:
                    try:
                        self.download_service.retry_failed_downloads()
                    except Exception:
                        logger.exception(
                            "Error during failed download queue processing"
                        )
                    finally:
                        next_retry_download_ts = now + download_retry_interval_sec
                # Determine how long to wait until the next scheduled task
                next_events = [
                    t
                    for t in (
                        next_notification_ts,
                        next_download_ts,
                        next_retry_download_ts,
                    )
                    if t is not None
                ]
                if next_events:
                    time_until_next = max(0.0, min(next_events) - time.time())
                else:
                    time_until_next = 30.0

                # Cap wait to react reasonably fast to stop requests
                wait_time = min(time_until_next, 30.0)
                self._stop_event.wait(timeout=wait_time)

        except KeyboardInterrupt:
            logger.info("Background worker interrupted by user. Stopping...")
            self.stop()
        finally:
            # Ensure we always stop the download worker
            try:
                self.download_service.stop()
            except Exception:
                logger.exception("Failed to stop download service cleanly")
            logger.info("Background worker stopped.")

    def stop(self):
        if not self._stop_event.is_set():
            logger.info("Background worker shutting down...")
            self._stop_event.set()
