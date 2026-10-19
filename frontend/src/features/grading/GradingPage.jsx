import { useEffect, useMemo, useState } from "react";

import {
  Badge,
  Button,
  Card,
  DataTable,
  EmptyState,
  FormField,
  Modal,
  PageHeader,
  Spinner,
  useToast,
} from "../../ui/index.js";
import { getSubmissions, gradeSubmission, listMyCourses, listTasks } from "./api.js";
import GradeSubmissionModal from "./GradeSubmissionModal.jsx";

function studentName(submission) {
  return submission.student?.name ?? `Estudiante #${submission.student_id}`;
}

function isGraded(submission) {
  return submission.grade !== null && submission.grade !== undefined;
}

function correctionBadge(submission) {
  if (isGraded(submission)) {
    return (
      <Badge tone="success" icon="check-circle-fill">
        Corregida
      </Badge>
    );
  }
  return (
    <Badge tone="warning" icon="hourglass-split">
      No corregida
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

function SubmissionBody({ submission }) {
  const content = summarize(submission.content);
  const links = submission.links ?? [];

  if (!content && links.length === 0) {
    return <span className="text-secondary">—</span>;
  }

  return (
    <div className="d-flex flex-column gap-1">
      {content && <span title={submission.content}>{content}</span>}
      {links.length > 0 && (
        <span className="small text-secondary">
          {links.length === 1 ? "1 enlace" : `${links.length} enlaces`}
        </span>
      )}
    </div>
  );
}

export default function GradingPage() {
  const { notify } = useToast();

  const [courses, setCourses] = useState([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [tasks, setTasks] = useState([]);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState("");
  const [submissions, setSubmissions] = useState([]);
  const [loadingSubmissions, setLoadingSubmissions] = useState(false);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [activeSubmission, setActiveSubmission] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const selectedCourse = useMemo(
    () => courses.find((course) => String(course.id) === String(selectedCourseId)) ?? null,
    [courses, selectedCourseId]
  );
  const selectedTask = useMemo(
    () => tasks.find((task) => String(task.id) === String(selectedTaskId)) ?? null,
    [tasks, selectedTaskId]
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
          setTasks((data ?? []).filter((task) => task.active));
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

  useEffect(() => {
    if (!selectedTaskId) {
      setSubmissions([]);
      return undefined;
    }
    let active = true;
    async function load() {
      setLoadingSubmissions(true);
      setError("");
      try {
        const data = await getSubmissions(selectedCourseId, selectedTaskId);
        if (active) {
          setSubmissions(data);
        }
      } catch (requestError) {
        if (active) {
          setError(requestError.message);
        }
      } finally {
        if (active) {
          setLoadingSubmissions(false);
        }
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [selectedCourseId, selectedTaskId]);

  async function reloadSubmissions() {
    const data = await getSubmissions(selectedCourseId, selectedTaskId);
    setSubmissions(data);
  }

  function handleCourseChange(event) {
    setSelectedCourseId(event.target.value);
    setSelectedTaskId("");
    setSubmissions([]);
    setError("");
  }

  function handleTaskChange(event) {
    setSelectedTaskId(event.target.value);
    setSubmissions([]);
    setError("");
  }

  function openGrade(submission) {
    setActiveSubmission(submission);
    setModalOpen(true);
  }

  function closeModal() {
    setModalOpen(false);
    setActiveSubmission(null);
  }

  async function handleSubmit(data) {
    const submission = activeSubmission;
    setSubmitting(true);
    try {
      await gradeSubmission(selectedCourseId, selectedTaskId, submission.student_id, data);
      await reloadSubmissions();
      closeModal();
      notify({
        tone: "success",
        title: isGraded(submission) ? "Corrección actualizada" : "Corrección guardada",
        message: `Se guardó la corrección de ${studentName(submission)}.`,
      });
    } finally {
      setSubmitting(false);
    }
  }

  const columns = [
    {
      key: "student",
      header: "Estudiante",
      render: (submission) => (
        <div className="d-flex flex-column">
          <span className="fw-semibold">{studentName(submission)}</span>
          {submission.student?.email && (
            <span className="small text-secondary">{submission.student.email}</span>
          )}
        </div>
      ),
    },
    {
      key: "body",
      header: "Entrega",
      render: (submission) => <SubmissionBody submission={submission} />,
    },
    { key: "status", header: "Estado", render: (submission) => correctionBadge(submission) },
    {
      key: "grade",
      header: "Nota",
      render: (submission) => <span>{isGraded(submission) ? submission.grade : "—"}</span>,
    },
    {
      key: "feedback",
      header: "Retroalimentación",
      render: (submission) => {
        const feedback = summarize(submission.feedback, 60);
        return feedback ? (
          <span title={submission.feedback}>{feedback}</span>
        ) : (
          <span className="text-secondary">—</span>
        );
      },
    },
    {
      key: "actions",
      header: "",
      className: "text-end",
      render: (submission) => (
        <div className="d-flex justify-content-end gap-2">
          <Button
            variant="soft"
            className="btn-sm"
            icon="pencil"
            onClick={() => openGrade(submission)}
            disabled={submitting}
            data-testid={`grade-submission-${submission.student_id}`}
          >
            {isGraded(submission) ? "Modificar" : "Corregir"}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div data-testid="grading-page">
      <PageHeader
        title="Corregir tareas"
        subtitle="Corregí las entregas de tus cursos y dejá retroalimentación"
        icon="bi-check2-square"
      />

      {error && (
        <div
          className="alert alert-danger d-flex align-items-center gap-2"
          role="alert"
          data-testid="grading-error"
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
          <div data-testid="grading-empty">
            <EmptyState icon="bi-journal-x" title="No tenés cursos para corregir">
              Cuando tengas cursos asignados, vas a poder corregir las entregas desde acá.
            </EmptyState>
          </div>
        </Card>
      ) : (
        <>
          <Card className="p-3 mb-3">
            <div className="row g-3">
              <div className="col-12 col-md-6">
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
              <div className="col-12 col-md-6">
                <FormField id="task-select" label="Tarea">
                  <select
                    id="task-select"
                    className="form-select"
                    value={selectedTaskId}
                    onChange={handleTaskChange}
                    disabled={!selectedCourseId || loadingTasks}
                    data-testid="task-select"
                  >
                    <option value="">
                      {loadingTasks ? "Cargando tareas..." : "Seleccioná una tarea"}
                    </option>
                    {tasks.map((task) => (
                      <option key={task.id} value={task.id}>
                        {task.title}
                      </option>
                    ))}
                  </select>
                </FormField>
              </div>
            </div>
          </Card>

          {selectedCourse && selectedTask && (
            <Card className="p-0 overflow-hidden">
              {loadingSubmissions ? (
                <div className="d-flex justify-content-center py-5">
                  <Spinner label="Cargando entregas..." />
                </div>
              ) : submissions.length === 0 ? (
                <div data-testid="grading-submissions-empty">
                  <EmptyState icon="bi-inbox" title="No hay entregas en esta tarea">
                    Cuando los estudiantes entreguen, vas a poder corregirlas desde acá.
                  </EmptyState>
                </div>
              ) : (
                <DataTable
                  testId="grading-submissions-table"
                  rowKey={(submission) => submission.id}
                  rowTestId={(submission) => `grading-row-${submission.student_id}`}
                  columns={columns}
                  rows={submissions}
                />
              )}
            </Card>
          )}
        </>
      )}

      <Modal
        open={modalOpen}
        title={isGraded(activeSubmission ?? {}) ? "Modificar corrección" : "Corregir entrega"}
        size="lg"
        scrollable
        onClose={closeModal}
      >
        {modalOpen && (
          <GradeSubmissionModal
            key={activeSubmission ? activeSubmission.student_id : "new"}
            submission={activeSubmission}
            submitting={submitting}
            onSubmit={handleSubmit}
            onCancel={closeModal}
          />
        )}
      </Modal>
    </div>
  );
}
