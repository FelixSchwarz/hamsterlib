from collections.abc import Iterator, Sequence
from datetime import date, datetime

import sqlalchemy
from sqlalchemy import and_
from sqlalchemy.orm import Session

from schwarz.hamsterlib.models import Fact
from schwarz.hamsterlib.tsv_parser import HamsterActivity


class HamsterDB:
    def __init__(self, session: Session):
        self.session = session

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
