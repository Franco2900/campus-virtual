from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from flask_migrate import upgrade as migrate_upgrade

from app import create_app
from models import (  # noqa: F401  (registers all model tables on the metadata)
    course,
    enrollment,
    user,
)
from models.base import db

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def test_migrations_match_models(tmp_path):
    application = create_app(
        {
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{(tmp_path / 'migrated.db').as_posix()}",
        }
    )
    with application.app_context():
        migrate_upgrade(directory=str(MIGRATIONS_DIR))
        with db.engine.connect() as connection:
            context = MigrationContext.configure(connection)
            diff = compare_metadata(context, db.metadata)

    assert diff == []
