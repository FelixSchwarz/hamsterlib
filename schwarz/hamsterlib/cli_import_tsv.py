import argparse
import sys
from datetime import datetime

from schwarz.hamsterlib.hamsterdb import HamsterDB
from schwarz.hamsterlib.high_level_api import compare_activities
from schwarz.hamsterlib.models import Fact
from schwarz.hamsterlib.tsv_parser import HamsterActivity, parse_hamster_tsv


def cli_import_tsv_main():
    parser = argparse.ArgumentParser(description="Import activities from a TSV file into Hamster")
    parser.add_argument("tsv_file", help="Path to the TSV file to import")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without actually importing",
    )
    parser.add_argument(
        "--allow-new-categories",
        action="store_true",
        help="Allow importing activities with new categories (creates them automatically)",
    )

    args = parser.parse_args()
    tsv_path = args.tsv_file
    dry_run = args.dry_run
    allow_new_categories = args.allow_new_categories

    hamster_db = HamsterDB.with_user_db()

    with open(tsv_path, "r", encoding="utf-8") as tsv_fp:
        hamster_activities = parse_hamster_tsv(tsv_fp)

    # Check for new categories before proceeding
    tsv_categories = {a.category for a in hamster_activities if a.category}
    new_categories = hamster_db.get_new_category_names(tsv_categories)
    if new_categories:
        _display_new_categories_warning(new_categories)
        if not allow_new_categories:
            print("Use --allow-new-categories to import anyway (categories will be created).")
            sys.exit(1)

    result = compare_activities(hamster_activities, hamster_db)
    print(f"New activities: {len(result.new_activities)}")
    print(f"Existing activities: {len(result.existing)}")
    print(f"Conflicting activities: {len(result.conflicts)}")

    if result.conflicts:
        for conflict in result.conflicts:
            _display_conflict(*conflict)
    if not result.new_activities:
        return

    print("\nNew activities to import:")
    for i, new_activity in enumerate(result.new_activities, 1):
        print(f"{_as_hamster_duration(new_activity)} {new_activity.activity}@{new_activity.category}")  # fmt: skip
    print("")

    if dry_run:
        print(f"🥽 Dry run: {len(result.new_activities)} entries would be imported.")
        hamster_db.rollback()
        return

    prompt = f"Do you want to import {len(result.new_activities)} new entries? (y/N): "
    should_import = _ask_for_confirmation(prompt)
    if not should_import:
        print("Import cancelled.")
        hamster_db.rollback()
        return

    hamster_db.create_backup()
    for new_activity in result.new_activities:
        hamster_db.import_tsv_activity(new_activity)
    hamster_db.commit()
    print(f"✅ {len(result.new_activities)} entries imported.")


def _display_conflict(activity: HamsterActivity, fact: Fact):
    if fact.activity:
        activity_name = fact.activity.name
        category_name = fact.activity.category.name if fact.activity.category else "???"
    else:
        activity_name = "???"
        category_name = "<uncategorized>"
    print("Conflict:")
    print(f"  TSV: {_as_hamster_duration(activity)} {activity.activity}@{activity.category}")  # fmt: skip
    print(f"  DB:  {_as_hamster_duration(fact)} {activity_name}@{category_name}")


def _as_hamster_duration(item: Fact | HamsterActivity) -> str:
    def _remove_seconds(dt: datetime) -> str:
        return dt.isoformat(timespec="minutes").replace("T", " ")

    start_str = _remove_seconds(item.start_time) if item.start_time else ""
    end_str = _remove_seconds(item.end_time) if item.end_time else ""
    return f"{start_str} - {end_str}"


def _ask_for_confirmation(prompt: str) -> bool:
    try:
        response = input(prompt).strip().lower()
        return response in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def _display_new_categories_warning(new_categories: set[str]) -> None:
    print("")
    print("⚠️  WARNING: New categories detected! ⚠️")
    print("=" * 45)
    for category in sorted(new_categories):
        print(f"  - {category}")
    print("=" * 45)
