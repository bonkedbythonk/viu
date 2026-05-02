import re

YOUTUBE_REGEX = re.compile(
    r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+", re.IGNORECASE
)
TORRENT_REGEX = re.compile(
    r"^(?:(magnet:\?xt=urn:btih:(?:[a-zA-Z0-9]{32}|[a-zA-Z0-9]{40}).*)|(https?://.*\.torrent))$",
    re.IGNORECASE,
)
