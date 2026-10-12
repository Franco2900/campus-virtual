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

function enrollmentBadge(enrollment) {
  if (!enrollment) {
    return (
      <Badge tone="neutral" icon="dash-circle">
        Sin inscripción
      </Badge>
    );
  }
  if (enrollment.active) {
    return (
      <Badge tone="success" icon="check-circle-fill">
        Inscripto activo
      </Badge>
    );
  }
  return (
    <Badge tone="warning" icon="pause-circle-fill">
      Inscripto inactivo
    </Badge>
  );
}

export default function EnrollmentsPage({ user }) {
  const { notify } = useToast();
  const isAdmin = user?.role === "admin";

  const [courses, setCourses] = useState([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [students, setStudents] = useState([]);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [studentOptions, setStudentOptions] = useState([]);
  const [selection, setSelection] = useState("");
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

  function handleCourseChange(event) {
    setSelectedCourseId(event.target.value);
    setSelection("");
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
                  <h6 className="fw-semibold">Inscribir estudiante</h6>
                  <div className="d-flex flex-wrap gap-2 align-items-end">
                    <div className="flex-grow-1">
                      {isAdmin ? (
                        <FormField id="enroll-student" label="Estudiante">
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
                        <FormField
                          id="enroll-student-id"
                          label="ID de estudiante"
                          hint="Ingresá el ID de la cuenta del estudiante a inscribir."
                        >
                          <input
                            id="enroll-student-id"
                            type="number"
                            min="1"
                            className="form-control"
                            value={selection}
                            onChange={(event) => setSelection(event.target.value)}
                            data-testid="enroll-student-id"
                          />
                        </FormField>
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
                    rows={students}
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
