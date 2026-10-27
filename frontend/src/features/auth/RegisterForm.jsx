import { useState } from "react";

import { Button, FormField } from "../../ui/index.js";
import { registerUser } from "./api.js";

const INITIAL_FORM = {
  firstName: "",
  lastName: "",
  email: "",
  password: "",
};

export default function RegisterForm({ onSuccess, onShowLogin }) {
  const [form, setForm] = useState(INITIAL_FORM);
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
      const user = await registerUser(form);
      setForm(INITIAL_FORM);
      onSuccess?.(user);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  // Native validation is disabled so the backend stays the source of truth.
  return (
    <>
      <h2 className="h5 mb-3">Crear cuenta</h2>
      <form onSubmit={handleSubmit} noValidate>
        <FormField
          id="firstName"
          name="firstName"
          label="Nombre"
          autoComplete="given-name"
          value={form.firstName}
          onChange={handleChange}
          required
        />

        <FormField
          id="lastName"
          name="lastName"
          label="Apellido"
          autoComplete="family-name"
          value={form.lastName}
          onChange={handleChange}
          required
        />

        <FormField
          id="email"
          name="email"
          type="email"
          label="Correo electrónico"
          autoComplete="email"
          value={form.email}
          onChange={handleChange}
          required
        />

        <FormField
          id="password"
          name="password"
          type="password"
          label="Contraseña"
          autoComplete="new-password"
          value={form.password}
          onChange={handleChange}
          required
        />

        {error && (
          <div className="alert alert-danger py-2" role="alert" data-testid="register-error">
            {error}
          </div>
        )}

        <Button type="submit" icon="person-plus-fill" className="w-100" disabled={submitting}>
          {submitting ? "Enviando..." : "Registrarme"}
        </Button>
      </form>

      <p className="text-center text-secondary mt-3 mb-0">
        ¿Ya tenés cuenta?{" "}
        <button type="button" className="btn btn-link p-0 align-baseline" onClick={onShowLogin}>
          Iniciá sesión
        </button>
      </p>
    </>
  );
}
