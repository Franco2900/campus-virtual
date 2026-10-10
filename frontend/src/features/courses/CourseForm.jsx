import { useState } from "react";

import { createCourse, updateCourse } from "./api.js";

const EMPTY_FORM = { name: "", code: "", description: "" };

function toForm(course) {
  if (!course) {
    return EMPTY_FORM;
  }
  return { name: course.name, code: course.code, description: course.description };
}

export default function CourseForm({ course, onSaved, onCancel }) {
  const [form, setForm] = useState(() => toForm(course));
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const isEditing = Boolean(course);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const saved = course ? await updateCourse(course.id, form) : await createCourse(form);
      onSaved(saved);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  // Native validation is disabled so the backend stays the source of truth.
  return (
    <section>
      <h3>{isEditing ? "Editar curso" : "Nuevo curso"}</h3>
      <form onSubmit={handleSubmit} noValidate>
        <label htmlFor="course-name">Nombre</label>
        <input
          id="course-name"
          name="name"
          type="text"
          value={form.name}
          onChange={handleChange}
          required
        />

        <label htmlFor="course-code">Código</label>
        <input
          id="course-code"
          name="code"
          type="text"
          value={form.code}
          onChange={handleChange}
          required
        />

        <label htmlFor="course-description">Descripción</label>
        <textarea
          id="course-description"
          name="description"
          value={form.description}
          onChange={handleChange}
        />

        <button type="submit" disabled={submitting}>
          {submitting ? "Guardando..." : "Guardar"}
        </button>
        <button type="button" onClick={onCancel} disabled={submitting}>
          Cancelar
        </button>
      </form>

      {error && <p role="alert">{error}</p>}
    </section>
  );
}
