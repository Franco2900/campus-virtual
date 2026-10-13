from werkzeug.security import generate_password_hash

from models.base import db
from models.course import Course
from models.course_teacher import CourseTeacher
from models.enrollment import Enrollment
from models.user import User, UserRole

ADMIN = {"email": "admin@example.com", "password": "adminpass123"}
STUDENT = {"email": "student@example.com", "password": "studentpass123"}
STUDENT_TWO = {"email": "student2@example.com", "password": "student2pass123"}
TEACHER = {"email": "teacher@example.com", "password": "teacherpass123"}


def _create_user(app, credentials, role, active=True, first_name="Nombre", last_name="Apellido"):
    with app.app_context():
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=credentials["email"].lower(),
            password_hash=generate_password_hash(credentials["password"]),
            role=role,
            active=active,
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, credentials):
    return client.post(
        "/api/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )


def _login_as(client, app, credentials, role, **kwargs):
    _create_user(app, credentials, role, **kwargs)
    return _login(client, credentials)


def _seed_course(app, code="PROG1", active=True):
    with app.app_context():
        course = Course(name="Programación I", code=code, description="", active=active)
        db.session.add(course)
        db.session.commit()
        return course.id


def _assign_teacher(app, course_id, teacher_id):
    with app.app_context():
        db.session.add(CourseTeacher(course_id=course_id, teacher_id=teacher_id))
        db.session.commit()


def _seed_enrollment(app, course_id, student_id, active=True):
    with app.app_context():
        enrollment = Enrollment(course_id=course_id, student_id=student_id, active=active)
        db.session.add(enrollment)
        db.session.commit()
        return enrollment.id


def test_enrollments_require_session(client, app):
    course_id = _seed_course(app)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    assert client.get(f"/api/courses/{course_id}/students").status_code == 401
    assert (
        client.post(
            f"/api/courses/{course_id}/students", json={"student_id": student_id}
        ).status_code
        == 401
    )
    assert (
        client.patch(
            f"/api/courses/{course_id}/students/{student_id}", json={"active": False}
        ).status_code
        == 401
    )
    assert client.delete(f"/api/courses/{course_id}/students/{student_id}").status_code == 401
    assert client.get("/api/courses/mine").status_code == 401


def test_enrollments_forbidden_for_student(client, app):
    _login_as(client, app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app)
    assert client.get(f"/api/courses/{course_id}/students").status_code == 403
    assert (
        client.post(f"/api/courses/{course_id}/students", json={"student_id": 1}).status_code == 403
    )
    assert (
        client.patch(f"/api/courses/{course_id}/students/1", json={"active": False}).status_code
        == 403
    )
    assert client.delete(f"/api/courses/{course_id}/students/1").status_code == 403


def test_mine_student_lists_only_active_enrollments(client, app):
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    active_course = _seed_course(app, code="PROG1")
    inactive_course = _seed_course(app, code="PROG2")
    _seed_course(app, code="PROG3")
    _seed_enrollment(app, active_course, student_id, active=True)
    _seed_enrollment(app, inactive_course, student_id, active=False)

    _login(client, STUDENT)
    response = client.get("/api/courses/mine")
    assert response.status_code == 200
    body = response.get_json()
    assert [course["id"] for course in body] == [active_course]


def test_mine_student_without_active_enrollments(client, app):
    _login_as(client, app, STUDENT, UserRole.STUDENT)
    _seed_course(app, code="PROG1")

    response = client.get("/api/courses/mine")
    assert response.status_code == 200
    assert response.get_json() == []


def test_mine_teacher_lists_only_assigned_courses(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    assigned = _seed_course(app, code="PROG1")
    assigned_inactive = _seed_course(app, code="PROG2", active=False)
    _seed_course(app, code="PROG3")
    _assign_teacher(app, assigned, teacher_id)
    _assign_teacher(app, assigned_inactive, teacher_id)

    _login(client, TEACHER)
    response = client.get("/api/courses/mine")
    assert response.status_code == 200
    body = response.get_json()
    assert [course["id"] for course in body] == [assigned, assigned_inactive]
    assert [course["active"] for course in body] == [True, False]


def test_mine_teacher_without_courses(client, app):
    _login_as(client, app, TEACHER, UserRole.TEACHER)
    _seed_course(app)
    response = client.get("/api/courses/mine")
    assert response.status_code == 200
    assert response.get_json() == []


def test_mine_admin_lists_all_courses(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    _seed_course(app, code="PROG1")
    _seed_course(app, code="PROG2", active=False)
    response = client.get("/api/courses/mine")
    assert response.status_code == 200
    assert len(response.get_json()) == 2


def test_list_students_with_and_without_enrollment(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    enrolled_id = _create_user(
        app, STUDENT, UserRole.STUDENT, first_name="Ada", last_name="Lovelace"
    )
    pending_id = _create_user(app, STUDENT_TWO, UserRole.STUDENT)
    _seed_enrollment(app, course_id, enrolled_id)

    response = client.get(f"/api/courses/{course_id}/students")
    assert response.status_code == 200
    body = response.get_json()
    assert [student["id"] for student in body] == [enrolled_id, pending_id]

    enrolled = next(student for student in body if student["id"] == enrolled_id)
    pending = next(student for student in body if student["id"] == pending_id)
    assert enrolled["first_name"] == "Ada"
    assert enrolled["role"] == "student"
    assert enrolled["enrollment"]["active"] is True
    assert enrolled["enrollment"]["enrolled_at"]
    assert pending["enrollment"] is None
    assert "password_hash" not in enrolled


def test_list_students_reflects_inactive_enrollment(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _seed_enrollment(app, course_id, student_id, active=False)

    response = client.get(f"/api/courses/{course_id}/students")
    assert response.status_code == 200
    body = response.get_json()
    assert [student["id"] for student in body] == [student_id]
    assert body[0]["enrollment"]["active"] is False


def test_list_students_excludes_inactive_and_non_students(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    active_student = _create_user(app, STUDENT, UserRole.STUDENT)
    inactive_student = _create_user(app, STUDENT_TWO, UserRole.STUDENT, active=False)
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    _seed_enrollment(app, course_id, inactive_student)

    response = client.get(f"/api/courses/{course_id}/students")
    assert response.status_code == 200
    ids = [student["id"] for student in response.get_json()]
    assert ids == [active_student]
    assert inactive_student not in ids
    assert teacher_id not in ids


def test_list_students_missing_course(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    assert client.get("/api/courses/9999/students").status_code == 404


def test_list_students_forbidden_for_unassigned_teacher(client, app):
    _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    _login(client, TEACHER)
    assert client.get(f"/api/courses/{course_id}/students").status_code == 403


def test_list_students_allowed_for_assigned_teacher(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    _assign_teacher(app, course_id, teacher_id)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _login(client, TEACHER)

    response = client.get(f"/api/courses/{course_id}/students")
    assert response.status_code == 200
    assert [student["id"] for student in response.get_json()] == [student_id]


def test_enroll_success(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)

    response = client.post(f"/api/courses/{course_id}/students", json={"student_id": student_id})
    assert response.status_code == 201
    body = response.get_json()
    assert body["id"] == student_id
    assert body["role"] == "student"
    assert body["enrollment"]["active"] is True
    assert body["enrollment"]["enrolled_at"]


def test_enroll_duplicate_active_enrollment(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    client.post(f"/api/courses/{course_id}/students", json={"student_id": student_id})

    response = client.post(f"/api/courses/{course_id}/students", json={"student_id": student_id})
    assert response.status_code == 409


def test_enroll_duplicate_inactive_enrollment(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _seed_enrollment(app, course_id, student_id, active=False)

    response = client.post(f"/api/courses/{course_id}/students", json={"student_id": student_id})
    assert response.status_code == 409


def test_enroll_inactive_course(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app, active=False)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)

    response = client.post(f"/api/courses/{course_id}/students", json={"student_id": student_id})
    assert response.status_code == 409


def test_enroll_rejects_non_student(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)

    response = client.post(f"/api/courses/{course_id}/students", json={"student_id": teacher_id})
    assert response.status_code == 400


def test_enroll_rejects_inactive_account(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT, active=False)

    response = client.post(f"/api/courses/{course_id}/students", json={"student_id": student_id})
    assert response.status_code == 400


def test_enroll_missing_student_id(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    assert client.post(f"/api/courses/{course_id}/students", json={}).status_code == 400


def test_enroll_non_integer_student_id(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    assert (
        client.post(f"/api/courses/{course_id}/students", json={"student_id": "abc"}).status_code
        == 400
    )
    assert (
        client.post(f"/api/courses/{course_id}/students", json={"student_id": True}).status_code
        == 400
    )


def test_enroll_missing_course(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    assert (
        client.post("/api/courses/9999/students", json={"student_id": student_id}).status_code
        == 404
    )


def test_enroll_missing_student(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    assert (
        client.post(f"/api/courses/{course_id}/students", json={"student_id": 9999}).status_code
        == 404
    )


def test_enroll_allowed_for_assigned_teacher(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    _assign_teacher(app, course_id, teacher_id)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _login(client, TEACHER)

    response = client.post(f"/api/courses/{course_id}/students", json={"student_id": student_id})
    assert response.status_code == 201


def test_enroll_forbidden_for_unassigned_teacher(client, app):
    _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _login(client, TEACHER)

    response = client.post(f"/api/courses/{course_id}/students", json={"student_id": student_id})
    assert response.status_code == 403


def test_patch_deactivate_and_reactivate(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    client.post(f"/api/courses/{course_id}/students", json={"student_id": student_id})

    deactivate = client.patch(
        f"/api/courses/{course_id}/students/{student_id}", json={"active": False}
    )
    assert deactivate.status_code == 200
    assert deactivate.get_json()["enrollment"]["active"] is False

    listed = client.get(f"/api/courses/{course_id}/students").get_json()
    assert listed[0]["enrollment"]["active"] is False

    reactivate = client.patch(
        f"/api/courses/{course_id}/students/{student_id}", json={"active": True}
    )
    assert reactivate.status_code == 200
    assert reactivate.get_json()["enrollment"]["active"] is True


def test_patch_missing_enrollment(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)

    response = client.patch(
        f"/api/courses/{course_id}/students/{student_id}", json={"active": False}
    )
    assert response.status_code == 404


def test_patch_missing_active_flag(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    client.post(f"/api/courses/{course_id}/students", json={"student_id": student_id})

    response = client.patch(f"/api/courses/{course_id}/students/{student_id}", json={})
    assert response.status_code == 400


def test_patch_non_boolean_active_flag(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    client.post(f"/api/courses/{course_id}/students", json={"student_id": student_id})

    response = client.patch(
        f"/api/courses/{course_id}/students/{student_id}", json={"active": "yes"}
    )
    assert response.status_code == 400


def test_patch_inactive_course(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app, active=False)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _seed_enrollment(app, course_id, student_id)

    response = client.patch(
        f"/api/courses/{course_id}/students/{student_id}", json={"active": False}
    )
    assert response.status_code == 409


def test_delete_success_and_reenroll(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    client.post(f"/api/courses/{course_id}/students", json={"student_id": student_id})

    removed = client.delete(f"/api/courses/{course_id}/students/{student_id}")
    assert removed.status_code == 200
    assert removed.get_json()["message"] == "Inscripción eliminada"

    listed = client.get(f"/api/courses/{course_id}/students").get_json()
    assert listed[0]["enrollment"] is None

    reenrolled = client.post(f"/api/courses/{course_id}/students", json={"student_id": student_id})
    assert reenrolled.status_code == 201
    assert reenrolled.get_json()["enrollment"]["active"] is True


def test_delete_missing_enrollment(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)

    response = client.delete(f"/api/courses/{course_id}/students/{student_id}")
    assert response.status_code == 404


def test_delete_allowed_on_inactive_course(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app, active=False)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _seed_enrollment(app, course_id, student_id)

    response = client.delete(f"/api/courses/{course_id}/students/{student_id}")
    assert response.status_code == 200
