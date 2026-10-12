from sqlalchemy.exc import IntegrityError

from models.base import db
from models.course import Course
from models.course_teacher import CourseTeacher
from models.enrollment import Enrollment
from models.user import User, UserRole
from services.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError


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


def list_students(course_id, current_user):
    get_manageable_course(course_id, current_user)
    return db.session.execute(
        db.select(User, Enrollment)
        .outerjoin(
            Enrollment,
            (Enrollment.student_id == User.id) & (Enrollment.course_id == course_id),
        )
        .where(User.active.is_(True))
        .where(User.role == UserRole.STUDENT)
        .order_by(User.id)
    ).all()


def enroll_student(course_id, student_id, current_user):
    course = get_manageable_course(course_id, current_user)
    if not course.active:
        raise ConflictError("El curso está inactivo")
    if not isinstance(student_id, int) or isinstance(student_id, bool):
        raise ValidationError("El campo student_id es obligatorio")

    student = db.session.execute(db.select(User).where(User.id == student_id)).scalar_one_or_none()
    if student is None:
        raise NotFoundError("El usuario no existe")
    if student.role != UserRole.STUDENT:
        raise ValidationError("El usuario no tiene rol Estudiante")
    if not student.active:
        raise ValidationError("La cuenta está inactiva")

    existing = db.session.execute(
        db.select(Enrollment).where(
            Enrollment.course_id == course_id,
            Enrollment.student_id == student_id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("El estudiante ya está inscripto en este curso")

    enrollment = Enrollment(course_id=course_id, student_id=student_id)
    db.session.add(enrollment)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("El estudiante ya está inscripto en este curso")
    return student, enrollment


def set_enrollment_active(course_id, student_id, active, current_user):
    course = get_manageable_course(course_id, current_user)
    if not course.active:
        raise ConflictError("El curso está inactivo")
    if not isinstance(active, bool):
        raise ValidationError("El campo active es obligatorio")

    enrollment = db.session.execute(
        db.select(Enrollment).where(
            Enrollment.course_id == course_id,
            Enrollment.student_id == student_id,
        )
    ).scalar_one_or_none()
    if enrollment is None:
        raise NotFoundError("La inscripción no existe")

    enrollment.active = active
    db.session.commit()
    student = db.session.execute(db.select(User).where(User.id == student_id)).scalar_one()
    return student, enrollment


def remove_enrollment(course_id, student_id, current_user):
    get_manageable_course(course_id, current_user)
    enrollment = db.session.execute(
        db.select(Enrollment).where(
            Enrollment.course_id == course_id,
            Enrollment.student_id == student_id,
        )
    ).scalar_one_or_none()
    if enrollment is None:
        raise NotFoundError("La inscripción no existe")
    db.session.delete(enrollment)
    db.session.commit()
