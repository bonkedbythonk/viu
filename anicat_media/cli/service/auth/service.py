import json
import logging
import os
import tomllib
from pathlib import Path
from typing import Optional

from ....core.constants import APP_DATA_DIR
from ....core.utils.file import AtomicWriter, FileLock
from ....libs.media_api.types import UserProfile
from .model import AuthModel, AuthProfile

logger = logging.getLogger(__name__)

AUTH_FILE = APP_DATA_DIR / "auth.json"

# Secondary config location following XDG conventions
_XDG_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
_XDG_TOKEN_FILE = _XDG_CONFIG_HOME / "anicat" / "token.txt"
_XDG_CONFIG_FILE = _XDG_CONFIG_HOME / "anicat" / "config.toml"


class AuthService:
    def __init__(self, media_api: str):
        self.path = AUTH_FILE
        self.media_api = media_api
        _lock_file = APP_DATA_DIR / "auth.lock"
        self._lock = FileLock(_lock_file)

    def resolve_token(self, explicit_token: str | None = None) -> str | None:
        """
        Resolve an AniList token from multiple sources in priority order.

        Priority:
            1. Explicit token (CLI flag / positional argument / direct string)
            2. $ANILIST_TOKEN environment variable
            3. Dedicated token file (~/.config/anicat/token.txt or APP_DATA_DIR/token.txt)
            4. Config file ('token' or 'access_token' key under [anilist] in config.toml)
            5. Saved auth.json from a previous successful login

        Args:
            explicit_token: A token string or path to a token file passed directly
                            by the user (e.g., via --token flag or positional argument).

        Returns:
            The resolved token string, or None if no token was found.
        """
        # 1. Explicit token (CLI flag / argument / direct call)
        if explicit_token:
            token = self._read_token_from_path_or_string(explicit_token)
            if token:
                logger.debug("Token resolved from explicit input.")
                return token

        # 2. Environment variable
        env_token = os.environ.get("ANILIST_TOKEN", "").strip()
        if env_token:
            logger.debug("Token resolved from $ANILIST_TOKEN environment variable.")
            return env_token

        # 3. Dedicated token file (check XDG path first, then APP_DATA_DIR)
        for token_path in (_XDG_TOKEN_FILE, APP_DATA_DIR / "token.txt"):
            if token_path.is_file():
                try:
                    token = token_path.read_text(encoding="utf-8").strip()
                    if token:
                        logger.debug(f"Token resolved from file: {token_path}")
                        return token
                except Exception as e:
                    logger.warning(f"Failed to read token file {token_path}: {e}")

        # 4. Config file (check for 'token' or 'access_token' under [anilist])
        for config_path in (_XDG_CONFIG_FILE, APP_DATA_DIR / "config.toml"):
            if config_path.is_file():
                try:
                    with config_path.open("rb") as f:
                        data = tomllib.load(f)
                    anilist_section = data.get("anilist", {})
                    for key in ("token", "access_token"):
                        val = anilist_section.get(key, "")
                        if isinstance(val, str) and val.strip():
                            logger.debug(
                                f"Token resolved from config key '{key}' in {config_path}"
                            )
                            return val.strip()
                except Exception as e:
                    logger.warning(f"Failed to read config file {config_path}: {e}")

        # 5. Already-saved auth.json
        auth_profile = self.get_auth()
        if auth_profile and auth_profile.token:
            logger.debug("Token resolved from saved auth.json.")
            return auth_profile.token

        logger.debug("No token found in any source.")
        return None

    @staticmethod
    def _read_token_from_path_or_string(value: str) -> str | None:
        """
        Interpret a value as either a file path (reading its contents) or a raw token string.

        Args:
            value: A string that is either a file path or a raw token.

        Returns:
            The token string, or None if the file was empty or unreadable.
        """
        path = Path(value)
        if path.is_file():
            try:
                token = path.read_text(encoding="utf-8").strip()
                if token:
                    return token
                logger.warning(f"Token file is empty: {path}")
                return None
            except Exception as e:
                logger.warning(f"Error reading token from file {path}: {e}")
                return None
        return value.strip() if value.strip() else None

    def get_auth(self) -> Optional[AuthProfile]:
        auth = self._load_auth()
        return auth.profiles.get(self.media_api)

    def save_user_profile(self, profile: UserProfile, token: str) -> None:
        auth = self._load_auth()
        auth.profiles[self.media_api] = AuthProfile(user_profile=profile, token=token)
        self._save_auth(auth)
        logger.info(f"Successfully saved user credentials to {self.path}")

    def clear_user_profile(self) -> None:
        """Deletes the user credentials file."""
        if self.path.exists():
            self.path.unlink()
            logger.info("Cleared user credentials.")

    def _load_auth(self) -> AuthModel:
        if not self.path.exists():
            self._auth = AuthModel()
            self._save_auth(self._auth)
            return self._auth

        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            self._auth = AuthModel.model_validate(data)
            return self._auth

    def _save_auth(self, auth: AuthModel):
        with self._lock:
            with AtomicWriter(self.path) as f:
                json.dump(auth.model_dump(), f, indent=2)
            logger.info(f"Successfully saved user credentials to {self.path}")

