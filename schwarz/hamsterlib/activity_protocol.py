from datetime import datetime
from typing import Protocol


class Activity(Protocol):
    @property
    def activities(self) -> tuple[str, ...]: ...

    @property
    def start_time(self) -> datetime: ...

    @property
    def end_time(self) -> datetime: ...

    @property
    def duration_minutes(self) -> int: ...

    @property
    def category(self) -> str | None: ...

    @property
    def display_str(self) -> str: ...
