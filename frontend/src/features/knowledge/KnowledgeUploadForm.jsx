import { useState } from "react";

import { Button, FormField } from "../../ui/index.js";
import { createSource } from "./api.js";

const SOURCE_TYPES = [
  { value: "document", label: "Documento" },
  { value: "approved_answer", label: "Respuesta aprobada" },
];

const ROLES = [
  { value: "student", label: "Estudiante" },
  { value: "teacher", label: "Profesor" },
  { value: "admin", label: "Administrador" },
];

export default function KnowledgeUploadForm({ onCreated, onCancel }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [sourceType, setSourceType] = useState(SOURCE_TYPES[0].value);
  const [roles, setRoles] = useState(ROLES.map((role) => role.value));
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function toggleRole(value) {
    setRoles((previous) =>
      previous.includes(value) ? previous.filter((role) => role !== value) : [...previous, value]
    );
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("name", name.trim());
      formData.append("description", description.trim());
      formData.append("source_type", sourceType);
      roles.forEach((role) => formData.append("target_roles", role));
      const created = await createSource(formData);
      onCreated(created);
    } catch (requestError) {
      // La validación del servidor es la fuente de verdad: solo mostramos su mensaje.
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate data-testid="knowledge-upload-form">
      <FormField
        id="knowledge-name"
        label="Nombre"
        value={name}
        onChange={(event) => setName(event.target.value)}
        required
        data-testid="knowledge-upload-name"
      />

      <FormField
        id="knowledge-description"
        label="Propósito"
        value={description}
        onChange={(event) => setDescription(event.target.value)}
        hint="Para qué sirve esta fuente dentro del chatbot."
        data-testid="knowledge-upload-description"
      />

      <FormField id="knowledge-source-type" label="Tipo">
        <select
          id="knowledge-source-type"
          className="form-select"
          value={sourceType}
          onChange={(event) => setSourceType(event.target.value)}
          data-testid="knowledge-upload-type"
        >
          {SOURCE_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </FormField>

      <fieldset className="mb-3">
        <legend className="form-label fw-semibold p-0 mb-2">Roles destino</legend>
        <div className="d-flex flex-wrap gap-3" data-testid="knowledge-upload-roles">
          {ROLES.map((role) => (
            <div className="form-check" key={role.value}>
              <input
                className="form-check-input"
                type="checkbox"
                id={`knowledge-role-${role.value}`}
                checked={roles.includes(role.value)}
                onChange={() => toggleRole(role.value)}
                data-testid={`knowledge-upload-role-${role.value}`}
              />
              <label className="form-check-label" htmlFor={`knowledge-role-${role.value}`}>
                {role.label}
              </label>
            </div>
          ))}
        </div>
        <div className="form-text">
          Si no seleccionás ningún rol, la fuente aplica a todos los roles.
        </div>
      </fieldset>

      <FormField
        id="knowledge-file"
        label="Archivo"
        hint="Formatos admitidos: .md y .txt (hasta 1 MB)."
      >
        <input
          id="knowledge-file"
          type="file"
          className="form-control"
          accept=".md,.txt"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          data-testid="knowledge-upload-file"
        />
      </FormField>

      {error && (
        <div className="alert alert-danger py-2" role="alert" data-testid="knowledge-upload-error">
          {error}
        </div>
      )}

      <div className="d-flex justify-content-end gap-2">
        <Button variant="soft" onClick={onCancel} disabled={submitting}>
          Cancelar
        </Button>
        <Button
          type="submit"
          icon="upload"
          disabled={submitting}
          data-testid="knowledge-upload-submit"
        >
          {submitting ? "Procesando..." : "Cargar fuente"}
        </Button>
      </div>
    </form>
  );
}
