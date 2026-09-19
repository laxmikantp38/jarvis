"""The ventures the system starts out knowing about.

Seeded once and never overwritten, so anything the user edits stays edited.
"""

from __future__ import annotations

from aos.domain.work.project import Project, ProjectStatus


def default_projects() -> list[Project]:
    return [
        Project(
            key="railzy",
            name="Railzy",
            objective="A live train product that has to become a business.",
        ),
        Project(
            key="ghumr",
            name="Ghumr",
            # Deliberately blank on detail: the system does not yet know what
            # this is, and inventing an objective would be worse than asking.
            objective="In development. Objective not yet described.",
        ),
        Project(
            key="content",
            name="Explore The Unmapped",
            objective="Grow the audience to the point it earns.",
        ),
        Project(
            key="freelance",
            name="Freelance client",
            objective="Deliver the evening client work and keep the retainer.",
        ),
        Project(
            key="naxova",
            name="Naxova",
            objective="Form the parent company so contracting and invoicing become possible.",
            status=ProjectStatus.NOT_YET_FORMED,
        ),
        Project(
            key="personal",
            name="Personal",
            objective="Family, health, and everything that is not a venture.",
        ),
    ]
