import { useState } from "react";

import { Button, FormField } from "../../ui/index.js";

const EMPTY_FORM = { title: "", description: "", due_date: "" };

function pad(value) {
  return String(value).padStart(2, "0");
}

// The backend sends ISO 8601 (UTC); datetime-local expects local "YYYY-MM-DDTHH:mm".
function isoToLocalInput(value) {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}

function toForm(initialValues) {
  if (!initialValues) {
    return EMPTY_FORM;
  }
  return {
    title: initialValues.title ?? "",
    description: initialValues.description ?? "",
    due_date: isoToLocalInput(initialValues.due_date),
  };
}

export default function TaskForm({ initialValues, submitting = false, onSubmit, onCancel }) {
  const [form, setForm] = useState(() => toForm(initialValues));
  const [error, setError] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    // Only serializes due_date to ISO; business rules stay on the backend.
    const payload = {
      title: form.title,
      description: form.description,
      due_date: form.due_date ? new Date(form.due_date).toISOString() : "",
    };
    try {
      await onSubmit(payload);
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <FormField
        id="task-title"
        name="title"
        label="Título"
        value={form.title}
        onChange={handleChange}
        required
        data-testid="task-form-title"
      />

      <FormField
        id="task-description"
        name="description"
        type="textarea"
        rows={3}
        label="Descripción"
        value={form.description}
        onChange={handleChange}
        data-testid="task-form-description"
      />

      <FormField
        id="task-due-date"
        name="due_date"
        type="datetime-local"
        label="Fecha límite"
        value={form.due_date}
        onChange={handleChange}
        data-testid="task-form-due-date"
      />

      {error && (
        <div className="alert alert-danger py-2" role="alert" data-testid="task-form-error">
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
