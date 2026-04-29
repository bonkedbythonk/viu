from typing import List, Literal, TypedDict


class HiAnimeEpisode(TypedDict):
    """
    Represents a single episode entry returned by the
    `/ajax/v2/episode/list/{anime_id}` endpoint.
    """

    title: str | None
    episodeId: str | None
    number: int
    isFiller: bool


class HiAnimeEpisodeServer(TypedDict):
    """
    Represents a single server entry returned by the
    `/ajax/v2/episode/servers?episodeId={episode_id}` endpoint.
    """

    serverName: str
    serverId: int | None


class HiAnimeSource(TypedDict):
    """
    Represents the JSON response from the
    `/ajax/v2/episode/sources?id={server_id}` endpoint,
    which contains the link to the extractor's embed page.
    """

    link: str
