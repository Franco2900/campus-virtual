import { useEffect, useRef, useState } from "react";

import {
  Button,
  Card,
  ConfirmDialog,
  EmptyState,
  PageHeader,
  Spinner,
  useToast,
} from "../../ui/index.js";
import { deleteHistory, getHistory, sendMessage } from "./api.js";
import ChatComposer from "./ChatComposer.jsx";
import MessageList from "./MessageList.jsx";

const ERROR_TITLES = {
  load: "No se pudo cargar el historial",
  send: "No se pudo completar la consulta",
  clear: "No se pudo eliminar el historial",
};

export default function ChatPage() {
  const { notify } = useToast();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [text, setText] = useState("");
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [clearing, setClearing] = useState(false);
  const lastTextRef = useRef("");

  function showError(message, kind) {
    setError({ message, kind });
    notify({
      tone: "danger",
      title: ERROR_TITLES[kind] ?? ERROR_TITLES.load,
      message,
    });
  }

  async function loadHistory() {
    setLoading(true);
    setError(null);
    try {
      const data = await getHistory();
      setMessages(Array.isArray(data?.messages) ? data.messages : []);
    } catch (requestError) {
      showError(requestError.message, "load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  async function handleSend(override) {
    const content = typeof override === "string" ? override.trim() : text.trim();
    if (!content || thinking) {
      return;
    }

    setError(null);
    setText("");
    setThinking(true);
    lastTextRef.current = content;

    const pendingId = `pending-${Date.now()}`;
    setMessages((current) => [...current, { id: pendingId, role: "user", content }]);

    try {
      const data = await sendMessage(content);
      setMessages((current) => [
        ...current.filter((message) => message.id !== pendingId),
        data.user_message,
        data.assistant_message,
      ]);
    } catch (requestError) {
      setMessages((current) => current.filter((message) => message.id !== pendingId));
      showError(requestError.message, "send");
    } finally {
      setThinking(false);
    }
  }

  function handleRetry() {
    if (!error) {
      return;
    }
    if (error.kind === "load") {
      loadHistory();
    } else if (error.kind === "clear") {
      setConfirmOpen(true);
    } else {
      handleSend(lastTextRef.current);
    }
  }

  async function handleClearHistory() {
    setClearing(true);
    try {
      await deleteHistory();
      setMessages([]);
      setError(null);
      notify({
        tone: "success",
        title: "Historial eliminado",
        message: "Se eliminó tu historial de conversaciones con el asistente.",
      });
    } catch (requestError) {
      showError(requestError.message, "clear");
    } finally {
      setClearing(false);
      setConfirmOpen(false);
    }
  }

  const showEmpty = !loading && messages.length === 0 && !thinking && error?.kind !== "load";

  return (
    <div data-testid="chat-page">
      <PageHeader
        title="Asistente"
        subtitle="Consultá sobre el funcionamiento del Campus Virtual y tus datos"
        icon="bi-chat-dots-fill"
      />

      <div className="d-flex justify-content-end mb-3">
        <Button
          variant="soft"
          icon="trash"
          onClick={() => setConfirmOpen(true)}
          disabled={loading || thinking || clearing}
          data-testid="chat-clear-history"
        >
          Eliminar historial
        </Button>
      </div>

      {error && (
        <div
          className="alert alert-danger d-flex align-items-center justify-content-between gap-3 flex-wrap"
          role="alert"
          data-testid="chat-error"
        >
          <span className="d-inline-flex align-items-center gap-2">
            <i className="bi bi-exclamation-triangle-fill" aria-hidden="true" />
            {error.message}
          </span>
          <Button icon="arrow-clockwise" onClick={handleRetry}>
            Reintentar
          </Button>
        </div>
      )}

      <Card className="p-3">
        {loading ? (
          <div className="d-flex justify-content-center py-5">
            <Spinner label="Cargando conversación..." />
          </div>
        ) : (
          <>
            {showEmpty ? (
              <div data-testid="chat-empty">
                <EmptyState icon="bi-chat-dots" title="Todavía no hay mensajes">
                  Hacé tu primera consulta sobre el funcionamiento de la plataforma y el asistente
                  te va a ayudar.
                </EmptyState>
              </div>
            ) : (
              <MessageList messages={messages} thinking={thinking} />
            )}
            <ChatComposer
              value={text}
              onChange={(event) => setText(event.target.value)}
              onSend={() => handleSend()}
              disabled={thinking}
            />
          </>
        )}
      </Card>

      <ConfirmDialog
        open={confirmOpen}
        title="Eliminar historial"
        tone="danger"
        icon="trash"
        confirmVariant="danger"
        confirmLabel="Eliminar historial"
        loading={clearing}
        testId="chat-clear-confirm"
        confirmTestId="chat-clear-confirm-accept"
        message="Se eliminarán todas tus conversaciones con el asistente. Esta acción no se puede recuperar desde la aplicación."
        onConfirm={handleClearHistory}
        onCancel={() => setConfirmOpen(false)}
      />
    </div>
  );
}
