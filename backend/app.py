from pathlib import Path

from flask import Flask
from flask_migrate import Migrate

from config.config import Config
from models.base import db

SQLITE_PREFIX = "sqlite:///"

migrate = Migrate()


def _ensure_sqlite_directory(database_uri):
    if not database_uri.startswith(SQLITE_PREFIX):
        return
    database_path = database_uri[len(SQLITE_PREFIX) :]
    if database_path and ":memory:" not in database_path:
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    _ensure_sqlite_directory(app.config["SQLALCHEMY_DATABASE_URI"])

    db.init_app(app)
    migrate.init_app(app, db)

    from blueprints.auth import auth_bp
    from blueprints.chat import chat_bp
    from blueprints.courses import courses_bp
    from blueprints.enrollments import enrollments_bp
    from blueprints.grades import grades_bp
    from blueprints.grading import grading_bp
    from blueprints.submissions import submissions_bp
    from blueprints.tasks import tasks_bp
    from blueprints.users import users_bp
    from models import (  # noqa: F401  (registers model tables)
        conversation,
        course,
        course_teacher,
        enrollment,
        message,
        submission,
        task,
        user,
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(enrollments_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(grading_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(grades_bp)

    with app.app_context():
        if app.config.get("TESTING"):
            db.create_all()

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
