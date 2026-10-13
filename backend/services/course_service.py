from sqlalchemy.exc import IntegrityError

from models.base import db
from models.course import Course
from models.course_teacher import CourseTeacher
from models.user import UserRole
from services.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError

NAME_MAX_LENGTH = 200
CODE_MAX_LENGTH = 50
DESCRIPTION_MAX_LENGTH = 1000


def get_manageable_course(course_id, current_user):
    course = db.session.execute(
        db.select(Course).where(Course.id == course_id)
    ).scalar_one_or_none()
    if course is None:
        raise NotFoundError("El curso no existe")

    if current_user.role == UserRole.TEACHER:
        assignment = db.session.execute(
            db.select(CourseTeacher).where(
                CourseTeacher.course_id == course_id,
                CourseTeacher.teacher_id == current_user.id,
            )
        ).scalar_one_or_none()
        if assignment is None:
            raise ForbiddenError("No trabajás en ese curso")

    return course


def list_courses():
    return db.session.execute(db.select(Course).order_by(Course.id)).scalars().all()


def list_courses_for_user(current_user):
    if current_user.role == UserRole.TEACHER:
        return (
            db.session.execute(
                db.select(Course)
                .join(CourseTeacher, CourseTeacher.course_id == Course.id)
                .where(CourseTeacher.teacher_id == current_user.id)
                .order_by(Course.id)
            )
            .scalars()
            .all()
        )
    return list_courses()


def get_course_or_404(course_id):
    course = db.session.execute(
        db.select(Course).where(Course.id == course_id)
    ).scalar_one_or_none()
    if course is None:
        raise NotFoundError("El curso no existe")
    return course


def _validate(data):
    if not isinstance(data, dict):
        raise ValidationError("El cuerpo de la solicitud debe ser un objeto JSON")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValidationError("El campo nombre es obligatorio")
    name = name.strip()
    if len(name) > NAME_MAX_LENGTH:
        raise ValidationError(f"El nombre no puede superar {NAME_MAX_LENGTH} caracteres")

    code = data.get("code")
    if not isinstance(code, str) or not code.strip():
        raise ValidationError("El campo código es obligatorio")
    code = code.strip().upper()
    if len(code) > CODE_MAX_LENGTH:
        raise ValidationError(f"El código no puede superar {CODE_MAX_LENGTH} caracteres")

    description = data.get("description") or ""
    if not isinstance(description, str):
        raise ValidationError("La descripción debe ser texto")
    description = description.strip()
    if len(description) > DESCRIPTION_MAX_LENGTH:
        raise ValidationError(
            f"La descripción no puede superar {DESCRIPTION_MAX_LENGTH} caracteres"
        )

    return name, code, description


def _ensure_code_available(code, exclude_id=None):
    query = db.select(Course).where(Course.code == code)
    if exclude_id is not None:
        query = query.where(Course.id != exclude_id)
    existing = db.session.execute(query).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("Ya existe un curso con ese código")


def create_course(data):
    name, code, description = _validate(data)
    _ensure_code_available(code)
    course = Course(name=name, code=code, description=description, active=True)
    db.session.add(course)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("Ya existe un curso con ese código")
    return course


def update_course(course_id, data):
    course = get_course_or_404(course_id)
    name, code, description = _validate(data)
    _ensure_code_available(code, exclude_id=course.id)
    course.name = name
    course.code = code
    course.description = description
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("Ya existe un curso con ese código")
    return course


def set_course_active(course_id, active):
    course = get_course_or_404(course_id)
    if not isinstance(active, bool):
        raise ValidationError("El campo active debe ser booleano")
    course.active = active
    db.session.commit()
    return course
