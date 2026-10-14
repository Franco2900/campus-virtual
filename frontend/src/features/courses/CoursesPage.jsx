import { useEffect, useState } from "react";

import {
  Button,
  Card,
  ConfirmDialog,
  DataTable,
  Modal,
  PageHeader,
  Spinner,
  StatusBadge,
  useToast,
} from "../../ui/index.js";
import { listCourses, setCourseActive } from "./api.js";
import CourseForm from "./CourseForm.jsx";
import CourseTeachers from "./CourseTeachers.jsx";

export default function CoursesPage() {
  const { notify } = useToast();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editingCourse, setEditingCourse] = useState(null);
  const [teachersCourse, setTeachersCourse] = useState(null);
  const [confirming, setConfirming] = useState(null);
  const [toggling, setToggling] = useState(false);

  async function loadCourses() {
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
  }

  useEffect(() => {
    loadCourses();
  }, []);

  function openCreate() {
    setEditingCourse(null);
    setFormOpen(true);
  }

  function openEdit(course) {
    setEditingCourse(course);
    setFormOpen(true);
  }

  function handleSaved(saved) {
    setFormOpen(false);
    loadCourses();
    notify({
      tone: "success",
      title: editingCourse ? "Curso actualizado" : "Curso creado",
      message: `El curso "${saved.name}" se guardó correctamente.`,
    });
  }

  async function confirmToggle() {
    const course = confirming;
    if (!course) {
      return;
    }
    setToggling(true);
    try {
      const updated = await setCourseActive(course.id, !course.active);
      setCourses((previous) => previous.map((item) => (item.id === updated.id ? updated : item)));
      notify({
        tone: "success",
        title: updated.active ? "Curso activado" : "Curso desactivado",
        message: `El curso "${updated.name}" cambió de estado.`,
      });
    } catch (requestError) {
      notify({
        tone: "danger",
        title: "No se pudo cambiar el estado",
        message: requestError.message,
      });
    } finally {
      setToggling(false);
      setConfirming(null);
    }
  }

  const columns = [
    {
      key: "code",
      header: "Código",
      render: (course) => <span className="font-monospace fw-semibold">{course.code}</span>,
    },
    { key: "name", header: "Nombre" },
    {
      key: "description",
      header: "Descripción",
      render: (course) => course.description || <span className="text-secondary">—</span>,
    },
    {
      key: "active",
      header: "Estado",
      render: (course) => <StatusBadge active={course.active} />,
    },
    {
      key: "actions",
      header: "",
      className: "text-end",
      render: (course) => (
        <div className="d-flex justify-content-end gap-2">
          <Button variant="soft" className="btn-sm" icon="pencil" onClick={() => openEdit(course)}>
            Editar
          </Button>
          <Button
            variant="soft"
            className="btn-sm"
            icon="people-fill"
            onClick={() => setTeachersCourse(course)}
            data-testid={`course-teachers-${course.id}`}
          >
            Profesores
          </Button>
          <Button
            variant="soft"
            className="btn-sm"
            icon={course.active ? "toggle-off" : "toggle-on"}
            onClick={() => setConfirming(course)}
          >
            {course.active ? "Desactivar" : "Activar"}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Cursos"
        subtitle="Alta, edición y estado de los cursos del campus"
        icon="bi-journal-bookmark-fill"
        actions={
          <Button icon="plus-lg" onClick={openCreate}>
            Nuevo curso
          </Button>
        }
      />

      {error && (
        <div className="alert alert-danger d-flex align-items-center gap-2" role="alert">
          <i className="bi bi-exclamation-triangle-fill" aria-hidden="true" />
          {error}
        </div>
      )}

      <Card className="p-0 overflow-hidden">
        {loading ? (
          <div className="d-flex justify-content-center py-5">
            <Spinner label="Cargando cursos..." />
          </div>
        ) : (
          <DataTable
            columns={columns}
            rows={courses}
            empty="Todavía no hay cursos. Creá el primero con el botón de arriba."
            emptyIcon="bi-journal-x"
          />
        )}
      </Card>

      <Modal
        open={formOpen}
        title={editingCourse ? "Editar curso" : "Nuevo curso"}
        onClose={() => setFormOpen(false)}
      >
        {formOpen && (
          <CourseForm
            key={editingCourse?.id ?? "new"}
            course={editingCourse}
            onSaved={handleSaved}
            onCancel={() => setFormOpen(false)}
          />
        )}
      </Modal>

      <Modal
        open={Boolean(teachersCourse)}
        title={teachersCourse ? `Profesores de "${teachersCourse.name}"` : "Profesores"}
        onClose={() => setTeachersCourse(null)}
      >
        {teachersCourse && (
          <CourseTeachers
            key={teachersCourse.id}
            course={teachersCourse}
            onClose={() => setTeachersCourse(null)}
          />
        )}
      </Modal>

      <ConfirmDialog
        open={Boolean(confirming)}
        title={confirming?.active ? "Desactivar curso" : "Activar curso"}
        tone={confirming?.active ? "danger" : "brand"}
        icon={confirming?.active ? "toggle-off" : "toggle-on"}
        confirmVariant={confirming?.active ? "danger" : "brand"}
        confirmLabel={confirming?.active ? "Desactivar" : "Activar"}
        loading={toggling}
        message={
          confirming
            ? `¿Confirmás ${confirming.active ? "desactivar" : "activar"} el curso "${confirming.name}"?`
            : ""
        }
        onConfirm={confirmToggle}
        onCancel={() => setConfirming(null)}
      />
    </div>
  );
}
