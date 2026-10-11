import { useState } from "react";

import { Button, FormField } from "../../ui/index.js";
import { updateUser } from "./api.js";

const ROLES = [
  { value: "student", label: "Estudiante" },
  { value: "teacher", label: "Profesor" },
  { value: "admin", label: "Administrador" },
];

function roleLabel(value) {
  return ROLES.find((role) => role.value === value)?.label ?? value;
}

function toForm(user) {
  return {
    first_name: user.first_name,
    last_name: user.last_name,
    email: user.email,
    role: user.role,
  };
}

export default function UserForm({ user, onSaved, onCancel }) {
  const [form, setForm] = useState(() => toForm(user));
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const roleChanged = form.role !== user.role;
  const demotingTeacher = user.role === "teacher" && form.role !== "teacher";
  const confirmationMessage =
    `¿Confirmás cambiar el rol de ${user.first_name} ${user.last_name} de ` +
    `${roleLabel(user.role)} a ${roleLabel(form.role)}?` +
    (demotingTeacher ? " Se quitarán sus asignaciones a cursos." : "");

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  async function persist() {
    setError("");
    setSubmitting(true);
    try {
      const saved = await updateUser(user.id, form);
      onSaved(saved);
    } catch (requestError) {
      setError(requestError.message);
      setConfirming(false);
    } finally {
      setSubmitting(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    if (roleChanged) {
      setConfirming(true);
      return;
    }
    persist();
  }

  const errorAlert = error ? (
    <div className="alert alert-danger py-2" role="alert" data-testid="user-form-error">
      {error}
    </div>
  ) : null;

  if (confirming) {
    return (
      <div data-testid="user-role-confirm">
        <div className="d-flex align-items-start gap-3 mb-4">
          <span
            className="auth-brand__icon"
            style={{ background: "var(--campus-brand-soft)", color: "var(--campus-brand)" }}
            aria-hidden="true"
          >
            <i className="bi bi-person-badge" />
          </span>
          <p className="mb-0">{confirmationMessage}</p>
        </div>

        {errorAlert}

        <div className="d-flex justify-content-end gap-2">
          <Button
            variant="soft"
            onClick={() => setConfirming(false)}
            disabled={submitting}
            data-testid="user-role-confirm-cancel"
          >
            Cancelar
          </Button>
          <Button
            variant="brand"
            icon="check-lg"
            onClick={persist}
            disabled={submitting}
            data-testid="user-role-confirm-accept"
          >
            {submitting ? "Guardando..." : "Confirmar cambio"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <FormField
        id="user-first-name"
        name="first_name"
        label="Nombre"
        value={form.first_name}
        onChange={handleChange}
        required
        data-testid="user-form-first-name"
      />

      <FormField
        id="user-last-name"
        name="last_name"
        label="Apellido"
        value={form.last_name}
        onChange={handleChange}
        required
        data-testid="user-form-last-name"
      />

      <FormField
        id="user-email"
        name="email"
        type="email"
        label="Correo electrónico"
        value={form.email}
        onChange={handleChange}
        required
        data-testid="user-form-email"
      />

      <FormField id="user-role" label="Rol">
        <select
          id="user-role"
          name="role"
          className="form-select"
          value={form.role}
          onChange={handleChange}
          data-testid="user-form-role"
        >
          {ROLES.map((role) => (
            <option key={role.value} value={role.value}>
              {role.label}
            </option>
          ))}
        </select>
      </FormField>

      {errorAlert}

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
