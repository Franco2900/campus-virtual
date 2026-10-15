import { Badge, Card, DataTable, EmptyState, StatCard } from "../../ui/index.js";
import { formatDueDate, formatValue } from "./format.js";

function isGraded(task) {
  return task.grade !== null && task.grade !== undefined;
}

function isCountedWithoutGrade(task) {
  return Boolean(task.counted) && !isGraded(task);
}

function statusBadge(task) {
  if (isGraded(task)) {
    return (
      <Badge tone="success" icon="check-circle-fill">
        Corregida
      </Badge>
    );
  }
  if (isCountedWithoutGrade(task)) {
    return (
      <Badge tone="danger" icon="exclamation-circle-fill">
        Vencida sin entrega
      </Badge>
    );
  }
  if (task.submitted) {
    return (
      <Badge tone="warning" icon="hourglass-split">
        Sin corregir
      </Badge>
    );
  }
  return (
    <Badge tone="neutral" icon="hourglass">
      Sin entregar
    </Badge>
  );
}

function approvalBadge(task) {
  if (!isGraded(task)) {
    return <span className="text-secondary">—</span>;
  }
  if (task.approved) {
    return (
      <Badge tone="success" icon="patch-check-fill">
        Aprobada
      </Badge>
    );
  }
  return (
    <Badge tone="danger" icon="x-circle-fill">
      Desaprobada
    </Badge>
  );
}

function summarize(value, max = 80) {
  if (!value) {
    return "";
  }
  const text = value.replace(/\s+/g, " ").trim();
  if (!text) {
    return "";
  }
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

const columns = [
  { key: "title", header: "Tarea" },
  {
    key: "due_date",
    header: "Fecha límite",
    render: (task) => <span>{formatDueDate(task.due_date)}</span>,
  },
  { key: "status", header: "Estado", render: (task) => statusBadge(task) },
  {
    key: "grade",
    header: "Nota",
    render: (task) => {
      if (isGraded(task)) {
        return <span>{formatValue(task.grade)}</span>;
      }
      if (isCountedWithoutGrade(task)) {
        return (
          <span className="text-secondary" title="Tarea vencida sin entrega: cuenta como 1">
            {formatValue(task.effective_value)}
          </span>
        );
      }
      return <span className="text-secondary">—</span>;
    },
  },
  { key: "approval", header: "Aprobación", render: (task) => approvalBadge(task) },
  {
    key: "feedback",
    header: "Retroalimentación",
    render: (task) => {
      const feedback = summarize(task.feedback);
      return feedback ? (
        <span title={task.feedback}>{feedback}</span>
      ) : (
        <span className="text-secondary">—</span>
      );
    },
  },
];

export default function StudentGradesView({ data }) {
  const tasks = data.tasks ?? [];

  if (tasks.length === 0) {
    return (
      <Card>
        <div data-testid="student-tasks-empty">
          <EmptyState icon="bi-journal-x" title="No hay tareas activas en este curso">
            Cuando el curso tenga tareas activas, vas a ver acá tus notas y retroalimentación.
          </EmptyState>
        </div>
      </Card>
    );
  }

  return (
    <>
      <div className="row g-3 mb-3">
        <div className="col-12 col-md-6 col-xl-4">
          <StatCard
            icon="bi-graph-up-arrow"
            value={formatValue(data.average)}
            label="Promedio del curso"
            color="var(--role-student)"
            soft="var(--role-student-soft)"
            testId="student-average"
          />
        </div>
      </div>

      <Card className="p-0 overflow-hidden">
        <DataTable
          testId="student-grades-table"
          rowKey={(task) => task.task_id}
          rowTestId={(task) => `student-grade-row-${task.task_id}`}
          columns={columns}
          rows={tasks}
        />
      </Card>
    </>
  );
}
