from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from operator import attrgetter

from schwarz.hamsterlib.hamsterdb import HamsterDB
from schwarz.hamsterlib.models import Fact
from schwarz.hamsterlib.tsv_parser import HamsterActivity


@dataclass(frozen=True)
class ComparisonResult:
    new_activities: Sequence[HamsterActivity]
    existing: Sequence[HamsterActivity]
    conflicts: Sequence[tuple[HamsterActivity, Fact]]


def compare_activities(
    hamster_activities: Sequence[HamsterActivity], hamster_db: HamsterDB
) -> ComparisonResult:
    _activities = sorted(hamster_activities, key=attrgetter("start_time"))
    if not _activities:
        return ComparisonResult(new_activities=[], existing=[], conflicts=[])
    facts_from = _activities[0].start_time.date()
    facts_until = _activities[-1].end_time.date()

    # Assume that the DB does not contain any facts that span over multiple days.
    # Just to be sure, query for a few days more on each side.
    db_from = facts_from - timedelta(days=2)
    db_until = facts_until + timedelta(days=2)
    db_facts = hamster_db.get_facts(from_=db_from, until=db_until)

    existing = []
    _remaining = []
    for activity in hamster_activities:
        if activity in db_facts:
            existing.append(activity)
        else:
            _remaining.append(activity)

    conflicts = []
    new_activities = []
    for activity in _remaining:
        overlap = False
        for fact in db_facts:
            if activity.end_time <= fact.start_time:
                continue
            elif activity.start_time >= fact.end_time:
                continue
            # complete overlap
            elif activity.start_time <= fact.start_time and activity.end_time >= fact.end_time:
                overlap = True
                break
            elif fact.start_time <= activity.start_time and fact.end_time >= activity.end_time:
                overlap = True
                break
            # partial overlap
            elif fact.start_time <= activity.start_time <= fact.end_time:
                overlap = True
                break
            elif fact.start_time <= activity.end_time <= fact.end_time:
                overlap = True
                break
        if overlap:
            conflicts.append((activity, fact))
        else:
            new_activities.append(activity)
    return ComparisonResult(new_activities=new_activities, existing=existing, conflicts=conflicts)
