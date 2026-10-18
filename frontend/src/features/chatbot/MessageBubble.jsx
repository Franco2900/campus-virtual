export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`d-flex mb-3 ${isUser ? "justify-content-end" : "justify-content-start"}`}>
      <div
        className={`px-3 py-2 rounded-4 text-break ${isUser ? "bg-brand-soft" : "bg-body border"}`}
        style={{ maxWidth: "80%", whiteSpace: "pre-wrap" }}
        data-testid={isUser ? "chat-message-user" : "chat-message-assistant"}
      >
        {message.content}
      </div>
    </div>
  );
}
