import { useState } from "react";

import { Button, FormField } from "../../ui/index.js";

const EMPTY_FORM = { content: "", links: "" };

function toForm(initialValues) {
  if (!initialValues) {
    return EMPTY_FORM;
  }
  return {
    content: initialValues.content ?? "",
    links: (initialValues.links ?? []).join("\n"),
  };
}

export default function SubmissionForm({ initialValues, submitting = false, onSubmit, onCancel }) {
  const [form, setForm] = useState(() => toForm(initialValues));
  const [error, setError] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    // One link per line; business rules (content-or-link) stay on the backend.
    const links = form.links
      .split("\n")
      .map((link) => link.trim())
      .filter(Boolean);
    try {
      await onSubmit({ content: form.content, links });
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <FormField
        id="submission-content"
        name="content"
        type="textarea"
        rows={5}
        label="Contenido"
        hint="Texto de tu entrega. Podés dejarlo vacío si enviás enlaces."
        value={form.content}
        onChange={handleChange}
        data-testid="submission-form-content"
      />

      <FormField
        id="submission-links"
        name="links"
        type="textarea"
        rows={3}
        label="Enlaces"
        hint="Un enlace por línea."
        value={form.links}
        onChange={handleChange}
        data-testid="submission-form-links"
      />

      {error && (
        <div className="alert alert-danger py-2" role="alert" data-testid="submission-form-error">
          {error}
        </div>
      )}

      <div className="d-flex justify-content-end gap-2">
        <Button variant="soft" onClick={onCancel} disabled={submitting}>
          Cancelar
        </Button>
        <Button
          type="submit"
          icon="save"
          disabled={submitting}
          data-testid="submission-form-submit"
        >
          {submitting ? "Guardando..." : "Guardar"}
        </Button>
      </div>
    </form>
  );
}
