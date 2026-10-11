import { useEffect, useState } from "react";

import { Button, FormField, Spinner, useToast } from "../../ui/index.js";
import { listUsers } from "../users/api.js";
import { assignCourseTeacher, listCourseTeachers, removeCourseTeacher } from "./api.js";

export default function CourseTeachers({ course, onClose }) {
  const { notify } = useToast();
  const [assigned, setAssigned] = useState([]);
  const [teacherOptions, setTeacherOptions] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [teachers, users] = await Promise.all([listCourseTeachers(course.id), listUsers()]);
      setAssigned(teachers);
      setTeacherOptions(users.filter((user) => user.role === "teacher"));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleAssign() {
    if (!selectedId) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      await assignCourseTeacher(course.id, Number(selectedId));
      setSelectedId("");
      await load();
      notify({ tone: "success", title: "Profesor asignado", message: "Se asignó al curso." });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleRemove(teacher) {
    setBusy(true);
    setError("");
    try {
      await removeCourseTeacher(course.id, teacher.id);
      await load();
      notify({
        tone: "success",
        title: "Profesor quitado",
        message: `Se quitó a ${teacher.first_name} ${teacher.last_name}.`,
      });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  const assignedIds = new Set(assigned.map((teacher) => teacher.id));
  const available = teacherOptions.filter((teacher) => !assignedIds.has(teacher.id));

  if (loading) {
    return (
      <div className="d-flex justify-content-center py-4">
        <Spinner label="Cargando profesores..." />
      </div>
    );
  }

  return (
    <div data-testid="course-teachers">
      {error && (
        <div className="alert alert-danger py-2" role="alert" data-testid="course-teachers-error">
          {error}
        </div>
      )}

      <h6 className="fw-semibold">Profesores asignados</h6>
      {assigned.length === 0 ? (
        <p className="text-secondary">Este curso todavía no tiene profesores asignados.</p>
      ) : (
        <ul className="list-group mb-4">
          {assigned.map((teacher) => (
            <li
              key={teacher.id}
              className="list-group-item d-flex justify-content-between align-items-center"
              data-testid={`assigned-teacher-${teacher.id}`}
            >
              <span>
                <span className="fw-semibold">
                  {teacher.first_name} {teacher.last_name}
                </span>
                <span className="text-secondary ms-2">{teacher.email}</span>
              </span>
              <Button
                variant="soft"
                className="btn-sm"
                icon="person-dash"
                onClick={() => handleRemove(teacher)}
                disabled={busy}
                data-testid={`remove-teacher-${teacher.id}`}
              >
                Quitar
              </Button>
            </li>
          ))}
        </ul>
      )}

      <h6 className="fw-semibold">Asignar profesor</h6>
      {available.length === 0 ? (
        <p className="text-secondary">No hay cuentas con rol Profesor disponibles para asignar.</p>
      ) : (
        <div className="d-flex gap-2 align-items-end">
          <div className="flex-grow-1">
            <FormField id="assign-teacher" label="Profesor">
              <select
                id="assign-teacher"
                className="form-select"
                value={selectedId}
                onChange={(event) => setSelectedId(event.target.value)}
                data-testid="assign-teacher-select"
              >
                <option value="">Seleccioná un profesor</option>
                {available.map((teacher) => (
                  <option key={teacher.id} value={teacher.id}>
                    {teacher.first_name} {teacher.last_name} ({teacher.email})
                  </option>
                ))}
              </select>
            </FormField>
          </div>
          <Button
            className="mb-3"
            icon="person-plus"
            onClick={handleAssign}
            disabled={busy || !selectedId}
            data-testid="assign-teacher-button"
          >
            Asignar
          </Button>
        </div>
      )}

      <div className="d-flex justify-content-end pt-2">
        <Button variant="soft" onClick={onClose} disabled={busy}>
          Cerrar
        </Button>
      </div>
    </div>
  );
}
