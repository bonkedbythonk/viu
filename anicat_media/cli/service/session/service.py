import json
import logging
from datetime import datetime
from typing import List, Optional

from ....core.config.model import SessionsConfig
from ....core.utils.file import AtomicWriter
from ...interactive.state import State
from .model import Session

logger = logging.getLogger(__name__)


class SessionsService:
    def __init__(self, config: SessionsConfig):
        self.dir = config.dir
        self._ensure_sessions_directory()

    def save_session(
        self, history: List[State], name: Optional[str] = None, default=True
    ):
        if default:
            name = "default"
            session = Session(history=history, name=name)
        else:
            session = Session(history=history)
        self._save_session(session)

    def create_crash_backup(self, history: List[State], default=True):
        if default:
            self._save_session(
                Session(history=history, name="crash", is_from_crash=True)
            )
        else:
            self._save_session(Session(history=history, is_from_crash=True))

    def get_session_history(self, session_name: str) -> Optional[List[State]]:
        if session := self._load_session(session_name):
            return session.history

    def get_default_session_history(self) -> Optional[List[State]]:
        if history := self.get_session_history("default"):
            return history

    def get_most_recent_session_history(self) -> Optional[List[State]]:
        session_name: Optional[str] = None
        latest_timestamp: Optional[datetime] = None
        for session_file in self.dir.iterdir():
            try:
                _session_timestamp = session_file.stem.split("_")[1]

                session_timestamp = datetime.strptime(
                    _session_timestamp, "%Y%m%d_%H%M%S_%f"
                )
                if latest_timestamp is None or session_timestamp > latest_timestamp:
                    session_name = session_file.stem
                    latest_timestamp = session_timestamp

            except Exception as e:
                logger.error(f"{self.dir} is impure which caused: {e}")

        if session_name:
            return self.get_session_history(session_name)

    def _save_session(self, session: Session):
        path = self.dir / f"{session.name}.json"
        with AtomicWriter(path) as f:
            json.dump(session.model_dump(mode="json", by_alias=True), f)

    def _load_session(self, session_name: str) -> Optional[Session]:
        path = self.dir / f"{session_name}.json"
        if not path.exists():
            logger.warning(f"Session file not found: {path}")
            return None

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            session = Session.model_validate(data)

        logger.info(f"Session loaded from {path} with {session.state_count} states")
        return session

    def _ensure_sessions_directory(self):
        self.dir.mkdir(parents=True, exist_ok=True)
