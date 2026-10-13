import { useEffect, useMemo, useState } from "react";

import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  DataTable,
  EmptyState,
  FormField,
  Modal,
  PageHeader,
  Spinner,
  useToast,
} from "../../ui/index.js";
import {
  createSubmission,
  deleteSubmission,
  listMyCourses,
  listTasks,
  updateSubmission,
} from "./api.js";
import SubmissionForm from "./SubmissionForm.jsx";

function formatDueDate(value) {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleString("es-AR", { dateStyle: "medium", timeStyle: "short" });
}

function submissionBadge(submission) {
  if (submission) {
    return (
      <Badge tone="success" icon="check-circle-fill">
        Entregada
      </Badge>
    );
  }
  return (
    <Badge tone="warning" icon="hourglass-split">
      Pendiente
    </Badge>
  );
}

export default function SubmissionsPage() {
  const { notify } = useToast();

  const [courses, setCourses] = useState([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [tasks, setTasks] = useState([]);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [error, setError] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [activeTask, setActiveTask] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [confirming, setConfirming] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const selectedCourse = useMemo(
    () => courses.find((course) => String(course.id) === String(selectedCourseId)) ?? null,
    [courses, selectedCourseId]
  );

  useEffect(() => {
    let active = true;
    async function load() {
      setLoadingCourses(true);
      setError("");
      try {
        const data = await listMyCourses();
        if (active) {
          setCourses(data);
        }
      } catch (requestError) {
        if (active) {
          setError(requestError.message);
        }
      } finally {
        if (active) {
          setLoadingCourses(false);
        }
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedCourseId) {
      setTasks([]);
      return undefined;
    }
    let active = true;
    async function load() {
      setLoadingTasks(true);
      setError("");
      try {
        const data = await listTasks(selectedCourseId);
        if (active) {
          setTasks(data);
        }
      } catch (requestError) {
        if (active) {
          setError(requestError.message);
        }
      } finally {
        if (active) {
          setLoadingTasks(false);
        }
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [selectedCourseId]);

  async function reloadTasks() {
    const data = await listTasks(selectedCourseId);
    setTasks(data);
  }

  function handleCourseChange(event) {
    setSelectedCourseId(event.target.value);
    setError("");
  }

  function openForm(task) {
    setActiveTask(task);
    setFormOpen(true);
  }

  function closeForm() {
    setFormOpen(false);
    setActiveTask(null);
  }

  async function handleSubmit(payload) {
    const task = activeTask;
    const hasSubmission = Boolean(task?.submission);
    setSubmitting(true);
    try {
      if (hasSubmission) {
        await updateSubmission(selectedCourseId, task.id, payload);
      } else {
        await createSubmission(selectedCourseId, task.id, payload);
      }
      await reloadTasks();
      closeForm();
      notify({
        tone: "success",
        title: hasSubmission ? "Entrega actualizada" : "Tarea entregada",
        message: `Se guardó tu entrega de "${task.title}".`,
      });
    } finally {
      setSubmitting(false);
    }
  }

  async function applyDelete() {
    const task = confirming;
    setDeleting(true);
    setError("");
    try {
      await deleteSubmission(selectedCourseId, task.id);
      await reloadTasks();
      notify({
        tone: "success",
        title: "Entrega eliminada",
        message: `Se eliminó tu entrega de "${task.title}".`,
      });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setDeleting(false);
      setConfirming(null);
    }
  }

  const columns = [
    { key: "title", header: "Título" },
    {
      key: "due_date",
      header: "Fecha límite",
      render: (task) => <span>{formatDueDate(task.due_date)}</span>,
    },
    { key: "submission", header: "Entrega", render: (task) => submissionBadge(task.submission) },
    {
      key: "actions",
      header: "",
      className: "text-end",
      render: (task) => (
        <div className="d-flex justify-content-end gap-2">
          <Button
            variant="soft"
            className="btn-sm"
            icon={task.submission ? "pencil" : "upload"}
            onClick={() => openForm(task)}
            disabled={deleting}
            data-testid={`submission-edit-${task.id}`}
          >
            {task.submission ? "Editar" : "Entregar"}
          </Button>
          {task.submission && (
            <Button
              variant="soft"
              className="btn-sm"
              icon="trash"
              onClick={() => setConfirming(task)}
              disabled={deleting}
              data-testid={`submission-delete-${task.id}`}
            >
              Eliminar
            </Button>
          )}
        </div>
      ),
    },
  ];

  const confirmingMessage = confirming
    ? `¿Confirmás eliminar tu entrega de "${confirming.title}"? Esta acción no se puede deshacer.`
    : "";

  return (
    <div data-testid="submissions-page">
      <PageHeader
        title="Mis entregas"
        subtitle="Entregá y gestioná tus tareas antes de la fecha límite"
        icon="bi-upload"
      />

      {error && (
        <div
          className="alert alert-danger d-flex align-items-center gap-2"
          role="alert"
          data-testid="submissions-error"
        >
          <i className="bi bi-exclamation-triangle-fill" aria-hidden="true" />
          {error}
        </div>
      )}

      {loadingCourses ? (
        <div className="d-flex justify-content-center py-5">
          <Spinner label="Cargando cursos..." />
        </div>
      ) : courses.length === 0 ? (
        <Card>
          <div data-testid="submissions-empty">
            <EmptyState icon="bi-journal-x" title="No tenés cursos inscriptos">
              Cuando te inscriban en un curso, vas a poder entregar tareas desde acá.
            </EmptyState>
          </div>
        </Card>
      ) : (
        <>
          <Card className="p-3 mb-3">
            <FormField id="course-select" label="Curso">
              <select
                id="course-select"
                className="form-select"
                value={selectedCourseId}
                onChange={handleCourseChange}
                data-testid="course-select"
              >
                <option value="">Seleccioná un curso</option>
                {courses.map((course) => (
                  <option key={course.id} value={course.id}>
                    {course.name} ({course.code})
                  </option>
                ))}
              </select>
            </FormField>
          </Card>

          {selectedCourse && (
            <Card className="p-0 overflow-hidden">
              {loadingTasks ? (
                <div className="d-flex justify-content-center py-5">
                  <Spinner label="Cargando tareas..." />
                </div>
              ) : tasks.length === 0 ? (
                <div data-testid="submissions-empty">
                  <EmptyState icon="bi-journal-x" title="No hay tareas disponibles">
                    No tenés tareas disponibles en este curso por ahora.
                  </EmptyState>
                </div>
              ) : (
                <DataTable
                  testId="submissions-table"
                  rowTestId={(task) => `task-row-${task.id}`}
                  columns={columns}
                  rows={tasks}
                />
              )}
            </Card>
          )}
        </>
      )}

      <Modal
        open={formOpen}
        title={activeTask?.submission ? "Editar entrega" : "Entregar tarea"}
        onClose={closeForm}
      >
        {formOpen && (
          <SubmissionForm
            key={activeTask ? activeTask.id : "new"}
            initialValues={activeTask?.submission}
            submitting={submitting}
            onSubmit={handleSubmit}
            onCancel={closeForm}
          />
        )}
      </Modal>

      <ConfirmDialog
        open={Boolean(confirming)}
        title="Eliminar entrega"
        tone="danger"
        icon="trash"
        confirmVariant="danger"
        confirmLabel="Eliminar"
        loading={deleting}
        message={confirmingMessage}
        onConfirm={applyDelete}
        onCancel={() => setConfirming(null)}
      />
    </div>
  );
}
