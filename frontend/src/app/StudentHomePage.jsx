import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { listMyCourses, listTasks } from "../features/submissions/api.js";
import { PageHeader, Card, Spinner, StatCard } from "../ui/index.js";
import { getRoleMeta } from "../ui/roles.js";

function formatDueDate(value) {
  if (!value) {
    return "Sin fecha límite";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function isOverdue(task) {
  if (!task.due_date) {
    return false;
  }
  const due = new Date(task.due_date);
  if (Number.isNaN(due.getTime())) {
    return false;
  }
  const now = new Date();
  return due.getTime() < now.getTime();
}

const QUICK_LINKS = [
  {
    to: "/submissions",
    label: "Mis entregas",
    icon: "bi-upload",
    testId: "student-quick-link-submissions",
  },
  {
    to: "/grades",
    label: "Calificaciones",
    icon: "bi-clipboard-check",
    testId: "student-quick-link-grades",
  },
  {
    to: "/chat",
    label: "Asistente",
    icon: "bi-chat-dots-fill",
    testId: "student-quick-link-chat",
  },
];

export default function StudentHomePage({ user }) {
  const [courses, setCourses] = useState(null);
  const [tasksByCourse, setTasksByCourse] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const meta = getRoleMeta(user.role);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        setLoading(true);
        setError("");
        const courseList = await listMyCourses();
        if (!active) {
          return;
        }
        setCourses(courseList || []);

        const entries = await Promise.allSettled(
          (courseList || []).map(async (course) => {
            const tasks = await listTasks(course.id);
            return [course.id, tasks || []];
          })
        );

        if (!active) {
          return;
        }

        const next = {};
        entries.forEach((result) => {
          if (result.status === "fulfilled") {
            const [courseId, tasks] = result.value;
            next[courseId] = tasks;
          }
        });
        setTasksByCourse(next);
      } catch (loadError) {
        if (active) {
          setError(loadError.message || "No se pudo cargar el inicio.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      active = false;
    };
  }, []);

  const allTasks = useMemo(() => {
    if (!courses) {
      return [];
    }
    return courses.flatMap((course) => {
      const tasks = tasksByCourse[course.id] || [];
      return tasks.map((task) => ({ ...task, courseName: course.name, courseId: course.id }));
    });
  }, [courses, tasksByCourse]);

  const pendingToSubmit = useMemo(
    () =>
      allTasks
        .filter((task) => task.active && !task.submission)
        .sort((a, b) => {
          const aDue = a.due_date ? new Date(a.due_date).getTime() : Number.POSITIVE_INFINITY;
          const bDue = b.due_date ? new Date(b.due_date).getTime() : Number.POSITIVE_INFINITY;
          return aDue - bDue;
        }),
    [allTasks]
  );

  const submitted = useMemo(() => allTasks.filter((task) => task.submission).length, [allTasks]);

  const overduePending = useMemo(
    () => pendingToSubmit.filter((task) => isOverdue(task)).length,
    [pendingToSubmit]
  );

  const enrolledCount = courses?.length || 0;

  return (
    <div data-testid="student-home">
      <PageHeader
        title={`Hola, ${user.first_name}`}
        subtitle="Inicio - Estudiante"
        icon="bi-house-door-fill"
        actions={<span className="text-secondary">Bienvenido/a al Campus Virtual</span>}
      />

      {error && (
        <div
          className="alert alert-danger d-flex align-items-center gap-2"
          role="alert"
          data-testid="student-home-error"
        >
          <i className="bi bi-exclamation-triangle-fill" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {loading && <Spinner label="Cargando tu inicio..." />}

      {!loading && !error && (
        <>
          <div className="row g-3">
            <div className="col-12 col-sm-6 col-lg-4 col-xl">
              <StatCard
                icon="bi-journal-bookmark-fill"
                value={enrolledCount}
                label="Cursos inscriptos"
                detail={[enrolledCount ? "Ves tus cursos desde el menú" : "Sin inscripciones aún"]}
                to="/grades"
                testId="student-stat-courses"
              />
            </div>
            <div className="col-12 col-sm-6 col-lg-4 col-xl">
              <StatCard
                icon="bi-upload"
                value={pendingToSubmit.length}
                label="Tareas por entregar"
                detail={[`Vencidas sin entregar: ${overduePending}`]}
                to="/submissions"
                testId="student-stat-pending"
              />
            </div>
            <div className="col-12 col-sm-6 col-lg-4 col-xl">
              <StatCard
                icon="bi-check2-circle"
                value={submitted}
                label="Entregas realizadas"
                detail={["Revisá el estado en Mis entregas"]}
                to="/submissions"
                testId="student-stat-submitted"
              />
            </div>
          </div>

          <div className="row g-3 mt-1">
            <div className="col-12 col-xl-8">
              <Card className="p-4 h-100">
                <div className="d-flex align-items-center justify-content-between mb-3">
                  <div className="d-flex align-items-center gap-2">
                    <i className="bi bi-calendar-event text-brand" aria-hidden="true" />
                    <h3 className="h6 mb-0">Próximos vencimientos</h3>
                  </div>
                  <Link to="/submissions" className="btn btn-link btn-sm px-0">
                    Ver todas
                  </Link>
                </div>
                {pendingToSubmit.length === 0 ? (
                  <p className="text-secondary mb-0">
                    No tenés tareas pendientes por entregar. Si hay nuevas tareas, van a aparecer
                    acá.
                  </p>
                ) : (
                  <div className="list-group list-group-flush">
                    {pendingToSubmit.slice(0, 6).map((task) => (
                      <Link
                        key={`${task.courseId}-${task.id}`}
                        to="/submissions"
                        className="list-group-item list-group-item-action d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-2"
                      >
                        <div>
                          <div className="fw-semibold">{task.title}</div>
                          <div className="small text-secondary">{task.courseName}</div>
                        </div>
                        <div className="text-md-end">
                          <div
                            className={`small ${isOverdue(task) ? "text-danger" : "text-secondary"}`}
                          >
                            Vence: {formatDueDate(task.due_date)}
                          </div>
                          <div className="small text-secondary">Ir a entregar</div>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </Card>
            </div>
            <div className="col-12 col-xl-4">
              <Card className="p-4 h-100">
                <div className="d-flex align-items-center gap-2 mb-3">
                  <span
                    className="d-inline-flex align-items-center justify-content-center rounded-circle"
                    style={{ width: 36, height: 36, color: meta.color, background: meta.soft }}
                  >
                    <i className={`bi ${meta.icon}`} aria-hidden="true" />
                  </span>
                  <div>
                    <div className="fw-semibold">Mi rol</div>
                    <div className="small text-secondary text-capitalize">{user.role}</div>
                  </div>
                </div>
                <h3 className="h6">Accesos rápidos</h3>
                <div className="d-flex flex-column gap-2">
                  {QUICK_LINKS.map((link) => (
                    <Link
                      key={link.to}
                      to={link.to}
                      className="campus-link-tile"
                      data-testid={link.testId}
                    >
                      <i className={`bi ${link.icon}`} aria-hidden="true" />
                      <span>{link.label}</span>
                    </Link>
                  ))}
                </div>
              </Card>
            </div>
          </div>

          {enrolledCount === 0 && (
            <Card className="p-4 mt-3">
              <div className="d-flex align-items-center gap-2 mb-2">
                <i className="bi bi-info-circle-fill text-brand" aria-hidden="true" />
                <span className="fw-semibold">Sin inscripciones</span>
              </div>
              <p className="text-secondary mb-0">
                Todavía no estás inscripto a ningún curso. Cuando un administrador o docente te
                inscriba, vas a verlo acá junto con sus tareas y calificaciones.
              </p>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
