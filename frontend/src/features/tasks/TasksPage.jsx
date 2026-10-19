import { useEffect, useMemo, useState } from "react";

import {
  Button,
  Card,
  ConfirmDialog,
  DataTable,
  EmptyState,
  FormField,
  Modal,
  PageHeader,
  Spinner,
  StatusBadge,
  useToast,
} from "../../ui/index.js";
import { formatDueDate } from "../../api/dates.js";
import { createTask, listMyCourses, listTasks, setTaskActive, updateTask } from "./api.js";
import TaskForm from "./TaskForm.jsx";

function taskBadge(task) {
  return <StatusBadge active={task.active} activeLabel="Activa" inactiveLabel="Inactiva" />;
}

export default function TasksPage() {
  const { notify } = useToast();

  const [courses, setCourses] = useState([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [tasks, setTasks] = useState([]);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [error, setError] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [confirming, setConfirming] = useState(null);
  const [toggling, setToggling] = useState(false);

  const selectedCourse = useMemo(
    () => courses.find((course) => String(course.id) === String(selectedCourseId)) ?? null,
    [courses, selectedCourseId]
  );
  const courseActive = Boolean(selectedCourse?.active);

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

  function openCreate() {
    setEditingTask(null);
    setFormOpen(true);
  }

  function openEdit(task) {
    setEditingTask(task);
    setFormOpen(true);
  }

  function closeForm() {
    setFormOpen(false);
    setEditingTask(null);
  }

  async function handleSubmit(payload) {
    setSubmitting(true);
    try {
      const saved = editingTask
        ? await updateTask(selectedCourseId, editingTask.id, payload)
        : await createTask(selectedCourseId, payload);
      await reloadTasks();
      closeForm();
      notify({
        tone: "success",
        title: editingTask ? "Tarea actualizada" : "Tarea creada",
        message: `Se guardó la tarea "${saved.title}".`,
      });
    } finally {
      setSubmitting(false);
    }
  }

  function handleToggle(task) {
    if (task.active) {
      setConfirming(task);
      return;
    }
    applyToggle(task);
  }

  async function applyToggle(task) {
    setToggling(true);
    setError("");
    try {
      const updated = await setTaskActive(selectedCourseId, task.id, !task.active);
      setTasks((previous) => previous.map((item) => (item.id === updated.id ? updated : item)));
      notify({
        tone: "success",
        title: updated.active ? "Tarea activada" : "Tarea desactivada",
        message: `La tarea "${updated.title}" cambió de estado.`,
      });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setToggling(false);
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
    { key: "active", header: "Estado", render: (task) => taskBadge(task) },
    {
      key: "actions",
      header: "",
      className: "text-end",
      render: (task) => (
        <div className="d-flex justify-content-end gap-2">
          <Button
            variant="soft"
            className="btn-sm"
            icon="pencil"
            onClick={() => openEdit(task)}
            disabled={toggling || !courseActive}
            data-testid={`task-edit-${task.id}`}
          >
            Editar
          </Button>
          <Button
            variant="soft"
            className="btn-sm"
            icon={task.active ? "toggle-off" : "toggle-on"}
            onClick={() => handleToggle(task)}
            disabled={toggling}
            data-testid={`task-toggle-${task.id}`}
          >
            {task.active ? "Desactivar" : "Activar"}
          </Button>
        </div>
      ),
    },
  ];

  const confirmingMessage = confirming
    ? `¿Confirmás desactivar la tarea "${confirming.title}"?`
    : "";

  return (
    <div data-testid="tasks-page">
      <PageHeader
        title="Tareas"
        subtitle="Creá y gestioná las tareas de tus cursos"
        icon="bi-journal-text"
      />

      {error && (
        <div
          className="alert alert-danger d-flex align-items-center gap-2"
          role="alert"
          data-testid="tasks-error"
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
          <div data-testid="tasks-empty">
            <EmptyState icon="bi-journal-x" title="No tenés cursos para gestionar">
              Cuando tengas cursos asignados, vas a poder crear tareas desde acá.
            </EmptyState>
          </div>
        </Card>
      ) : (
        <>
          <Card className="p-3 mb-3">
            <div className="d-flex flex-wrap gap-2 align-items-end">
              <div className="flex-grow-1">
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
                        {course.name} ({course.code}){course.active ? "" : " — inactivo"}
                      </option>
                    ))}
                  </select>
                </FormField>
              </div>
              <Button
                className="mb-3"
                icon="plus-lg"
                onClick={openCreate}
                disabled={!selectedCourseId || !courseActive}
                data-testid="new-task-button"
              >
                Nueva tarea
              </Button>
            </div>
          </Card>

          {selectedCourse && (
            <>
              {!courseActive && (
                <div
                  className="alert alert-warning d-flex align-items-center gap-2"
                  role="status"
                  data-testid="course-inactive-notice"
                >
                  <i className="bi bi-exclamation-triangle-fill" aria-hidden="true" />
                  El curso está inactivo. No se pueden crear ni modificar tareas.
                </div>
              )}

              <Card className="p-0 overflow-hidden">
                {loadingTasks ? (
                  <div className="d-flex justify-content-center py-5">
                    <Spinner label="Cargando tareas..." />
                  </div>
                ) : tasks.length === 0 ? (
                  <div data-testid="tasks-empty">
                    <EmptyState icon="bi-journal-x" title="No hay tareas en este curso">
                      Creá la primera tarea con el botón "Nueva tarea".
                    </EmptyState>
                  </div>
                ) : (
                  <DataTable
                    testId="tasks-table"
                    rowTestId={(task) => `task-row-${task.id}`}
                    columns={columns}
                    rows={tasks}
                  />
                )}
              </Card>
            </>
          )}
        </>
      )}

      <Modal
        open={formOpen}
        title={editingTask ? "Editar tarea" : "Nueva tarea"}
        onClose={closeForm}
      >
        {formOpen && (
          <TaskForm
            key={editingTask ? editingTask.id : "new"}
            initialValues={editingTask}
            submitting={submitting}
            onSubmit={handleSubmit}
            onCancel={closeForm}
          />
        )}
      </Modal>

      <ConfirmDialog
        open={Boolean(confirming)}
        title="Desactivar tarea"
        tone="danger"
        icon="toggle-off"
        confirmVariant="danger"
        confirmLabel="Desactivar"
        loading={toggling}
        message={confirmingMessage}
        onConfirm={() => applyToggle(confirming)}
        onCancel={() => setConfirming(null)}
      />
    </div>
  );
}
