import { useState } from "react";

import { Button, FormField } from "../../ui/index.js";
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
    <form onSubmit={handleSubmit} noValidate>
      <FormField
        id="course-name"
        name="name"
        label="Nombre"
        value={form.name}
        onChange={handleChange}
        required
      />

      <FormField
        id="course-code"
        name="code"
        label="Código"
        value={form.code}
        onChange={handleChange}
        required
      />

      <FormField
        id="course-description"
        name="description"
        type="textarea"
        rows={3}
        label="Descripción"
        value={form.description}
        onChange={handleChange}
      />

      {error && (
        <div className="alert alert-danger py-2" role="alert">
          {error}
        </div>
      )}

      <div className="d-flex justify-content-end gap-2">
        <Button variant="soft" onClick={onCancel} disabled={submitting}>
          Cancelar
        </Button>
        <Button type="submit" icon="save" disabled={submitting}>
          {submitting ? "Guardando..." : "Guardar"}
        </Button>
      </div>
    </form>
  );
}
