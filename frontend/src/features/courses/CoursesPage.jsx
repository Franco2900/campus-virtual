import { useCallback, useEffect, useState } from "react";

import { listCourses, setCourseActive } from "./api.js";
import CourseForm from "./CourseForm.jsx";

const NEW_COURSE = "new";

export default function CoursesPage() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [togglingId, setTogglingId] = useState(null);

  const loadCourses = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await listCourses();
      setCourses(data);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCourses();
  }, [loadCourses]);

  function handleSaved() {
    setEditingId(null);
    loadCourses();
  }

  async function handleToggle(course) {
    setError("");
    setTogglingId(course.id);
    try {
      const updated = await setCourseActive(course.id, !course.active);
      setCourses((previous) => previous.map((item) => (item.id === updated.id ? updated : item)));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setTogglingId(null);
    }
  }

  const editingCourse = courses.find((course) => course.id === editingId) ?? null;

  return (
    <section>
      <header>
        <h2>Cursos</h2>
        <button type="button" onClick={() => setEditingId(NEW_COURSE)}>
          Nuevo curso
        </button>
      </header>

      {editingId !== null && (
        <CourseForm
          key={editingId}
          course={editingCourse}
          onSaved={handleSaved}
          onCancel={() => setEditingId(null)}
        />
      )}

      {error && <p role="alert">{error}</p>}

      {loading ? (
        <p>Cargando cursos...</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Nombre</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {courses.map((course) => (
              <tr key={course.id}>
                <td>{course.code}</td>
                <td>{course.name}</td>
                <td>{course.active ? "Activo" : "Inactivo"}</td>
                <td>
                  <button type="button" onClick={() => setEditingId(course.id)}>
                    Editar
                  </button>
                  <button
                    type="button"
                    onClick={() => handleToggle(course)}
                    disabled={togglingId === course.id}
                  >
                    {course.active ? "Desactivar" : "Activar"}
                  </button>
                </td>
              </tr>
            ))}
            {courses.length === 0 && (
              <tr>
                <td colSpan={4}>No hay cursos.</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </section>
  );
}
