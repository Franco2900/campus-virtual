import { useEffect, useMemo, useState } from "react";

import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  DataTable,
  EmptyState,
  FormField,
  PageHeader,
  Spinner,
  StatusBadge,
  useToast,
} from "../../ui/index.js";
import { listUsers } from "../users/api.js";
import {
  enrollStudent,
  listMyCourses,
  listStudents,
  removeEnrollment,
  setEnrollmentActive,
} from "./api.js";

function normalizeText(value) {
  return String(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function enrollmentBadge(enrollment) {
  if (!enrollment) {
    return (
      <Badge tone="neutral" icon="dash-circle">
        Sin inscripción
      </Badge>
    );
  }
  return (
    <StatusBadge
      active={enrollment.active}
      activeLabel="Inscripto activo"
      inactiveLabel="Inscripto inactivo"
    />
  );
}

export default function EnrollmentsPage({ user }) {
  const { notify } = useToast();
  const isAdmin = user?.role === "admin";
  const courseListLabel = isAdmin ? "Todos los cursos" : "Cursos asignados";

  const [courses, setCourses] = useState([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [students, setStudents] = useState([]);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [studentOptions, setStudentOptions] = useState([]);
  const [selection, setSelection] = useState("");
  const [studentQuery, setStudentQuery] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(null);

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
    if (!isAdmin) {
      return undefined;
    }
    let active = true;
    listUsers()
      .then((users) => {
        if (active) {
          setStudentOptions(users.filter((item) => item.role === "student" && item.active));
        }
      })
      .catch((requestError) => {
        if (active) {
          setError(requestError.message);
        }
      });
    return () => {
      active = false;
    };
  }, [isAdmin]);

  useEffect(() => {
    if (!selectedCourseId) {
      setStudents([]);
      return undefined;
    }
    let active = true;
    async function load() {
      setLoadingStudents(true);
      setError("");
      try {
        const data = await listStudents(selectedCourseId);
        if (active) {
          setStudents(data);
        }
      } catch (requestError) {
        if (active) {
          setError(requestError.message);
        }
      } finally {
        if (active) {
          setLoadingStudents(false);
        }
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [selectedCourseId]);

  async function reloadStudents() {
    const data = await listStudents(selectedCourseId);
    setStudents(data);
  }

  function handleCourseSelect(courseId) {
    setSelectedCourseId(courseId);
    setSelection("");
    setStudentQuery("");
    setError("");
  }

  async function handleEnroll() {
    const studentId = Number(selection);
    if (!selectedCourseId || !selection || !Number.isInteger(studentId)) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      await enrollStudent(selectedCourseId, studentId);
      setSelection("");
      setStudentQuery("");
      await reloadStudents();
      notify({
        tone: "success",
        title: "Estudiante inscripto",
        message: "La inscripción se registró correctamente.",
      });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  async function applyToggle(student) {
    setBusy(true);
    setError("");
    try {
      await setEnrollmentActive(selectedCourseId, student.id, !student.enrollment.active);
      await reloadStudents();
      notify({
        tone: "success",
        title: student.enrollment.active ? "Inscripción desactivada" : "Inscripción activada",
        message: `${student.first_name} ${student.last_name} cambió de estado en el curso.`,
      });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
      setConfirming(null);
    }
  }

  async function applyRemove(student) {
    setBusy(true);
    setError("");
    try {
      await removeEnrollment(selectedCourseId, student.id);
      await reloadStudents();
      notify({
        tone: "success",
        title: "Inscripción eliminada",
        message: `Se quitó a ${student.first_name} ${student.last_name} del curso.`,
      });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
      setConfirming(null);
    }
  }

  function handleToggle(student) {
    if (student.enrollment.active) {
      setConfirming({ kind: "deactivate", student });
      return;
    }
    applyToggle(student);
  }

  function handleConfirm() {
    if (!confirming) {
      return;
    }
    if (confirming.kind === "remove") {
      applyRemove(confirming.student);
      return;
    }
    applyToggle(confirming.student);
  }

  const enrolledIds = new Set(students.filter((student) => student.enrollment).map((s) => s.id));
  const availableStudents = studentOptions.filter((student) => !enrolledIds.has(student.id));

  const candidateStudents = useMemo(() => {
    const query = normalizeText(studentQuery);
    return students.filter((student) => {
      if (student.enrollment) {
        return false;
      }
      if (!query) {
        return true;
      }
      return normalizeText(`${student.first_name} ${student.last_name} ${student.email}`).includes(
        query
      );
    });
  }, [students, studentQuery]);

  const courseStudents = isAdmin ? students : students.filter((student) => student.enrollment);

  const columns = [
    { key: "first_name", header: "Nombre" },
    { key: "last_name", header: "Apellido" },
    { key: "email", header: "Correo" },
    {
      key: "enrollment",
      header: "Inscripción",
      render: (student) => enrollmentBadge(student.enrollment),
    },
    {
      key: "actions",
      header: "",
      className: "text-end",
      render: (student) => (
        <div className="d-flex justify-content-end gap-2">
          {student.enrollment ? (
            <>
              <Button
                variant="soft"
                className="btn-sm"
                icon={student.enrollment.active ? "toggle-off" : "toggle-on"}
                onClick={() => handleToggle(student)}
                disabled={busy || !courseActive}
                data-testid={`enrollment-action-${student.id}`}
              >
                {student.enrollment.active ? "Desactivar" : "Activar"}
              </Button>
              <Button
                variant="soft"
                className="btn-sm"
                icon="trash"
                onClick={() => setConfirming({ kind: "remove", student })}
                disabled={busy}
                data-testid={`enrollment-remove-${student.id}`}
              >
                Quitar
              </Button>
            </>
          ) : (
            <span className="text-secondary small">Sin inscripción</span>
          )}
        </div>
      ),
    },
  ];

  const confirmingMessage = confirming
    ? confirming.kind === "remove"
      ? `¿Confirmás eliminar la inscripción de ${confirming.student.first_name} ${confirming.student.last_name}?`
      : `¿Confirmás desactivar la inscripción de ${confirming.student.first_name} ${confirming.student.last_name}?`
    : "";

  return (
    <div data-testid="enrollments-page">
      <PageHeader
        title="Inscripciones"
        subtitle="Inscribí estudiantes y gestioná su estado en cada curso"
        icon="bi-person-plus-fill"
      />

      {error && (
        <div
          className="alert alert-danger d-flex align-items-center gap-2"
          role="alert"
          data-testid="enrollments-error"
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
          <div data-testid="enrollments-empty">
            <EmptyState icon="bi-journal-x" title="No tenés cursos para gestionar">
              Cuando tengas cursos asignados, vas a poder inscribir estudiantes desde acá.
            </EmptyState>
          </div>
        </Card>
      ) : (
        <>
          <Card className="p-3 mb-3">
            <h6 className="fw-semibold mb-3">{courseListLabel}</h6>
            <div className="list-group" data-testid="course-list" aria-label={courseListLabel}>
              {courses.map((course) => {
                const value = String(course.id);
                const selected = value === String(selectedCourseId);
                return (
                  <button
                    key={course.id}
                    type="button"
                    aria-pressed={selected}
                    className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center gap-2${
                      selected ? " active" : ""
                    }`}
                    onClick={() => handleCourseSelect(value)}
                    data-testid={`course-option-${course.id}`}
                  >
                    <span className="fw-semibold">
                      {course.name} <span className="fw-normal">({course.code})</span>
                    </span>
                    {!course.active && <StatusBadge active={false} />}
                  </button>
                );
              })}
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
                  El curso está inactivo. No se pueden inscribir ni modificar inscripciones.
                </div>
              )}

              {courseActive && (
                <Card className="p-3 mb-3">
                  <div className="d-flex flex-wrap gap-2 align-items-end">
                    <div className="flex-grow-1">
                      {isAdmin ? (
                        <FormField id="enroll-student" label="Inscribir estudiante">
                          <select
                            id="enroll-student"
                            className="form-select"
                            value={selection}
                            onChange={(event) => setSelection(event.target.value)}
                            data-testid="enroll-student-select"
                          >
                            <option value="">Seleccioná un estudiante</option>
                            {availableStudents.map((student) => (
                              <option key={student.id} value={student.id}>
                                {student.first_name} {student.last_name} ({student.email})
                              </option>
                            ))}
                          </select>
                        </FormField>
                      ) : (
                        <>
                          <FormField
                            id="enroll-student-search"
                            label="Inscribir estudiante"
                            hint="Escribí el nombre, apellido o correo. Solo se listan estudiantes activos que todavía no pertenecen al curso."
                          >
                            <input
                              id="enroll-student-search"
                              type="search"
                              className="form-control"
                              value={studentQuery}
                              onChange={(event) => setStudentQuery(event.target.value)}
                              autoComplete="off"
                              data-testid="enroll-student-search"
                            />
                          </FormField>
                          <div
                            className="list-group mb-3 overflow-auto"
                            style={{ maxHeight: "18rem" }}
                            data-testid="student-results"
                            aria-label="Estudiantes disponibles para inscribir"
                          >
                            {candidateStudents.length === 0 ? (
                              <div className="list-group-item" data-testid="student-results-empty">
                                <span style={{ color: "var(--campus-muted)" }}>
                                  {studentQuery
                                    ? "Sin coincidencias."
                                    : "Todos los estudiantes ya están inscriptos."}
                                </span>
                              </div>
                            ) : (
                              candidateStudents.map((student) => {
                                const selected = String(student.id) === String(selection);
                                return (
                                  <button
                                    key={student.id}
                                    type="button"
                                    aria-pressed={selected}
                                    className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center gap-2${
                                      selected ? " active" : ""
                                    }`}
                                    onClick={() => setSelection(String(student.id))}
                                    data-testid={`student-option-${student.id}`}
                                  >
                                    <span className="fw-semibold">
                                      {student.first_name} {student.last_name}
                                    </span>
                                    <span
                                      className="small"
                                      style={
                                        selected ? undefined : { color: "var(--campus-muted)" }
                                      }
                                    >
                                      {student.email}
                                    </span>
                                  </button>
                                );
                              })
                            )}
                          </div>
                        </>
                      )}
                    </div>
                    <Button
                      className="mb-3"
                      icon="person-plus"
                      onClick={handleEnroll}
                      disabled={busy || !selection}
                      data-testid="enroll-button"
                    >
                      Inscribir
                    </Button>
                  </div>
                </Card>
              )}

              <Card className="p-0 overflow-hidden">
                {!isAdmin && (
                  <div className="p-3 border-bottom">
                    <h6 className="fw-semibold mb-1">Estudiantes del curso</h6>
                    <p className="mb-0 small" style={{ color: "var(--campus-muted)" }}>
                      Solo figuran los estudiantes que pertenecen al curso. Para sumar a alguien,
                      usá el buscador de arriba.
                    </p>
                  </div>
                )}
                {loadingStudents ? (
                  <div className="d-flex justify-content-center py-5">
                    <Spinner label="Cargando estudiantes..." />
                  </div>
                ) : students.length === 0 ? (
                  <div data-testid="enrollments-empty">
                    <EmptyState icon="bi-person-x" title="No hay estudiantes activos">
                      Registrá estudiantes para poder inscribirlos en el curso.
                    </EmptyState>
                  </div>
                ) : (
                  <DataTable
                    testId="enrollments-table"
                    rowTestId={(student) => `enrollment-row-${student.id}`}
                    columns={columns}
                    rows={courseStudents}
                    empty={
                      isAdmin
                        ? "No hay estudiantes activos."
                        : "No hay estudiantes inscriptos en el curso."
                    }
                  />
                )}
              </Card>
            </>
          )}
        </>
      )}

      <ConfirmDialog
        open={Boolean(confirming)}
        title={confirming?.kind === "remove" ? "Eliminar inscripción" : "Desactivar inscripción"}
        tone="danger"
        icon={confirming?.kind === "remove" ? "trash" : "toggle-off"}
        confirmVariant="danger"
        confirmLabel={confirming?.kind === "remove" ? "Eliminar" : "Desactivar"}
        loading={busy}
        message={confirmingMessage}
        onConfirm={handleConfirm}
        onCancel={() => setConfirming(null)}
      />
    </div>
  );
}
