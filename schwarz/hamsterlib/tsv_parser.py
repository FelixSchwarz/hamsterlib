import re
from collections.abc import Sequence
from datetime import datetime, timedelta
from io import StringIO
from typing import NamedTuple


class HamsterActivity(NamedTuple):
    activity: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    category: str | None
    description: str | None = None
    tags: str | None = None

    @classmethod
    def create(
        cls,
        activity: str,
        start_time: datetime,
        end_time: datetime | None = None,
        duration_minutes: int | None = None,
        category: str | None = None,
        description: str | None = None,
        tags: str | None = None,
    ) -> "HamsterActivity":
        if duration_minutes is None:
            if end_time is None:
                raise ValueError("Either end_time or duration_minutes must be provided.")
            duration_minutes = int((end_time - start_time).total_seconds() / 60)
        elif end_time is None:
            end_time = start_time + timedelta(minutes=duration_minutes)
        _hamster_activity = HamsterActivity(
            activity=activity,
            start_time=start_time,
            end_time=end_time,  # type: ignore[arg-type]
            category=category,
            description=description,
            tags=tags,
            duration_minutes=duration_minutes,
        )
        _validate_duration(_hamster_activity)
        return _hamster_activity

    @property
    def display_str(self) -> str:
        return self.activity

    @property
    def activities(self) -> tuple[str]:
        return (self.activity,)


def parse_hamster_tsv(tsv_fp: StringIO) -> Sequence[HamsterActivity]:
    lines = tsv_fp.readlines()
    if not lines:
        return []
    header = lines[0].strip().split("\t")
    entries = []
    for line in lines[1:]:
        if not line.strip():
            continue
        values = line.strip(" \n").split("\t")
        if len(values) != len(header):
            raise ValueError(f"damaged line: '{line}'")
        tsv_item = dict(zip(header, values))
        activity = HamsterActivity(
            activity=tsv_item["activity"],
            start_time=_parse_tsv_dt(tsv_item["start time"]),
            end_time=_parse_tsv_dt(tsv_item["end time"]),
            duration_minutes=_parse_minutes(tsv_item["duration minutes"]),
            category=tsv_item["category"] or None,
            description=tsv_item["description"] or None,
            tags=tsv_item["tags"] or None,
        )
        entries.append(activity)
    return entries


def _parse_tsv_dt(dt_str: str) -> datetime:
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")


RE_MINUTES = re.compile(r"^(\d+)\.0$")


def _parse_minutes(minutes_str: str) -> int:
    match = RE_MINUTES.match(minutes_str)
    if not match:
        raise ValueError(f"Invalid 'duration minutes': '{minutes_str}'")
    return int(match.group(1))


def _validate_duration(activity: HamsterActivity) -> None:
    expected_end_time = activity.start_time + timedelta(minutes=activity.duration_minutes)
    if activity.end_time != expected_end_time:
        _error = (
            f"'{activity.display_str}' has inconsistent end_time ({activity.end_time}) and "
            f"duration_minutes ({activity.duration_minutes}), expected end_time: {expected_end_time}."
        )
        raise ValueError(_error)
