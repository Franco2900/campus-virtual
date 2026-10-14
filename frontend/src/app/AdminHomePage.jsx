import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listCourses } from "../features/courses/api.js";
import { listUsers } from "../features/users/api.js";
import { PageHeader, RoleBadge, Spinner, StatCard } from "../ui/index.js";
import { getRoleMeta } from "../ui/roles.js";

const QUICK_LINKS = [
  {
    to: "/courses",
    label: "Cursos",
    icon: "bi-journal-bookmark-fill",
    testId: "quick-link-courses",
  },
  {
    to: "/enrollments",
    label: "Inscripciones",
    icon: "bi-person-plus-fill",
    testId: "quick-link-enrollments",
  },
  {
    to: "/users",
    label: "Usuarios",
    icon: "bi-people-fill",
    testId: "quick-link-users",
  },
];

export default function AdminHomePage({ user }) {
  const [courses, setCourses] = useState(null);
  const [users, setUsers] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const [courseList, userList] = await Promise.all([listCourses(), listUsers()]);
        if (!active) {
          return;
        }
        setCourses(courseList);
        setUsers(userList);
      } catch (loadError) {
        if (active) {
          setError(loadError.message || "No se pudo cargar el resumen del campus.");
        }
      }
    }

    load();
    return () => {
      active = false;
    };
  }, []);

  const adminMeta = getRoleMeta("admin");
  const studentMeta = getRoleMeta("student");
  const teacherMeta = getRoleMeta("teacher");

  const loading = !courses || !users;
  const activeCourses = courses ? courses.filter((course) => course.active).length : 0;
  const activeUsers = users ? users.filter((item) => item.active).length : 0;
  const students = users ? users.filter((item) => item.role === "student") : [];
  const teachers = users ? users.filter((item) => item.role === "teacher") : [];
  const admins = users ? users.filter((item) => item.role === "admin") : [];
  const activeStudents = students.filter((item) => item.active).length;
  const activeTeachers = teachers.filter((item) => item.active).length;
  const activeAdmins = admins.filter((item) => item.active).length;

  return (
    <div data-testid="admin-home">
      <PageHeader
        title={`Hola, ${user.first_name}`}
        subtitle="Panel de administración del Campus Virtual"
        icon="bi-speedometer2"
        actions={<RoleBadge role={user.role} />}
      />

      {error && (
        <div
          className="alert alert-danger d-flex align-items-center gap-2"
          role="alert"
          data-testid="admin-home-error"
        >
          <i className="bi bi-exclamation-triangle-fill" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {!error && loading && <Spinner label="Cargando el resumen del campus..." />}

      {!error && !loading && (
        <>
          <div className="row g-3">
            <div className="col-12 col-sm-6 col-lg-4 col-xl">
              <StatCard
                icon="bi-journal-bookmark-fill"
                value={courses.length}
                label="Cursos"
                detail={[
                  `Activos: ${activeCourses}`,
                  `Inactivos: ${courses.length - activeCourses}`,
                ]}
                to="/courses"
                testId="stat-courses"
              />
            </div>
            <div className="col-12 col-sm-6 col-lg-4 col-xl">
              <StatCard
                icon="bi-people-fill"
                value={users.length}
                label="Usuarios"
                detail={[`Activos: ${activeUsers}`, `Inactivos: ${users.length - activeUsers}`]}
                to="/users"
                testId="stat-users"
              />
            </div>
            <div className="col-12 col-sm-6 col-lg-4 col-xl">
              <StatCard
                icon={studentMeta.icon}
                value={students.length}
                label="Estudiantes"
                detail={[
                  `Activos: ${activeStudents}`,
                  `Inactivos: ${students.length - activeStudents}`,
                ]}
                color={studentMeta.color}
                soft={studentMeta.soft}
                testId="stat-students"
              />
            </div>
            <div className="col-12 col-sm-6 col-lg-4 col-xl">
              <StatCard
                icon={teacherMeta.icon}
                value={teachers.length}
                label="Docentes"
                detail={[
                  `Activos: ${activeTeachers}`,
                  `Inactivos: ${teachers.length - activeTeachers}`,
                ]}
                color={teacherMeta.color}
                soft={teacherMeta.soft}
                testId="stat-teachers"
              />
            </div>
            <div className="col-12 col-sm-6 col-lg-4 col-xl">
              <StatCard
                icon={adminMeta.icon}
                value={admins.length}
                label="Administradores"
                detail={[`Activos: ${activeAdmins}`, `Inactivos: ${admins.length - activeAdmins}`]}
                color={adminMeta.color}
                soft={adminMeta.soft}
                testId="stat-admins"
              />
            </div>
          </div>

          <h3 className="h6 text-secondary mt-4 mb-2">Accesos rápidos</h3>
          <div className="row g-2">
            {QUICK_LINKS.map((link) => (
              <div className="col-12 col-md-4" key={link.to}>
                <Link to={link.to} className="campus-link-tile" data-testid={link.testId}>
                  <i className={`bi ${link.icon}`} aria-hidden="true" />
                  <span>{link.label}</span>
                </Link>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
