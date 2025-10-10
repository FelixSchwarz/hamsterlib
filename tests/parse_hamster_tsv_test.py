from datetime import datetime
from io import StringIO
from typing import TYPE_CHECKING

import pytest

from schwarz.hamsterlib.activity_protocol import Activity
from schwarz.hamsterlib.tsv_parser import HamsterActivity, parse_hamster_tsv

_TSV_HEADER = "activity\tstart time\tend time\tduration minutes\tcategory\tdescription\ttags"


def test_parse_hamster_tsv():
    tsv_fp = _build_tsv_fp(
        ["Working\t2023-01-01 09:00\t2023-01-01 10:11\t71.0\tWork\tDescription 1\ttag1,tag2"]
    )
    activities = parse_hamster_tsv(tsv_fp)

    assert len(activities) == 1
    assert activities[0] == HamsterActivity(
        activity="Working",
        start_time=datetime(2023, 1, 1, 9, 0),
        end_time=datetime(2023, 1, 1, hour=10, minute=11),
        duration_minutes=71,
        category="Work",
        description="Description 1",
        tags="tag1,tag2",
    )


def _build_tsv_fp(tsv_lines: list[str]) -> StringIO:
    return StringIO("\n".join([_TSV_HEADER] + tsv_lines))


def test_hamster_activity_detects_wrong_duration():
    with pytest.raises(ValueError):
        HamsterActivity.create(
            activity="working",
            start_time=datetime(2025, 3, 14, hour=9),
            end_time=datetime(2025, 3, 14, hour=11),
            duration_minutes=100,
            category="work",
        )


# only detected by mypy, not ty 0.0.1-alpha21 (2025-10)
if TYPE_CHECKING:
    _: type[Activity] = HamsterActivity


def test_hamster_activity_implements_activity_protocol() -> None:
    _: Activity = HamsterActivity(
        activity="Working",
        start_time=datetime(2023, 1, 1, 9, 0),
        end_time=datetime(2023, 1, 1, 10, 11, 12),
        duration_minutes=71,
        category="Work",
        description="Description 1",
        tags="tag1,tag2",
    )
