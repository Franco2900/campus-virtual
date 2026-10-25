import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { listMyCourses, listTasks, getSubmissions } from "../features/grading/api.js";
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

const QUICK_LINKS = [
  {
    to: "/tasks",
    label: "Tareas",
    icon: "bi-journal-text",
    testId: "teacher-quick-link-tasks",
  },
  {
    to: "/grading",
    label: "Corregir tareas",
    icon: "bi-check2-square",
    testId: "teacher-quick-link-grading",
  },
  {
    to: "/grades",
    label: "Calificaciones",
    icon: "bi-clipboard-check",
    testId: "teacher-quick-link-grades",
  },
  {
    to: "/enrollments",
    label: "Inscripciones",
    icon: "bi-person-plus-fill",
    testId: "teacher-quick-link-enrollments",
  },
];

export default function TeacherHomePage({ user }) {
  const [courses, setCourses] = useState(null);
  const [tasksByCourse, setTasksByCourse] = useState({});
  const [submissionsByTask, setSubmissionsByTask] = useState({});
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

        const taskEntries = await Promise.allSettled(
          (courseList || []).map(async (course) => {
            const tasks = await listTasks(course.id);
            return [course.id, tasks || []];
          })
        );

        if (!active) {
          return;
        }

        const tasksMap = {};
        taskEntries.forEach((result) => {
          if (result.status === "fulfilled") {
            const [courseId, tasks] = result.value;
            tasksMap[courseId] = tasks;
          }
        });
        setTasksByCourse(tasksMap);

        const activeTasks = Object.entries(tasksMap).flatMap(([courseId, tasks]) =>
          tasks.filter((task) => task.active).map((task) => ({ courseId, task }))
        );

        const submissionEntries = await Promise.allSettled(
          activeTasks.map(async ({ courseId, task }) => {
            const submissions = await getSubmissions(courseId, task.id);
            return [`${courseId}-${task.id}`, submissions || []];
          })
        );

        if (!active) {
          return;
        }

        const submissionsMap = {};
        submissionEntries.forEach((result) => {
          if (result.status === "fulfilled") {
            const [key, submissions] = result.value;
            submissionsMap[key] = submissions;
          }
        });
        setSubmissionsByTask(submissionsMap);
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

  const allActiveTasks = useMemo(() => {
    if (!courses) {
      return [];
    }
    return courses.flatMap((course) => {
      const tasks = (tasksByCourse[course.id] || []).filter((task) => task.active);
      return tasks.map((task) => ({ ...task, courseName: course.name, courseId: course.id }));
    });
  }, [courses, tasksByCourse]);

  const pendingGrading = useMemo(() => {
    const items = [];
    allActiveTasks.forEach((task) => {
      const key = `${task.courseId}-${task.id}`;
      const submissions = submissionsByTask[key] || [];
      submissions.forEach((submission) => {
        if (submission.grade === null || submission.grade === undefined) {
          items.push({
            key: `${key}-${submission.student_id}`,
            taskTitle: task.title,
            courseName: task.courseName,
            courseId: task.courseId,
            taskId: task.id,
            studentName: submission.student?.name || `Estudiante #${submission.student_id}`,
            submittedAt: submission.submitted_at,
          });
        }
      });
    });
    return items.slice(0, 8);
  }, [allActiveTasks, submissionsByTask]);

  const assignedCourses = courses?.length || 0;
  const activeTasksCount = allActiveTasks.length;

  return (
    <div data-testid="teacher-home">
      <PageHeader
        title={`Hola, ${user.first_name}`}
        subtitle="Inicio - Docente"
        icon="bi-easel-fill"
        actions={<span className="text-secondary">Bienvenido/a al Campus Virtual</span>}
      />

      {error && (
        <div
          className="alert alert-danger d-flex align-items-center gap-2"
          role="alert"
          data-testid="teacher-home-error"
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
                value={assignedCourses}
                label="Mis cursos"
                detail={[
                  assignedCourses ? "Administrá inscripciones y tareas" : "Sin cursos asignados",
                ]}
                to="/enrollments"
                testId="teacher-stat-courses"
              />
            </div>
            <div className="col-12 col-sm-6 col-lg-4 col-xl">
              <StatCard
                icon="bi-journal-text"
                value={activeTasksCount}
                label="Tareas activas"
                detail={["Creá y gestioná desde Tareas"]}
                to="/tasks"
                testId="teacher-stat-tasks"
              />
            </div>
            <div className="col-12 col-sm-6 col-lg-4 col-xl">
              <StatCard
                icon="bi-check2-square"
                value={pendingGrading.length}
                label="Entregas por corregir"
                detail={["Ir a Corregir tareas"]}
                to="/grading"
                testId="teacher-stat-pending-grading"
              />
            </div>
          </div>

          <div className="row g-3 mt-1">
            <div className="col-12 col-xl-8">
              <Card className="p-4 h-100">
                <div className="d-flex align-items-center justify-content-between mb-3">
                  <div className="d-flex align-items-center gap-2">
                    <i className="bi bi-inbox text-brand" aria-hidden="true" />
                    <h3 className="h6 mb-0">Por corregir</h3>
                  </div>
                  <Link to="/grading" className="btn btn-link btn-sm px-0">
                    Ir a corregir
                  </Link>
                </div>
                {pendingGrading.length === 0 ? (
                  <p className="text-secondary mb-0">
                    No hay entregas pendientes de corrección. Cuando un estudiante entregue, van a
                    aparecer acá.
                  </p>
                ) : (
                  <div className="list-group list-group-flush">
                    {pendingGrading.map((item) => (
                      <Link
                        key={item.key}
                        to="/grading"
                        className="list-group-item list-group-item-action d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-2"
                      >
                        <div>
                          <div className="fw-semibold">{item.studentName}</div>
                          <div className="small text-secondary">
                            {item.courseName} · {item.taskTitle}
                          </div>
                        </div>
                        <div className="text-md-end">
                          <div className="small text-secondary">
                            {item.submittedAt
                              ? `Entregado: ${formatDueDate(item.submittedAt)}`
                              : "Sin fecha de entrega"}
                          </div>
                          <div className="small text-secondary">Corregir</div>
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

          {assignedCourses === 0 && (
            <Card className="p-4 mt-3">
              <div className="d-flex align-items-center gap-2 mb-2">
                <i className="bi bi-info-circle-fill text-brand" aria-hidden="true" />
                <span className="fw-semibold">Sin cursos asignados</span>
              </div>
              <p className="text-secondary mb-0">
                Aún no tenés cursos asignados. Cuando un administrador te asigne a un curso, vas a
                poder crear tareas, inscribir estudiantes y corregir entregas.
              </p>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
