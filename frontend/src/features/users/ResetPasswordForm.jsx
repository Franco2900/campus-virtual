import { useState } from "react";

import { Button, FormField } from "../../ui/index.js";
import { resetUserPassword } from "./api.js";

export default function ResetPasswordForm({ user, onSaved, onCancel }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await resetUserPassword(user.id, password);
      onSaved();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <p className="text-secondary">
        Vas a asignar una nueva contraseña a{" "}
        <strong>
          {user.first_name} {user.last_name}
        </strong>{" "}
        ({user.email}).
      </p>

      <FormField
        id="reset-password"
        name="password"
        type="password"
        label="Nueva contraseña"
        hint="Mínimo 8 caracteres."
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        required
        data-testid="reset-password-input"
      />

      {error && (
        <div className="alert alert-danger py-2" role="alert" data-testid="reset-password-error">
          {error}
        </div>
      )}

      <div className="d-flex justify-content-end gap-2">
        <Button variant="soft" onClick={onCancel} disabled={submitting}>
          Cancelar
        </Button>
        <Button type="submit" icon="key-fill" disabled={submitting}>
          {submitting ? "Guardando..." : "Resetear contraseña"}
        </Button>
      </div>
    </form>
  );
}
