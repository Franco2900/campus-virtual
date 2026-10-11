from sqlalchemy.exc import IntegrityError

from models.base import db
from models.course import Course
from models.course_teacher import CourseTeacher
from models.user import User, UserRole
from services.errors import ConflictError, NotFoundError, ValidationError


def _get_course_or_404(course_id):
    course = db.session.execute(
        db.select(Course).where(Course.id == course_id)
    ).scalar_one_or_none()
    if course is None:
        raise NotFoundError("El curso no existe")
    return course


def _get_user_or_404(user_id):
    user = db.session.execute(db.select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise NotFoundError("El usuario no existe")
    return user


def list_teachers(course_id):
    _get_course_or_404(course_id)
    return (
        db.session.execute(
            db.select(User)
            .join(CourseTeacher, CourseTeacher.teacher_id == User.id)
            .where(CourseTeacher.course_id == course_id)
            .where(User.role == UserRole.TEACHER)
            .order_by(User.id)
        )
        .scalars()
        .all()
    )


def clear_teacher_assignments(teacher_id):
    links = (
        db.session.execute(db.select(CourseTeacher).where(CourseTeacher.teacher_id == teacher_id))
        .scalars()
        .all()
    )
    for link in links:
        db.session.delete(link)
    return len(links)


def assign_teacher(course_id, teacher_id):
    _get_course_or_404(course_id)
    if not isinstance(teacher_id, int) or isinstance(teacher_id, bool):
        raise ValidationError("El campo teacher_id es obligatorio")
    user = _get_user_or_404(teacher_id)
    if user.role != UserRole.TEACHER:
        raise ValidationError("El usuario no tiene rol Profesor")

    existing = db.session.execute(
        db.select(CourseTeacher).where(
            CourseTeacher.course_id == course_id,
            CourseTeacher.teacher_id == teacher_id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("El profesor ya está asignado a este curso")

    link = CourseTeacher(course_id=course_id, teacher_id=teacher_id)
    db.session.add(link)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("El profesor ya está asignado a este curso")
    return user


def remove_teacher(course_id, teacher_id):
    _get_course_or_404(course_id)
    existing = db.session.execute(
        db.select(CourseTeacher).where(
            CourseTeacher.course_id == course_id,
            CourseTeacher.teacher_id == teacher_id,
        )
    ).scalar_one_or_none()
    if existing is None:
        raise NotFoundError("La asignación no existe")
    db.session.delete(existing)
    db.session.commit()
