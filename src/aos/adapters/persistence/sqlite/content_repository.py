from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from aos.adapters.persistence.sqlite.models import DailyCheckRow, FootageReserveRow
from aos.common.timeutil import utc_now
from aos.domain.content.footage import FootageReserve

SINGLETON_ID = 1


class SqliteFootageRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def get(self) -> FootageReserve:
        with self._sessions() as session:
            row = session.get(FootageReserveRow, SINGLETON_ID)
            if row is None:
                return FootageReserve(clips_available=0)
            return FootageReserve(
                clips_available=row.clips_available,
                clips_per_publish=row.clips_per_publish,
            )

    def save(self, reserve: FootageReserve) -> None:
        with self._sessions() as session, session.begin():
            row = session.get(FootageReserveRow, SINGLETON_ID)
            if row is None:
                row = FootageReserveRow(id=SINGLETON_ID)
                session.add(row)
            row.clips_available = reserve.clips_available
            row.clips_per_publish = reserve.clips_per_publish
            row.updated_at = utc_now().replace(tzinfo=None)


class SqliteDailyCheckLog:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def last_run(self, name: str) -> str | None:
        with self._sessions() as session:
            row = session.get(DailyCheckRow, name)
            return row.last_local_day if row else None

    def mark_run(self, name: str, local_day: str) -> None:
        with self._sessions() as session, session.begin():
            row = session.get(DailyCheckRow, name)
            if row is None:
                row = DailyCheckRow(name=name, last_local_day=local_day)
                session.add(row)
            else:
                row.last_local_day = local_day
