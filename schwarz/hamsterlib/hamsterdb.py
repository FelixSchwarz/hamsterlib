import sqlite3
from collections.abc import Iterator, Sequence
from datetime import date, datetime
from pathlib import Path

import sqlalchemy
from sqlalchemy import and_
from sqlalchemy.orm import Session

from schwarz.hamsterlib.db_utils import path_to_hamster_db
from schwarz.hamsterlib.models import Activity, Category, Fact
from schwarz.hamsterlib.tsv_parser import HamsterActivity


class HamsterDB:
    def __init__(self, session: Session):
        self.session = session

    @classmethod
    def with_user_db(cls) -> "HamsterDB":
        return cls.from_db_path(path_to_hamster_db())

    @classmethod
    def from_db_path(cls, db_path: Path) -> "HamsterDB":
        db_url = f"sqlite:///{db_path}"
        session = Session(sqlalchemy.create_engine(db_url))
        return cls(session)

    def create_activity(self, name: str, category: Category | None) -> Activity:
        activity = Activity(name=name, category=category, search_name=name.lower())
        return activity

    def get_activity(self, name: str, category: Category | None = None) -> Activity | None:
        q_activity = sqlalchemy.select(Activity).where(
            and_(
                Activity.name == name,
                Activity.deleted == 0,
                Activity.category == category,
            )
        )
        return self.session.execute(q_activity).scalar_one_or_none()

    def get_facts(self, from_: date, until: date) -> "HamsterFacts":
        """
        Retrieve all facts whose start_time falls within the specified date
        range (end date is included).
        """
        stmt = (
            sqlalchemy.select(Fact)
            .where(
                and_(
                    Fact.start_time >= datetime.combine(from_, datetime.min.time()),
                    Fact.start_time <= datetime.combine(until, datetime.max.time()),
                )
            )
            .order_by(Fact.start_time)
        )
        db_facts = self.session.execute(stmt).scalars().all()
        return HamsterFacts(db_facts)

    def import_tsv_activity(self, activity: HamsterActivity) -> Fact:
        category_name = activity.category
        q_category = sqlalchemy.select(Category).where(Category.name == category_name)
        category = self.session.execute(q_category).scalar_one_or_none()
        assert category is not None, f"Category {category_name} not found in DB"

        db_activity = self.get_activity(activity.activity, category)
        if db_activity is None:
            db_activity = self.create_activity(activity.activity, category)

        fact = Fact(
            start_time=activity.start_time,
            end_time=activity.end_time,
            activity=db_activity,
        )
        self.session.add(fact)
        return fact

    def db_path(self) -> Path:
        return Path(self.session.bind.url.database)

    def create_backup(self) -> Path:
        now_str = datetime.now().strftime("%Y%m%d-%H%M%S")
        path_backup_db = self.db_path().with_suffix(f".{now_str}.db")

        connection_to_backup_db = sqlite3.connect(path_backup_db)
        raw_connection = self.session.connection().connection
        raw_connection.backup(connection_to_backup_db)
        connection_to_backup_db.close()

        return path_backup_db

    def commit(self) -> None:
        self.session.commit()


class HamsterFacts:
    def __init__(self, facts: Sequence[Fact]):
        self.facts = facts

    def __contains__(self, hamster_activity: HamsterActivity) -> bool:
        activity_period = (hamster_activity.start_time, hamster_activity.end_time)
        activity_description = (hamster_activity.activity, hamster_activity.category)
        for existing_fact in self.facts:
            fact_period = (existing_fact.start_time, existing_fact.end_time)
            fact_str = (existing_fact.activity.name, existing_fact.activity.category.name)
            if (activity_period == fact_period) and (activity_description == fact_str):
                return True
        return False

    def __iter__(self) -> Iterator[Fact]:
        return iter(self.facts)

    def __len__(self) -> int:
        return len(self.facts)
