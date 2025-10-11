from datetime import datetime, timedelta

import pytest

from schwarz.hamsterlib.db_utils import setup_db
from schwarz.hamsterlib.hamsterdb import HamsterDB
from schwarz.hamsterlib.high_level_api import compare_activities
from schwarz.hamsterlib.models import Activity, Category, Fact
from schwarz.hamsterlib.tsv_parser import HamsterActivity


@pytest.fixture
def session():
    db_url = "sqlite:///:memory:"
    session = setup_db(db_url, enable_foreign_keys=True, create_tables=True)
    try:
        yield session
    finally:
        session.close()


def test_compare_activities_empty_hamster(session, coding_work_activity):
    hamster_db = HamsterDB(session)
    result = compare_activities([], hamster_db)
    assert result.new_activities == []
    assert result.existing == []

    result = compare_activities([coding_work_activity], hamster_db)
    assert result.new_activities == [coding_work_activity]
    assert result.existing == []
    assert result.conflicts == []


@pytest.fixture
def db_category_work(session) -> Category:
    category = Category(name="work")
    session.add(category)
    return category


@pytest.fixture
def db_coding_work(db_category_work, session) -> Activity:
    activity = Activity(name="coding", category=db_category_work)
    session.add(activity)
    return activity


@pytest.fixture
def db_meeting_work(db_category_work, session) -> Activity:
    activity = Activity(name="meeting", category=db_category_work)
    session.add(activity)
    return activity


@pytest.fixture
def coding_work_activity(db_coding_work) -> HamsterActivity:
    return HamsterActivity(
        start_time=datetime(2024, 6, 1, hour=9, minute=0),
        end_time=datetime(2024, 6, 1, hour=11, minute=0),
        duration_minutes=120,
        activity=db_coding_work.name,
        category=db_coding_work.category.name,
    )


@pytest.fixture
def meeting_work_activity(db_meeting_work) -> HamsterActivity:
    return HamsterActivity(
        start_time=datetime(2024, 6, 1, hour=13, minute=0),
        end_time=datetime(2024, 6, 1, hour=14, minute=0),
        duration_minutes=60,
        activity=db_meeting_work.name,
        category=db_meeting_work.category.name,
    )


def test_compare_activities(coding_work_activity, db_coding_work, meeting_work_activity, session):
    session.flush()
    _fact_from_activity(coding_work_activity, session=session)
    meeting_fact = _fact_from_activity(meeting_work_activity, session=session)
    session.commit()
    # overlaps with `meeting_work_activity` but different activity and category
    sleep_activity = HamsterActivity(
        start_time=meeting_work_activity.start_time + timedelta(minutes=20),
        end_time=meeting_work_activity.end_time + timedelta(minutes=60),
        duration_minutes=180,
        activity="sleep",
        category="leisure",
    )

    coding_fun = HamsterActivity(
        start_time=datetime(2024, 6, 1, hour=21, minute=15),
        end_time=datetime(2024, 6, 1, hour=21, minute=45),
        duration_minutes=30,
        activity="coding",
        category="fun",
    )

    hamster_db = HamsterDB(session)
    result = compare_activities([coding_work_activity, sleep_activity, coding_fun], hamster_db)
    assert result.new_activities == [coding_fun]
    assert result.existing == [coding_work_activity]
    assert result.conflicts == [(sleep_activity, meeting_fact)]


def _fact_from_activity(hamster_activity: HamsterActivity, *, session) -> Fact:
    db_category = _get_or_create_category(hamster_activity.category, session=session)
    activity_name = hamster_activity.activity
    db_activity = _get_or_create_activity(activity_name, category=db_category, session=session)
    fact = Fact(
        start_time=hamster_activity.start_time,
        end_time=hamster_activity.end_time,
        activity=db_activity,
    )
    session.add(fact)
    return fact


def _get_or_create_category(name: str | None, *, session) -> Category | None:
    if name is None:
        return None
    instance = session.query(Category).filter_by(name=name).one_or_none()
    if instance is None:
        instance = Category(name=name)
        session.add(instance)
        session.commit()
    return instance


def _get_or_create_activity(name: str, *, category: Category | None, session) -> Activity:
    instance = session.query(Activity).filter_by(name=name, category=category).one_or_none()
    if instance is None:
        instance = Activity(name=name, category=category)
        session.add(instance)
        session.commit()
    return instance
