from datetime import UTC, datetime

from models.base import db


class Submission(db.Model):
    __tablename__ = "submission"
    __table_args__ = (
        db.UniqueConstraint("task_id", "student_id", name="uq_submission_task_student"),
    )

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=False, default="")
    links = db.Column(db.JSON, nullable=False, default=list)
    grade = db.Column(db.Integer, nullable=True)
    feedback = db.Column(db.Text, nullable=True, default="")
    graded_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
