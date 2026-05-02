from typing import Dict

from pydantic import BaseModel, Field

from ....libs.media_api.types import UserProfile

AUTH_VERSION = "1.0"


class AuthProfile(BaseModel):
    user_profile: UserProfile
    token: str


class AuthModel(BaseModel):
    version: str = Field(default=AUTH_VERSION)
    profiles: Dict[str, AuthProfile] = Field(default_factory=dict)
