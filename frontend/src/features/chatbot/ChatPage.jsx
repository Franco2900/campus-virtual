import { useEffect, useRef, useState } from "react";

import { Button, Card, EmptyState, PageHeader, Spinner, useToast } from "../../ui/index.js";
import { getHistory, sendMessage } from "./api.js";
import ChatComposer from "./ChatComposer.jsx";
import MessageList from "./MessageList.jsx";

export default function ChatPage() {
  const { notify } = useToast();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [text, setText] = useState("");
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState(null);
  const lastTextRef = useRef("");

  function showError(message, kind) {
    setError({ message, kind });
    notify({
      tone: "danger",
      title:
        kind === "send" ? "No se pudo completar la consulta" : "No se pudo cargar el historial",
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
    } else {
      handleSend(lastTextRef.current);
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
    </div>
  );
}
