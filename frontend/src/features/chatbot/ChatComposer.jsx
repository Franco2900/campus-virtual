import { Button, FormField } from "../../ui/index.js";

export default function ChatComposer({ value, onChange, onSend, disabled }) {
  const cannotSend = disabled || !value.trim();

  function submit() {
    if (!cannotSend) {
      onSend();
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <form
      className="border-top mt-3 pt-3"
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <FormField id="chat-input" label="Tu consulta">
        <textarea
          id="chat-input"
          className="form-control"
          rows={2}
          value={value}
          onChange={onChange}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Escribí tu consulta sobre la plataforma…"
          data-testid="chat-input"
        />
      </FormField>
      <div className="d-flex justify-content-end">
        <Button type="submit" icon="send" disabled={cannotSend} data-testid="chat-send">
          Enviar
        </Button>
      </div>
    </form>
  );
}
