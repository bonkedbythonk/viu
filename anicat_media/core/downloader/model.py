"""Download result models for downloader implementations."""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class DownloadResult(BaseModel):
    """Result of a download operation."""

    success: bool = Field(description="Whether the download was successful")
    video_path: Optional[Path] = Field(
        default=None, description="Path to the downloaded video file"
    )
    subtitle_paths: list[Path] = Field(
        default_factory=list, description="Paths to downloaded subtitle files"
    )
    merged_path: Optional[Path] = Field(
        default=None,
        description="Path to the merged video+subtitles file if merge was performed",
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if download failed"
    )
    anime_title: str = Field(description="Title of the anime")
    episode_title: str = Field(description="Title of the episode")

    model_config = {"arbitrary_types_allowed": True}
