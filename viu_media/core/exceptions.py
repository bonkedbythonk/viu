class ViuError(Exception):
    """
    Base exception for all custom errors raised by the Viu library and application.

    Catching this exception will catch any error originating from within this project,
    distinguishing it from built-in Python errors or third-party library errors.
    """

    pass


# ==============================================================================
# Configuration and Initialization Errors
# ==============================================================================


class ConfigError(ViuError):
    """
    Represents an error found in the user's configuration file (config.ini).

    This is typically raised by the ConfigLoader when validation fails.
    """

    pass


class AuthenticationError(ViuError):
    """
    Raised when no valid AniList token can be resolved from any source.

    Provides clear, actionable remediation instructions to the user.
    """

    def __init__(self, reason: str = ""):
        lines = [
            reason or "No AniList token found.",
            "",
            "To authenticate, provide your token using one of these methods (in priority order):",
            "  1. CLI flag:     viu anilist auth --token <your_token>",
            "  2. CLI argument: viu anilist auth /path/to/token.txt",
            "  3. Env var:      export ANILIST_TOKEN='<your_token>'",
            "  4. Token file:   Save your token to ~/.config/viu/token.txt",
            "  5. Config file:  Add 'token = \"<your_token>\"' under [anilist] in config.toml",
            "",
            "To obtain a token, visit:",
            "  https://anilist.co/api/v2/oauth/authorize?client_id=20148&response_type=token",
        ]
        super().__init__("\n".join(lines))


class DependencyNotFoundError(ViuError):
    """
    A required external command-line tool (e.g., ffmpeg, fzf) was not found.

    This indicates a problem with the user's environment setup.
    """

    def __init__(self, dependency_name: str, hint: str | None = None):
        self.dependency_name = dependency_name
        message = (
            f"Required dependency '{dependency_name}' not found in your system's PATH."
        )
        if hint:
            message += f"\nHint: {hint}"
        super().__init__(message)


# ==============================================================================
# Provider and Network Errors
# ==============================================================================


class ProviderError(ViuError):
    """
    Base class for all errors related to an anime provider.

    This allows for catching any provider-related issue while still allowing
    for more specific error handling of its subclasses.
    """

    def __init__(self, provider_name: str, message: str):
        self.provider_name = provider_name
        super().__init__(f"[{provider_name.capitalize()}] {message}")


class ProviderAPIError(ProviderError):
    """
    An error occurred while communicating with the provider's API.

    This typically corresponds to network issues, timeouts, or HTTP error
    status codes like 4xx (client error) or 5xx (server error).
    """

    def __init__(
        self, provider_name: str, http_status: int | None = None, details: str = ""
    ):
        self.http_status = http_status
        message = "An API communication error occurred."
        if http_status:
            message += f" (Status: {http_status})"
        if details:
            message += f" Details: {details}"
        super().__init__(provider_name, message)


class ProviderParsingError(ProviderError):
    """
    Failed to parse or find expected data in the provider's response.

    This often indicates that the source website's HTML structure or API
    response schema has changed, and the provider's parser needs to be updated.
    """

    pass


# ==============================================================================
# Application Logic and Workflow Errors
# ==============================================================================


class DownloaderError(ViuError):
    """
    An error occurred during the file download or post-processing phase.

    This can be raised by the YTDLPService for issues like failed downloads
    or ffmpeg merging errors.
    """

    pass


class InvalidEpisodeRangeError(ViuError, ValueError):
    """
    The user-provided episode range string is malformed or invalid.

    Inherits from ValueError for semantic compatibility but allows for specific
    catching as a ViuError.
    """

    pass


class NoStreamsFoundError(ProviderError):
    """
    A provider was successfully queried, but no streamable links were returned.
    """

    def __init__(self, provider_name: str, anime_title: str, episode: str):
        message = f"No streams were found for '{anime_title}' episode {episode}."
        super().__init__(provider_name, message)
