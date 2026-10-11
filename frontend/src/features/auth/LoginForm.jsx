import { useState } from "react";

import { Button, FormField } from "../../ui/index.js";
import { login } from "./api.js";

const INITIAL_FORM = {
  email: "",
  password: "",
};

export default function LoginForm({ onSuccess, onShowRegister }) {
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
      const user = await login(form);
      onSuccess(user);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  // Native validation is disabled so the backend stays the source of truth.
  return (
    <>
      <h2 className="h5 mb-3">Iniciar sesión</h2>
      <form onSubmit={handleSubmit} noValidate>
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
          autoComplete="current-password"
          value={form.password}
          onChange={handleChange}
          required
        />

        {error && (
          <div className="alert alert-danger py-2" role="alert">
            {error}
          </div>
        )}

        <Button type="submit" icon="box-arrow-in-right" className="w-100" disabled={submitting}>
          {submitting ? "Iniciando sesión..." : "Iniciar sesión"}
        </Button>
      </form>

      <p className="text-center text-secondary mt-3 mb-0">
        ¿No tenés cuenta?{" "}
        <button type="button" className="btn btn-link p-0 align-baseline" onClick={onShowRegister}>
          Registrate
        </button>
      </p>
    </>
  );
}
