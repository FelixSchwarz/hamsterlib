from collections.abc import Sequence
from datetime import date, datetime

import sqlalchemy
from sqlalchemy import and_
from sqlalchemy.orm import Session

from schwarz.hamsterlib.models import Fact


class HamsterDB:
    def __init__(self, session: Session):
        self.session = session

    def get_facts(self, from_: date, until: date) -> Sequence[Fact]:
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
        return self.session.execute(stmt).scalars().all()
