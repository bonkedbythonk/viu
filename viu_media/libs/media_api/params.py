from dataclasses import dataclass
from typing import List, Optional, Union

from .types import (
    MediaFormat,
    MediaGenre,
    MediaSeason,
    MediaSort,
    MediaStatus,
    MediaTag,
    MediaType,
    UserMediaListSort,
    UserMediaListStatus,
)


@dataclass(frozen=True)
class MediaSearchParams:
    query: Optional[str] = None
    page: int = 1
    per_page: Optional[int] = None
    sort: Optional[Union[MediaSort, List[MediaSort]]] = None

    # IDs
    id_in: Optional[List[int]] = None

    # Genres
    genre_in: Optional[List[MediaGenre]] = None
    genre_not_in: Optional[List[MediaGenre]] = None

    # Tags
    tag_in: Optional[List[MediaTag]] = None
    tag_not_in: Optional[List[MediaTag]] = None

    # Status
    status_in: Optional[List[MediaStatus]] = None  # Corresponds to [MediaStatus]
    status: Optional[MediaStatus] = None  # Corresponds to MediaStatus
    status_not_in: Optional[List[MediaStatus]] = None  # Corresponds to [MediaStatus]

    # Popularity
    popularity_greater: Optional[int] = None
    popularity_lesser: Optional[int] = None

    # Average Score
    averageScore_greater: Optional[int] = None
    averageScore_lesser: Optional[int] = None

    # Season and Year
    seasonYear: Optional[int] = None
    season: Optional[MediaSeason] = None

    # Start Date (FuzzyDateInt is often an integer representation like YYYYMMDD)
    startDate_greater: Optional[int] = None
    startDate_lesser: Optional[int] = None
    startDate: Optional[int] = None

    # End Date (FuzzyDateInt)
    endDate_greater: Optional[int] = None
    endDate_lesser: Optional[int] = None

    # Format and Type
    format_in: Optional[List[MediaFormat]] = None
    type: Optional[MediaType] = None

    # On List
    on_list: Optional[bool] = None


@dataclass(frozen=True)
class UserMediaListSearchParams:
    status: UserMediaListStatus
    page: int = 1
    type: Optional[MediaType] = None
    sort: Optional[UserMediaListSort] = None
    per_page: Optional[int] = None


@dataclass(frozen=True)
class UpdateUserMediaListEntryParams:
    media_id: int
    status: Optional[UserMediaListStatus] = None
    progress: Optional[str] = None
    score: Optional[float] = None


@dataclass(frozen=True)
class MediaRecommendationParams:
    id: int
    page: Optional[int] = 1
    per_page: Optional[int] = None


@dataclass(frozen=True)
class MediaCharactersParams:
    id: int
    type: Optional[MediaType] = None


@dataclass(frozen=True)
class MediaRelationsParams:
    id: int
    # page: Optional[int] = 1
    # per_page: Optional[int] = None


@dataclass(frozen=True)
class MediaAiringScheduleParams:
    id: int


@dataclass(frozen=True)
class MediaReviewsParams:
    id: int
    page: int = 1
    per_page: Optional[int] = None
