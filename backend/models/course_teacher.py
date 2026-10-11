from models.base import db


class CourseTeacher(db.Model):
    __tablename__ = "course_teacher"
    __table_args__ = (db.UniqueConstraint("course_id", "teacher_id", name="uq_course_teacher"),)

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
