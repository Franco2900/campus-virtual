import { useEffect, useState } from "react";

import { Card, EmptyState, FormField, PageHeader, Spinner } from "../../ui/index.js";
import { getGrades, listMyCourses } from "./api.js";
import StudentGradesView from "./StudentGradesView.jsx";
import TeacherGradesView from "./TeacherGradesView.jsx";

export default function GradesPage({ user }) {
  const isTeacher = user?.role === "teacher";

  const [courses, setCourses] = useState([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [grades, setGrades] = useState(null);
  const [loadingGrades, setLoadingGrades] = useState(false);
  const [error, setError] = useState("");

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
      setGrades(null);
      return undefined;
    }
    let active = true;
    async function load() {
      setLoadingGrades(true);
      setError("");
      setGrades(null);
      try {
        const data = await getGrades(selectedCourseId);
        if (active) {
          setGrades(data);
        }
      } catch (requestError) {
        if (active) {
          setError(requestError.message);
        }
      } finally {
        if (active) {
          setLoadingGrades(false);
        }
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [selectedCourseId]);

  function handleCourseChange(event) {
    setSelectedCourseId(event.target.value);
    setError("");
  }

  return (
    <div data-testid="grades-page">
      <PageHeader
        title="Calificaciones"
        subtitle="Consultá las notas, la retroalimentación y los promedios de tus cursos"
        icon="bi-clipboard-check"
      />

      {error && (
        <div
          className="alert alert-danger d-flex align-items-center gap-2"
          role="alert"
          data-testid="grades-error"
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
          <div data-testid="grades-empty">
            <EmptyState icon="bi-journal-x" title="No tenés cursos disponibles">
              {isTeacher
                ? "Cuando tengas cursos asignados, vas a poder consultar sus calificaciones desde acá."
                : "Cuando te inscriban en un curso, vas a poder consultar tus calificaciones desde acá."}
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

          {selectedCourseId &&
            (loadingGrades ? (
              <div className="d-flex justify-content-center py-5">
                <Spinner label="Cargando calificaciones..." />
              </div>
            ) : (
              grades &&
              (isTeacher ? (
                <TeacherGradesView data={grades} />
              ) : (
                <StudentGradesView data={grades} />
              ))
            ))}
        </>
      )}
    </div>
  );
}
