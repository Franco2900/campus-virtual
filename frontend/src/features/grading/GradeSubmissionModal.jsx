import { useState } from "react";

import { Button, FormField } from "../../ui/index.js";

const GRADE_MIN = 1;
const GRADE_MAX = 10;
const FEEDBACK_MAX_LENGTH = 5000;
const GRADE_ERROR = "La calificación debe ser un entero entre 1 y 10";
const FEEDBACK_ERROR = `La retroalimentación no puede superar ${FEEDBACK_MAX_LENGTH} caracteres`;

function studentLabel(submission) {
  return submission?.student?.name ?? "el estudiante";
}

export default function GradeSubmissionModal({
  submission,
  submitting = false,
  onSubmit,
  onCancel,
}) {
  const [form, setForm] = useState(() => ({
    grade: submission?.grade ?? "",
    feedback: submission?.feedback ?? "",
  }));
  const [error, setError] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    // Client-side checks are UX only; the backend remains the source of truth.
    const rawGrade = String(form.grade).trim();
    const grade = Number(rawGrade);
    if (rawGrade === "" || !Number.isInteger(grade) || grade < GRADE_MIN || grade > GRADE_MAX) {
      setError(GRADE_ERROR);
      return;
    }

    const feedback = form.feedback ?? "";
    if (feedback.length > FEEDBACK_MAX_LENGTH) {
      setError(FEEDBACK_ERROR);
      return;
    }

    try {
      await onSubmit({ grade, feedback });
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate data-testid="grade-submission-modal">
      <p className="text-secondary">
        Corrigiendo la entrega de <strong>{studentLabel(submission)}</strong>.
      </p>

      <FormField
        id="grade-form-grade"
        name="grade"
        type="number"
        min={GRADE_MIN}
        max={GRADE_MAX}
        step="1"
        label="Calificación (1 a 10)"
        hint="Ingresá un número entero entre 1 y 10."
        value={form.grade}
        onChange={handleChange}
        required
        data-testid="grade-form-grade"
      />

      <FormField
        id="grade-form-feedback"
        name="feedback"
        type="textarea"
        rows={4}
        label="Retroalimentación"
        hint={`Opcional. Máximo ${FEEDBACK_MAX_LENGTH} caracteres.`}
        value={form.feedback}
        onChange={handleChange}
        data-testid="grade-form-feedback"
      />

      {error && (
        <div className="alert alert-danger py-2" role="alert" data-testid="grade-form-error">
          {error}
        </div>
      )}

      <div className="d-flex justify-content-end gap-2">
        <Button variant="soft" onClick={onCancel} disabled={submitting}>
          Cancelar
        </Button>
        <Button type="submit" icon="save" disabled={submitting} data-testid="grade-form-submit">
          {submitting ? "Guardando..." : "Guardar"}
        </Button>
      </div>
    </form>
  );
}
