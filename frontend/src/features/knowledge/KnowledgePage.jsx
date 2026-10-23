import { useEffect, useState } from "react";

import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  DataTable,
  Modal,
  PageHeader,
  RoleBadge,
  Spinner,
  StatusBadge,
  useToast,
} from "../../ui/index.js";
import KnowledgeUploadForm from "./KnowledgeUploadForm.jsx";
import { deleteSource, getSources } from "./api.js";

const TYPE_META = {
  document: { label: "Documento", tone: "neutral", icon: "file-text" },
  approved_answer: { label: "Respuesta aprobada", tone: "success", icon: "check2-circle" },
};

function SourceStatus({ source }) {
  if (source.status === "active") {
    return <StatusBadge active activeLabel="Activa" />;
  }
  if (source.status === "processing") {
    return <StatusBadge active={false} inactiveLabel="Procesando" />;
  }
  return (
    <div>
      <Badge tone="danger" icon="exclamation-triangle-fill">
        Error
      </Badge>
      {source.error_message && (
        <div className="small text-secondary mt-1" data-testid="knowledge-source-error-detail">
          {source.error_message}
        </div>
      )}
    </div>
  );
}

function renderType(source) {
  const meta = TYPE_META[source.source_type] ?? TYPE_META.document;
  return (
    <Badge tone={meta.tone} icon={meta.icon}>
      {meta.label}
    </Badge>
  );
}

function renderRoles(source) {
  const roles = source.target_roles ?? [];
  if (roles.length === 0) {
    return <Badge tone="neutral">Todos</Badge>;
  }
  return (
    <div className="d-flex flex-wrap gap-1">
      {roles.map((role) => (
        <RoleBadge key={role} role={role} />
      ))}
    </div>
  );
}

export default function KnowledgePage() {
  const { notify } = useToast();
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [confirming, setConfirming] = useState(null);
  const [deleting, setDeleting] = useState(false);

  async function loadSources() {
    setLoading(true);
    setError("");
    try {
      const data = await getSources();
      setSources(data?.sources ?? []);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSources();
  }, []);

  function handleCreated(created) {
    setUploadOpen(false);
    loadSources();
    notify({
      tone: "success",
      title: "Fuente cargada",
      message: `«${created?.source?.name ?? "La fuente"}» ya está disponible para el chatbot.`,
    });
  }

  async function confirmDelete() {
    const source = confirming;
    if (!source) {
      return;
    }
    setDeleting(true);
    try {
      await deleteSource(source.id);
      notify({
        tone: "success",
        title: "Fuente eliminada",
        message: `«${source.name}» dejó de estar disponible para el chatbot.`,
      });
      loadSources();
    } catch (requestError) {
      notify({
        tone: "danger",
        title: "No se pudo eliminar la fuente",
        message: requestError.message,
      });
    } finally {
      setDeleting(false);
      setConfirming(null);
    }
  }

  const columns = [
    {
      key: "name",
      header: "Nombre",
      render: (source) => <span className="fw-semibold">{source.name}</span>,
    },
    {
      key: "description",
      header: "Propósito",
      render: (source) =>
        source.description ? source.description : <span className="text-secondary">—</span>,
    },
    { key: "source_type", header: "Tipo", render: renderType },
    { key: "target_roles", header: "Roles", render: renderRoles },
    { key: "status", header: "Estado", render: (source) => <SourceStatus source={source} /> },
    {
      key: "actions",
      header: "",
      className: "text-end",
      render: (source) => (
        <Button
          variant="soft"
          className="btn-sm"
          icon="trash"
          onClick={() => setConfirming(source)}
          data-testid={`knowledge-delete-${source.id}`}
        >
          Eliminar
        </Button>
      ),
    },
  ];

  return (
    <div data-testid="knowledge-page">
      <PageHeader
        title="Fuentes de conocimiento"
        subtitle="Documentos y respuestas aprobadas que consulta el asistente"
        icon="bi-bookmark-data-fill"
        actions={
          <Button
            icon="plus-lg"
            onClick={() => setUploadOpen(true)}
            data-testid="knowledge-upload-open"
          >
            Cargar fuente
          </Button>
        }
      />

      {error && (
        <div
          className="alert alert-danger d-flex align-items-center gap-2"
          role="alert"
          data-testid="knowledge-error"
        >
          <i className="bi bi-exclamation-triangle-fill" aria-hidden="true" />
          {error}
        </div>
      )}

      <Card className="p-0 overflow-hidden">
        {loading ? (
          <div className="d-flex justify-content-center py-5">
            <Spinner label="Cargando fuentes..." />
          </div>
        ) : (
          <DataTable
            columns={columns}
            rows={sources}
            rowTestId={() => "knowledge-source-row"}
            empty="Todavía no hay fuentes de conocimiento."
            emptyIcon="bi-bookmark-data"
          />
        )}
      </Card>

      <Modal open={uploadOpen} title="Cargar fuente" onClose={() => setUploadOpen(false)}>
        {uploadOpen && (
          <KnowledgeUploadForm
            onCreated={handleCreated}
            onCancel={() => setUploadOpen(false)}
            onFailed={loadSources}
          />
        )}
      </Modal>

      <ConfirmDialog
        open={Boolean(confirming)}
        title="Eliminar fuente"
        tone="danger"
        icon="trash"
        confirmVariant="danger"
        confirmLabel="Eliminar"
        loading={deleting}
        testId="knowledge-delete-confirm"
        confirmTestId="knowledge-delete-confirm-accept"
        message={
          confirming
            ? `¿Eliminás «${confirming.name}»? La fuente dejará de estar disponible para el chatbot y no se puede deshacer.`
            : ""
        }
        onConfirm={confirmDelete}
        onCancel={() => setConfirming(null)}
      />
    </div>
  );
}
