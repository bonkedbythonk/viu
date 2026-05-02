from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field

from ...interactive.state import State


class Session(BaseModel):
    history: List[State]

    created_at: datetime = Field(default_factory=datetime.now)
    name: str = Field(
        default_factory=lambda: "session_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    )
    description: Optional[str] = None
    is_from_crash: bool = False

    @computed_field
    @property
    def state_count(self) -> int:
        return len(self.history)
