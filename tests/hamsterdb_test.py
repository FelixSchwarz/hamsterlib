from datetime import date, datetime

import pytest
import sqlalchemy

from schwarz.hamsterlib.db_utils import setup_db
from schwarz.hamsterlib.hamsterdb import HamsterDB
from schwarz.hamsterlib.models import Activity, Category
from schwarz.hamsterlib.tsv_parser import HamsterActivity


@pytest.fixture
def session():
    db_url = "sqlite:///:memory:"
    session = setup_db(db_url, enable_foreign_keys=True, create_tables=True)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def hamster_db(session):
    return HamsterDB(session)


def test_hamsterdb_import_tsv_activity(hamster_db):
    # LATER: should create categories automatically
    _category = Category(name="Test Category")
    hamster_db.session.add(_category)
    hamster_db.session.commit()

    activity = HamsterActivity(
        start_time=datetime(2023, 1, 1, hour=12, minute=0),
        end_time=datetime(2023, 1, 1, hour=12, minute=30),
        duration_minutes=30,
        activity="Test Activity",
        category="Test Category",
    )

    fact = hamster_db.import_tsv_activity(activity)
    assert fact.start_time == activity.start_time
    assert fact.end_time == activity.end_time
    assert fact.activity.name == activity.activity
    assert fact.activity.category.name == activity.category
    hamster_db.commit()

    hamster_db.session.expunge_all()
    q_categories = sqlalchemy.select(Category)
    categories = hamster_db.session.execute(q_categories).scalars().all()
    assert [c.name for c in categories] == ["Test Category"]
    q_activities = sqlalchemy.select(Activity)
    activities = hamster_db.session.execute(q_activities).scalars().all()
    assert [a.name for a in activities] == ["Test Activity"]
    facts = hamster_db.get_facts(from_=date(2023, 1, 1), until=date(2023, 1, 1))
    assert len(facts) == 1
    (db_fact,) = facts
    assert db_fact.start_time == activity.start_time
    assert db_fact.end_time == activity.end_time
    assert db_fact.activity.name == activity.activity
    assert db_fact.activity.category.name == activity.category
