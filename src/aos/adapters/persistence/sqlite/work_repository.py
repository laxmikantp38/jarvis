from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from aos.adapters.persistence.sqlite.models import EventRow, ProjectRow, TaskRow, UserFactRow
from aos.common.timeutil import utc_now
from aos.domain.memory.classification import Confidentiality
from aos.domain.work.event import Event, EventType
from aos.domain.work.project import Project, ProjectStatus
from aos.domain.work.task import Attention, Task, TaskStatus


def _utc(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


class SqliteProjectRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def all(self) -> list[Project]:
        with self._sessions() as session:
            rows = session.scalars(select(ProjectRow).order_by(ProjectRow.key)).all()
            return [
                Project(
                    key=row.key,
                    name=row.name,
                    objective=row.objective,
                    status=ProjectStatus(row.status),
                )
                for row in rows
            ]

    def get(self, key: str) -> Project | None:
        return next((p for p in self.all() if p.key == key), None)

    def add_missing(self, projects: list[Project]) -> list[str]:
        inserted: list[str] = []
        with self._sessions() as session, session.begin():
            existing = set(session.scalars(select(ProjectRow.key)).all())
            for project in projects:
                if project.key in existing:
                    continue
                session.add(
                    ProjectRow(
                        key=project.key,
                        name=project.name,
                        objective=project.objective,
                        status=project.status.value,
                    )
                )
                inserted.append(project.key)
        return inserted


class SqliteTaskRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def open_tasks(self, project_key: str | None = None) -> list[Task]:
        with self._sessions() as session:
            query = select(TaskRow).where(TaskRow.status == TaskStatus.OPEN.value)
            if project_key:
                query = query.where(TaskRow.project_key == project_key)
            rows = session.scalars(query.order_by(TaskRow.created_at)).all()
            return [self._to_domain(row) for row in rows]

    def get(self, task_id: str) -> Task | None:
        with self._sessions() as session:
            row = session.get(TaskRow, task_id)
            return self._to_domain(row) if row else None

    def save(self, task: Task) -> None:
        with self._sessions() as session, session.begin():
            row = session.get(TaskRow, task.id)
            if row is None:
                row = TaskRow(id=task.id)
                session.add(row)
            row.project_key = task.project_key
            row.title = task.title
            row.status = task.status.value
            row.attention = task.attention.value
            row.confidentiality = task.confidentiality.value
            row.notes = task.notes
            row.created_at = task.created_at
            row.completed_at = task.completed_at

    @staticmethod
    def _to_domain(row: TaskRow) -> Task:
        return Task(
            id=row.id,
            project_key=row.project_key,
            title=row.title,
            created_at=_utc(row.created_at),
            status=TaskStatus(row.status),
            attention=Attention(row.attention),
            confidentiality=Confidentiality(row.confidentiality),
            notes=row.notes,
            completed_at=_utc(row.completed_at) if row.completed_at else None,
        )


class SqliteEventStore:
    """Append-only in the application and in the database (AD-8)."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def append(self, event: Event) -> None:
        with self._sessions() as session, session.begin():
            session.add(
                EventRow(
                    id=event.id,
                    type=event.type.value,
                    occurred_at=event.occurred_at,
                    recorded_at=event.recorded_at,
                    payload=event.payload,
                    project_key=event.project_key,
                    task_id=event.task_id,
                )
            )

    def recent(self, limit: int = 50) -> list[Event]:
        with self._sessions() as session:
            rows = session.scalars(
                select(EventRow).order_by(EventRow.occurred_at.desc()).limit(limit)
            ).all()
            return [
                Event(
                    id=row.id,
                    type=EventType(row.type),
                    occurred_at=_utc(row.occurred_at),
                    recorded_at=_utc(row.recorded_at),
                    payload=row.payload,
                    project_key=row.project_key,
                    task_id=row.task_id,
                )
                for row in rows
            ]


class SqliteUserFactRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def get(self, key: str) -> tuple[str, Confidentiality] | None:
        with self._sessions() as session:
            row = session.get(UserFactRow, key)
            if row is None:
                return None
            return row.value, Confidentiality(row.confidentiality)

    def set(self, key: str, value: str, confidentiality: Confidentiality) -> None:
        with self._sessions() as session, session.begin():
            row = session.get(UserFactRow, key)
            if row is None:
                row = UserFactRow(key=key)
                session.add(row)
            row.value = value
            row.confidentiality = confidentiality.value
            row.updated_at = utc_now().replace(tzinfo=None)

    def all(self) -> dict[str, str]:
        with self._sessions() as session:
            rows = session.scalars(select(UserFactRow).order_by(UserFactRow.key)).all()
            return {row.key: row.value for row in rows}
