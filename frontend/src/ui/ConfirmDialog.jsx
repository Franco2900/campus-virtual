import Button from "./Button.jsx";
import Modal from "./Modal.jsx";

const TONE_STYLE = {
  brand: { background: "var(--campus-brand-soft)", color: "var(--campus-brand)" },
  danger: { background: "var(--campus-danger-soft)", color: "var(--campus-danger)" },
};

export default function ConfirmDialog({
  open,
  title = "Confirmar acción",
  message,
  icon = "question-circle",
  tone = "brand",
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  confirmVariant = "brand",
  loading = false,
  testId,
  confirmTestId,
  onConfirm,
  onCancel,
}) {
  const style = TONE_STYLE[tone] ?? TONE_STYLE.brand;

  const footer = (
    <>
      <Button variant="soft" onClick={onCancel} disabled={loading}>
        {cancelLabel}
      </Button>
      <Button
        variant={confirmVariant}
        onClick={onConfirm}
        disabled={loading}
        data-testid={confirmTestId}
      >
        {loading ? "Procesando..." : confirmLabel}
      </Button>
    </>
  );

  return (
    <Modal open={open} title={title} footer={footer} testId={testId} onClose={onCancel}>
      <div className="d-flex align-items-start gap-3">
        <span className="auth-brand__icon" style={style} aria-hidden="true">
          <i className={`bi bi-${icon}`} />
        </span>
        <p className="mb-0">{message}</p>
      </div>
    </Modal>
  );
}
