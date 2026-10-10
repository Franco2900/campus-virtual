import { useState } from "react";

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
    <section>
      <h2>Iniciar sesión</h2>
      <form onSubmit={handleSubmit} noValidate>
        <label htmlFor="email">Correo electrónico</label>
        <input
          id="email"
          name="email"
          type="email"
          value={form.email}
          onChange={handleChange}
          required
        />

        <label htmlFor="password">Contraseña</label>
        <input
          id="password"
          name="password"
          type="password"
          value={form.password}
          onChange={handleChange}
          required
        />

        <button type="submit" disabled={submitting}>
          {submitting ? "Iniciando sesión..." : "Iniciar sesión"}
        </button>
      </form>

      {error && <p role="alert">{error}</p>}

      <button type="button" onClick={onShowRegister}>
        ¿No tenés cuenta? Registrate
      </button>
    </section>
  );
}