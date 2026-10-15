import { Card, DataTable, EmptyState, StatCard } from "../../ui/index.js";
import { formatValue } from "./format.js";

export default function TeacherGradesView({ data }) {
  const tasks = data.tasks ?? [];
  const students = data.students ?? [];

  if (students.length === 0) {
    return (
      <Card>
        <div data-testid="teacher-grades-empty">
          <EmptyState icon="bi-people" title="No hay estudiantes inscriptos en este curso">
            Cuando haya estudiantes con inscripción activa, vas a ver acá la matriz de
            calificaciones.
          </EmptyState>
        </div>
      </Card>
    );
  }

  if (tasks.length === 0) {
    return (
      <Card>
        <div data-testid="teacher-grades-empty">
          <EmptyState icon="bi-journal-x" title="No hay tareas activas en este curso">
            Cuando el curso tenga tareas activas, vas a ver acá la matriz de calificaciones.
          </EmptyState>
        </div>
      </Card>
    );
  }

  const columns = [
    {
      key: "student",
      header: "Estudiante",
      render: (row) => (
        <div className="d-flex flex-column">
          <span className="fw-semibold">{row.student?.name}</span>
          {row.student?.email && <span className="small text-secondary">{row.student.email}</span>}
        </div>
      ),
    },
    ...tasks.map((task) => ({
      key: `task-${task.task_id}`,
      header: task.title,
      render: (row) => <span>{formatValue(row.grades?.[String(task.task_id)])}</span>,
    })),
    {
      key: "average",
      header: "Promedio",
      render: (row) => <span className="fw-semibold">{formatValue(row.average)}</span>,
    },
  ];

  return (
    <>
      <div className="row g-3 mb-3">
        <div className="col-12 col-md-6 col-xl-4">
          <StatCard
            icon="bi-graph-up-arrow"
            value={formatValue(data.course_average)}
            label="Promedio del curso"
            color="var(--role-teacher)"
            soft="var(--role-teacher-soft)"
            testId="teacher-course-average"
          />
        </div>
      </div>

      <Card className="p-0 overflow-hidden">
        <DataTable
          testId="teacher-grades-table"
          rowKey={(row) => row.student?.id}
          rowTestId={(row) => `teacher-grade-row-${row.student?.id}`}
          columns={columns}
          rows={students}
        />
      </Card>
    </>
  );
}
