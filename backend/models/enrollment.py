from datetime import UTC, datetime

from models.base import db


class Enrollment(db.Model):
    __tablename__ = "enrollment"
    __table_args__ = (db.UniqueConstraint("course_id", "student_id", name="uq_enrollment"),)

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    enrolled_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
