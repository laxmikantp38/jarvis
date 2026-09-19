"""Alembic environment.

The URL comes from the running configuration rather than alembic.ini, so a
migration is always applied to the environment you are actually using.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from aos.adapters.persistence.sqlite.models import Base
from aos.adapters.system.settings import load_settings
from aos.common import paths

config = context.config
if config.config_file_name is not None:
    # Without this, alembic silently disables every logger the application
    # already configured - including, when driven from a test, caplog's.
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def database_url() -> str:
    """The active environment's database, unless a caller names one explicitly.

    The override exists so tests can migrate a throwaway file with the real
    migrations rather than approximating the schema.
    """
    override = os.environ.get("AOS_DATABASE_OVERRIDE")
    if override:
        return f"sqlite+pysqlite:///{override}"
    settings = load_settings()
    return f"sqlite+pysqlite:///{paths.database_file(settings.environment)}"


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = database_url()
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        # Batch mode: SQLite cannot ALTER in place, so later migrations that
        # change a column need a table rebuild.
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
