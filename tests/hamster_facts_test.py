from datetime import datetime

import pytest

from schwarz.hamsterlib.hamsterdb import HamsterFacts
from schwarz.hamsterlib.models import Activity, Category, Fact
from schwarz.hamsterlib.tsv_parser import HamsterActivity


@pytest.fixture
def work_category() -> Category:
    return Category(name="Work")


@pytest.fixture
def coding_work(work_category) -> Activity:
    return Activity(name="Coding", category=work_category)


def test_hamsterfacts_contain_activity(coding_work):
    hamster_activity = HamsterActivity(
        start_time=datetime(2024, 6, 1, hour=9, minute=0),
        end_time=datetime(2024, 6, 1, hour=11, minute=0),
        duration_minutes=120,
        category=coding_work.category.name,
        activity=coding_work.name,
    )
    fact1 = Fact(
        start_time=datetime(2024, 5, 1, hour=9, minute=0),
        end_time=datetime(2024, 5, 1, hour=11, minute=0),
        activity=coding_work,
    )
    # overlapping activity but not exactly the same
    fact2 = Fact(
        start_time=datetime(2024, 6, 1, hour=9, minute=30),
        end_time=datetime(2024, 6, 1, hour=12, minute=15),
        activity=coding_work,
    )
    fact3 = Fact(
        start_time=datetime(2024, 6, 1, hour=12, minute=0),
        end_time=datetime(2024, 6, 1, hour=13, minute=0),
        activity=coding_work,
    )

    hamster_facts = HamsterFacts(facts=[fact1, fact2, fact3])
    assert hamster_activity not in hamster_facts

    fact4 = Fact(
        start_time=hamster_activity.start_time,
        end_time=hamster_activity.end_time,
        activity=coding_work,
    )
    # fact4 overlaps with fact2 but that should be ok for this test
    hamster_facts = HamsterFacts(facts=[fact1, fact2, fact3, fact4])
    assert hamster_activity in hamster_facts
