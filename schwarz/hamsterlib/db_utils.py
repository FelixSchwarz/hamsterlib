from pathlib import Path

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from schwarz.hamsterlib.models import Base


def path_to_hamster_db() -> Path:
    return Path.home() / ".local" / "share" / "hamster" / "hamster.db"


def setup_db(db_url: str, *, enable_foreign_keys: bool = True, create_tables: bool = False):
    engine = create_engine(db_url, echo=False)
    if create_tables:
        Base.metadata.create_all(engine)
    if enable_foreign_keys:
        sqlalchemy.event.listen(engine, "connect", _sqlite_enable_foreign_keys)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def _sqlite_enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
