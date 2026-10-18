import { useEffect, useRef } from "react";

import { Spinner } from "../../ui/index.js";
import MessageBubble from "./MessageBubble.jsx";

export default function MessageList({ messages, thinking }) {
  const listRef = useRef(null);

  useEffect(() => {
    const list = listRef.current;
    if (list) {
      list.scrollTop = list.scrollHeight;
    }
  }, [messages, thinking]);

  return (
    <div
      ref={listRef}
      className="overflow-y-auto pe-1"
      style={{ maxHeight: "60vh" }}
      aria-live="polite"
      data-testid="chat-message-list"
    >
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {thinking && (
        <div className="d-flex justify-content-start mb-3">
          <div className="bg-body border rounded-4 px-3 py-2" data-testid="chat-thinking">
            <Spinner label="Pensando…" />
          </div>
        </div>
      )}
    </div>
  );
}
